from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
import os
import re
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz import fuzz
from utils.db_manager import DatabaseManager
from utils.sms_sender import SMSSender
from train import FaceTrainer
from detect import FaceDetector
from dotenv import load_dotenv

# Download NLTK stopwords
try:
    nltk.download('stopwords', quiet=True)
except:
    print("Warning: Could not download NLTK stopwords. Text matching may be less accurate.")

load_dotenv()

app = Flask(__name__)
CORS(app)

def preprocess_text(text):
    """Preprocess text for mole matching"""
    if not text:
        return ""
    text = text.lower()  # Convert to lowercase
    text = re.sub(r'[^a-z0-9\s]', '', text)  # Remove special characters
    try:
        words = text.split()  # Tokenization
        stop_words = set(stopwords.words('english'))
        words = [word for word in words if word not in stop_words]  # Remove stopwords
        return ' '.join(words)
    except:
        # Fallback if NLTK is not available
        return text

def fuzzy_match_score(user_input, stored_texts):
    """Compute fuzzy matching score"""
    if not stored_texts:
        return -1, 0
    scores = [fuzz.token_set_ratio(user_input, text) for text in stored_texts]
    best_match_idx = scores.index(max(scores))  # Get index of highest score
    return best_match_idx, scores[best_match_idx]

def tfidf_cosine_similarity(user_input, stored_texts):
    """Compute TF-IDF + Cosine Similarity"""
    if not stored_texts:
        return -1, 0
    vectorizer = TfidfVectorizer()
    all_texts = [user_input] + stored_texts
    try:
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        cosine_sim = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1:])  # Compare user input to stored texts
        best_match_idx = cosine_sim.argmax()  # Get index of highest similarity
        return best_match_idx, cosine_sim[0][best_match_idx] * 100  # Convert to percentage
    except:
        # Fallback if vectorizer fails
        return -1, 0

def find_best_mole_match(user_input, mole_data):
    """Find best match for mole description"""
    if not user_input or not mole_data:
        return None, 0
    
    stored_texts = [item['description'] for item in mole_data]
    user_input_clean = preprocess_text(user_input)
    stored_texts_clean = [preprocess_text(text) for text in stored_texts]
    
    # Step 1: Fuzzy Matching
    best_fuzzy_idx, fuzzy_score = fuzzy_match_score(user_input_clean, stored_texts_clean)
    
    if fuzzy_score >= 90:
        return mole_data[best_fuzzy_idx], fuzzy_score
    
    # Step 2: TF-IDF + Cosine Similarity (if fuzzy match is inconclusive)
    best_tfidf_idx, tfidf_score = tfidf_cosine_similarity(user_input_clean, stored_texts_clean)
    
    if best_tfidf_idx >= 0 and tfidf_score >= 80:
        return mole_data[best_tfidf_idx], tfidf_score
    
    return None, 0

@app.route('/api/report-missing', methods=['POST'])
def report_missing():
    try:
        data = request.form
        files = request.files.getlist('photos')
        
        if not files:
            return jsonify({'error': 'No files uploaded'}), 400

        db = DatabaseManager()
        case_id = str(uuid.uuid4())
        
        # Get parent phone number and distinguishing features
        parent_phone = data.get('parentPhone')
        distinguishing_features = data.get('distinguishingFeatures')
        
        # Insert child, photos, and mole data
        db.insert_missing_child(
            data['childName'], 
            case_id, 
            files,
            parent_phone,
            distinguishing_features
        )
        
        # Retrieve photos for training
        training_dir = db.retrieve_child_photos()
        
        # Train model with updated dataset
        if training_dir:
            trainer = FaceTrainer()
            trainer.train_from_directory(training_dir)
        
        db.close()

        return jsonify({'message': 'Report submitted successfully', 'case_id': case_id}), 200

    except Exception as e:
        print(f"Error in report_missing: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/report-found', methods=['POST'])
def report_found():
    try:
        data = request.form
        
        # Check if foundPhoto exists in the request files
        if 'foundPhoto' not in request.files:
            return jsonify({'error': 'No file part'}), 400
            
        file = request.files['foundPhoto']
        
        # Check if file is empty
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Save uploaded file temporarily
        temp_path = f"temp_{uuid.uuid4()}.jpg"
        file.save(temp_path)

        # Initialize detector and process image
        detector = FaceDetector()
        results = detector.detect_face(temp_path)

        # Create a single database manager instance for all operations
        db = DatabaseManager()
        
        # Get mole description from the details field
        details = data.get('details', '')
        reported_mole_description = None
        
        # Try to extract mole-related information from details
        if details and ('mole' in details.lower() or 'mark' in details.lower()):
            reported_mole_description = details
        
        # Perform mole matching if applicable
        mole_match_found = False
        matched_child_name = None
        
        if reported_mole_description:
            all_mole_data = db.get_all_mole_data()
            if all_mole_data:
                best_match, match_score = find_best_mole_match(reported_mole_description, all_mole_data)
                if best_match and match_score >= 80:  # Threshold for considering a match
                    mole_match_found = True
                    matched_child_name = best_match['child_name']
                    print(f"Mole match found for child: {matched_child_name} with score: {match_score}")

        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)

        # Get reporter details
        reporter_name = data.get('reporterName', 'Anonymous')
        reporter_phone = data.get('reporterPhone', 'Unknown')
        location = data.get('location', 'Unknown location')
        
        # Store the reported information
        if data.get('location') and data.get('reporterName') and data.get('reporterPhone'):
            db.store_reported_child(
                data.get('childName') or matched_child_name,
                location,
                reporter_name,
                reporter_phone,
                details
            )

        # If mole match was found but no face match was found
        if mole_match_found and (not results or len(results) == 0):
            # Get case details for the matched child
            case_details = db.get_child_details(matched_child_name)
            
            # Get location information - make sure we fetch the most recent sighting
            last_seen_location = None
            locations = db.get_last_seen_locations(matched_child_name)
            if locations and len(locations) > 0:
                last_seen_location = locations[0]['location']
            
            # If still no location, use a default text
            if not last_seen_location or last_seen_location.strip() == "":
                last_seen_location = "Unknown location"
            
            # Get parent phone and send SMS notification if available
            parent_phone = db.get_parent_phone(matched_child_name)
            sms_sent = False
            
            if parent_phone:
                # Send SMS notification
                sms_sender = SMSSender()
                sms_sent = sms_sender.send_child_found_notification(
                    parent_phone,
                    matched_child_name,
                    location,
                    reporter_name,
                    reporter_phone
                )
                print(f"SMS notification sent: {sms_sent}")
            
            db.close()
            
            return jsonify({
                'match_found': True,
                'match_method': 'mole_description',
                'child_name': matched_child_name,
                'last_seen_location': last_seen_location,
                'notification_sent': sms_sent
            }), 200

        # Process face detection results if available
        if not results:
            db.close()
            return jsonify({
                'message': 'No match found',
                'match_found': False
            }), 200

        # Get the best match from face detection
        matched_name, confidence = results[0]
        
        # Get case details
        case_details = db.get_child_details(matched_name)
        
        # Get location information
        last_seen_location = None
        locations = db.get_last_seen_locations(matched_name)
        if locations and len(locations) > 0:
            last_seen_location = locations[0]['location']  # Get the most recent location
        
        # If still no location, use a default text
        if not last_seen_location or last_seen_location.strip() == "":
            last_seen_location = "Unknown location"
            
        # Get parent phone and send SMS notification if available
        parent_phone = db.get_parent_phone(matched_name)
        sms_sent = False

        if parent_phone:
            # Send SMS notification
            sms_sender = SMSSender()
            sms_sent = sms_sender.send_child_found_notification(
                parent_phone,
                matched_name,
                location,
                reporter_name,
                reporter_phone
            )
            print(f"SMS notification sent: {sms_sent}")
        
        # Check if there's a mole match for the same child (double confirmation)
        mole_description = db.get_mole_data_for_child(matched_name)
        mole_match = False
        if mole_description and reported_mole_description:
            _, match_score = find_best_mole_match(reported_mole_description, [{'description': mole_description}])
            mole_match = match_score >= 80
        
        # Close database connection only after all operations are complete
        db.close()

        return jsonify({
            'match_found': True,
            'match_method': 'facial_recognition',
            'child_name': matched_name,
            'confidence': float(confidence),
            'last_seen_location': last_seen_location,
            'notification_sent': sms_sent,
            'mole_match_confirmation': mole_match
        }), 200

    except Exception as e:
        print(f"Error in report_found: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

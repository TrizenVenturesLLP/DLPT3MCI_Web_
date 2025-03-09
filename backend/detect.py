
import cv2
import numpy as np
import dlib
from architecture import InceptionResNetV2
from scipy.spatial.distance import cosine
import pickle

class FaceDetector:
    def __init__(self):
        self.recognition_t = 0.4
        self.required_size = (160, 160)
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor("assets/model/shape_predictor_68_face_landmarks.dat")
        self.face_encoder = InceptionResNetV2()
        self.face_encoder.load_weights("assets/model/facenet_keras_weights.h5")

    def get_aligned_face(self, img, rect):
        """Get aligned face using dlib's face chip"""
        landmarks = self.predictor(img, rect)
        aligned_face = dlib.get_face_chip(img, landmarks, size=160)
        return aligned_face

    def get_encode(self, face):
        """Get face encoding using the InceptionResNetV2 model"""
        face = cv2.resize(face, self.required_size)
        face = face.astype('float32') / 255.0
        encode = self.face_encoder.predict(np.expand_dims(face, axis=0))[0]
        return encode

    def load_encodings(self):
        """Load saved face encodings from pickle file"""
        try:
            with open("assets/encodings/encodings.pkl", "rb") as f:
                return pickle.load(f)
        except FileNotFoundError:
            print("No encodings file found")
            return None
        except Exception as e:
            print(f"Error loading encodings: {e}")
            return None

    def detect_face(self, image_path):
        """Detect and recognize faces in the image"""
        try:
            img = cv2.imread(image_path)
            if img is None:
                print("Error loading image")
                return None

            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            faces = self.detector(img_rgb)
            
            if not faces:
                print("No faces detected in the image")
                return None

            # Get encodings for the uploaded image
            aligned_face = self.get_aligned_face(img_rgb, faces[0])
            encode = self.get_encode(aligned_face)
            
            # Load existing encodings
            encoding_dict = self.load_encodings()
            if not encoding_dict:
                return None

            # Find matches
            matches = []
            for db_name, db_encode in encoding_dict.items():
                dist = cosine(db_encode, encode)
                if dist < self.recognition_t:
                    confidence = 1 - dist  # Convert distance to confidence score
                    matches.append((db_name, confidence))

            # Sort by confidence
            matches.sort(key=lambda x: x[1], reverse=True)
            return matches

        except Exception as e:
            print(f"Error in detect_face: {e}")
            return None

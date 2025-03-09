
import cv2
import numpy as np
import dlib
import os
import pickle
from architecture import InceptionResNetV2
from tensorflow.keras.models import load_model

class FaceTrainer:
    def __init__(self):
        self.required_size = (160, 160)
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor("assets/model/shape_predictor_68_face_landmarks.dat")
        self.face_encoder = InceptionResNetV2()
        self.face_encoder.load_weights("assets/model/facenet_keras_weights.h5")

    def get_aligned_face(self, img, rect):
        landmarks = self.predictor(img, rect)
        aligned_face = dlib.get_face_chip(img, landmarks, size=160)
        return aligned_face

    def get_encode(self, face):
        face = cv2.resize(face, self.required_size)
        face = face.astype('float32') / 255.0
        encode = self.face_encoder.predict(np.expand_dims(face, axis=0))[0]
        return encode

    def train_from_directory(self, training_dir):
        encoding_dict = {}
        
        for person_name in os.listdir(training_dir):
            person_dir = os.path.join(training_dir, person_name)
            if not os.path.isdir(person_dir):
                continue

            encodings = []
            for img_name in os.listdir(person_dir):
                img_path = os.path.join(person_dir, img_name)
                img = cv2.imread(img_path)
                if img is None:
                    continue

                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                faces = self.detector(img_rgb)
                
                if len(faces) > 0:
                    aligned_face = self.get_aligned_face(img_rgb, faces[0])
                    encode = self.get_encode(aligned_face)
                    encodings.append(encode)

            if encodings:
                encoding_dict[person_name] = np.mean(encodings, axis=0)

        # Save encodings
        with open("assets/encodings/encodings.pkl", "wb") as f:
            pickle.dump(encoding_dict, f)

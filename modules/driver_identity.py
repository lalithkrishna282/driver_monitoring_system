import os
import cv2
import numpy as np
import face_recognition


class DriverIdentity:

    def __init__(self, database_path="drivers"):
        self.database_path = database_path
        self.known_encodings = []
        self.known_names = []

        if not os.path.exists(database_path):
            os.makedirs(database_path)

        self.load_database()

    def load_database(self):
        for file in os.listdir(self.database_path):

            path = os.path.join(self.database_path, file)

            image = face_recognition.load_image_file(path)

            encodings = face_recognition.face_encodings(image)

            if len(encodings) > 0:
                self.known_encodings.append(encodings[0])
                name = os.path.splitext(file)[0]
                self.known_names.append(name)

    def recognize(self, frame):

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        boxes = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, boxes)

        name = "Unknown"

        for encoding in encodings:

            matches = face_recognition.compare_faces(self.known_encodings, encoding)

            if True in matches:
                index = matches.index(True)
                name = self.known_names[index]

        return name
import face_recognition
import os
import cv2

class DriverRecognition:

    def __init__(self, drivers_folder="drivers"):
        self.drivers_folder = drivers_folder
        self.known_encodings = []
        self.known_names = []

        self.load_drivers()

    def load_drivers(self):
        self.known_encodings = []
        self.known_names = []

        if not os.path.isdir(self.drivers_folder):
            return

        for file in os.listdir(self.drivers_folder):

            if file.endswith(".jpg") or file.endswith(".png"):

                path = os.path.join(self.drivers_folder, file)

                image = face_recognition.load_image_file(path)

                encodings = face_recognition.face_encodings(image)

                if len(encodings) > 0:
                    self.known_encodings.append(encodings[0])

                    name = os.path.splitext(file)[0]
                    self.known_names.append(name)

    def recognize(self, frame):

        # convert BGR to RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # detect faces
        faces = face_recognition.face_locations(rgb)

        if len(faces) == 0:
            return "Unknown"

        encodings = face_recognition.face_encodings(rgb, faces)

        name = "Unknown"

        for encoding in encodings:

            matches = face_recognition.compare_faces(self.known_encodings, encoding)

            if True in matches:

                index = matches.index(True)
                name = self.known_names[index]

                break

        return name

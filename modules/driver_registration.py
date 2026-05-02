import cv2
import os

class DriverRegistration:

    def __init__(self, save_path="drivers"):
        self.save_path = save_path

        if not os.path.exists(save_path):
            os.makedirs(save_path)

    def register(self, frame, driver_name):

        file_path = os.path.join(self.save_path, f"{driver_name}.jpg")

        cv2.imwrite(file_path, frame)

        print(f"Driver {driver_name} registered successfully.")
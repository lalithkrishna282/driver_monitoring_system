class FocusZone:

    def detect(self, yaw, pitch):

        if abs(yaw) < 10 and pitch < 15:
            return "ROAD"

        elif yaw <= -15:
            return "LEFT MIRROR"

        elif yaw >= 15:
            return "RIGHT MIRROR"

        elif pitch > 20:
            return "DASHBOARD"

        else:
            return "DISTRACTED"
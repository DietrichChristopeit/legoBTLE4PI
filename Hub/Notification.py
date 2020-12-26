from bluepy import btle

class Notification(btle.DefaultDelegate):
    def __init__(self):
        btle.DefaultDelegate.__init__(self)

    def handleNotification(self, cHandle, data):  # Eigentliche Callbackfunktion
        print('Notification erhalten : {}'.format(data.hex()))

    def schreibeNotification(self, data):
        pass

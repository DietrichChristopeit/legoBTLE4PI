class Message(dict):
    DEVICE_TYPE = {
        b'\x01': b'INTERNAL_MOTOR',
        b'\x02': b'SYSTEM_TRAIN_MOTOR',
        b'\x05': b'BUTTON',
        b'\x08': b'LED',
        b'\x14': b'VOLTAGE',
        b'\x15': b'CURRENT',
        b'\x16': b'PIEZO_TONE',
        b'\x17': b'RGB_LIGHT',
        b'\x22': b'EXTERNAL_TILT_SENSOR',
        b'\x23': b'MOTION_SENSOR',
        b'\x25': b'VISION_SENSOR',
        b'\x2e': b'EXTERNAL_MOTOR',
        b'\x2f': b'EXTERNAL_MOTOR_WITH_TACHO',
        b'\x27': b'INTERNAL_MOTOR_WITH_TACHO',
        b'\x28': b'INTERNAL_TILT'
        }
    
    def __init__(self, payload: bytearray = b''):
        super().__init__()
        self._payload: bytearray = payload
        return
    
    def __missing__(self, key) -> bytes:
        return b''
    
    def encode(self):
        message: Message = Message()
        message['d_type'] = Message.DEVICE_TYPE.get(self._payload[2], b'')
        
        return message


from collections import namedtuple


class BMessage:
    DEVICE_TYPE: dict = {
        '01': 'INTERNAL_MOTOR',
        '02': 'SYSTEM_TRAIN_MOTOR',
        '05': 'BUTTON',
        '08': 'LED',
        '14': 'VOLTAGE',
        '15': 'CURRENT',
        '16': 'PIEZO_TONE',
        '17': 'RGB_LIGHT',
        '22': 'EXTERNAL_TILT_SENSOR',
        '23': 'MOTION_SENSOR',
        '25': 'VISION_SENSOR',
        '2e': 'EXTERNAL_MOTOR',
        '2f': 'EXTERNAL_MOTOR_WITH_TACHO',
        '27': 'INTERNAL_MOTOR_WITH_TACHO',
        '28': 'INTERNAL_TILT'
        }
    
    m = {'length': bytes,
         'hubid': bytes,
         'mtype': namedtuple('type', DEVICE_TYPE)
         }
    

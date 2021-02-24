from LegoBTLE.LegoWP.messages.upstream import UpStreamMessageBuilder
from LegoBTLE.LegoWP.types import M_TYPE

if __name__ == '__main__':
    data:bytearray = bytearray(b'\x0f\x00\x04<\x01\x14\x00\x00\x00\x00\x10\x00\x00\x00\x10')
    # e = UpStreamMessageBuilder(data=data)
    print(data[2])
    print(data[2].to_bytes(1, 'little', signed=False) == M_TYPE.UPS_HUB_ATTACHED_IO)
    # mret = e.build()
    # print(f"{mret}")

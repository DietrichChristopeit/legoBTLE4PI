#from bluepy import btle

#dev = btle.Peripheral('90:84:2B:5E:CF:1F')
from time import sleep

from Controller.HubType.HubType import HubNo2

if __name__ == '__main__':
    jeep = HubNo2('90:84:2B:5E:CF:1F')

    print('Controller name:', jeep.leseControllerName)

    sleep(6)



    #gefundeneGeraete = LegoJeep.sucheJeep()

    #print(f'gefundene Geräte: {gefundeneGeraete}')

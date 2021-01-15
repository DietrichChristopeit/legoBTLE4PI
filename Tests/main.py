from time import sleep

from Controller.Hub_new import Hub
from Geraet.Motor import Motor
from Konstanten.Anschluss import Anschluss

if __name__ == '__main__':
    def init():
        # BEGINN Initialisierung
        adresse: str = '90:84:2B:5E:CF:1F'
        terminateEvent: threading.Event = threading.Event()

        mainThread = threading.current_thread()
        mainThread.setName("MAIN")

        hubExecQ: queue.Queue = queue.Queue(maxsize=100)
        hubExecQEmptyEvent: threading.Event = threading.Event()
        # ENDE Initialisierung
        return adresse, hubExecQ, terminateEvent, hubExecQEmptyEvent, mainThread


    hub: Hub = Hub("Lego Technic Hub", adresse=init[0], execQ=init()[1], terminateOn=init()[2],
                                     execQEmpty=init()[3])

    motorA: Motor = Motor("Motor A", anschluss=Anschluss.A, execQ=init()[1], terminateOn=init()[2])
    motorB: Motor = Motor("Motor B", anschluss=Anschluss.B, execQ=init()[1], terminateOn=init()[2])
    motorC: Motor = Motor("Motor C", anschluss=Anschluss.C, execQ=init()[1], terminateOn=init()[2])

    # Fahrtprogramm
    print("[{}]-[MSG]: Starting Command Execution Subsystem...".format(init()[3].name))
    hub.start()
    motorA.start()
    motorC.start()
    motorB.start()
    print("[{}]-[MSG]: Registering Motor Devices...".format(init()[3].name))
    hub.register(motorB)
    hub.register(motorC)
    hub.register(motorA)
    print("[{}]-[MSG]: waiting 5...".format(init()[3].name))
    sleep(5)
    print("Sending command A to Motor A")
    motorA.commandA(motorA.name)
    print("Sending command B to Motor A")
    motorA.commandB(motorA.name)
    print("Sending command A to Motor B")
    motorB.commandA(motorB.name)
    print("Sending command C to Motor B")
    motorB.commandC(motorB.name)
    print("Sending command B to Motor A")
    motorA.commandB(motorA.name)
    print("[{}]-[SIG]: WAITING FOR ALL COMMANDS TO END...".format(init()[3].name))
    init()[2].wait()
    print("[{}]-[SIG]: RESUME COMMAND EXECUTION RECEIVED...".format(init()[3].name))
    print("Sending command C to Motor A")
    motorA.commandC(motorA.name)
    print("Sending command B to Motor B")
    motorB.commandB(motorB.name)
    print("Sending command B to Motor A")
    motorA.commandB(motorA.name)
    print("Sending command B to Motor A")
    motorA.commandB(motorA.name)

    print("[{}]-[MSG]: SHUTTING DOWN...".format(init()[3].name))
    sleep(2)
    init()[1].set()
    print("[{}]-[SIG]: SHUT DOWN SIGNAL SENT...".format(init()[3].name))
    motorC.join()
    motorB.join()
    motorA.join()
    print("[{}]-[MSG]: SHUT DOWN COMPLETE: Command Execution Subsystem ...".format(init()[3].name))
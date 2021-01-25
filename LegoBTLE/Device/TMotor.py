#  MIT License
#
#  Copyright (c) 2021 Dietrich Christopeit
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
from abc import ABC, abstractmethod

from queue import Empty, Queue
from random import uniform
from threading import Thread, Event, Condition
from time import sleep

from colorama import Fore, Style, init

from LegoBTLE.Constants import SIUnit
from LegoBTLE.Constants.MotorConstant import MotorConstant
from LegoBTLE.Constants.Port import Port
from LegoBTLE.Device.Command import Command


class Motor(ABC):
    """Abstract base class for all Motor Types."""

    @property
    @abstractmethod
    def debug(self) -> bool:
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @name.setter
    @abstractmethod
    def name(self, name: str):
        raise NotImplementedError

    @property
    @abstractmethod
    def Q_rsltrcv_RCV(self) -> Queue:
        raise NotImplementedError

    @property
    @abstractmethod
    def E_rsltrcv_STARTED(self) -> Event:
        raise NotImplementedError

    @property
    @abstractmethod
    def E_rsltrcv_STOPPED(self) -> Event:
        raise NotImplementedError

    @property
    @abstractmethod
    def Q_cmdsnd_WAITING(self) -> Queue:
        raise NotImplementedError

    @property
    @abstractmethod
    def E_cmdsnd_STARTED(self) -> Event:
        raise NotImplementedError

    @property
    @abstractmethod
    def E_cmdsnd_STOPPED(self) -> Event:
        raise NotImplementedError

    @property
    def Q_cmd_EXEC(self) -> Queue:
        raise NotImplementedError

    @property
    @abstractmethod
    def E_port_FREE(self) -> Event:
        raise NotImplementedError

    @property
    @abstractmethod
    def T_RSLTReceiver(self) -> Thread:
        raise NotImplementedError

    @property
    @abstractmethod
    def T_CMDSender(self) -> Thread:
        raise NotImplementedError

    @property
    @abstractmethod
    def T_Listener_STOP(self) -> Thread:
        raise NotImplementedError

    @property
    @abstractmethod
    def C_port_FREE(self) -> Condition:
        raise NotImplementedError

    @property
    @abstractmethod
    def E_TERMINATE(self) -> Event:
        raise NotImplementedError

    @property
    @abstractmethod
    def E_PROCESSES_TERMINATE(self) -> Event:
        raise NotImplementedError

    @property
    @abstractmethod
    def E_MOTOR_STARTED(self) -> Event:
        raise NotImplementedError

    @property
    @abstractmethod
    def E_MOTOR_TERMINATED(self) -> Event:
        raise NotImplementedError

    @property
    @abstractmethod
    def port(self) -> int:
        raise NotImplementedError

    @port.setter
    @abstractmethod
    def port(self, port: int):
        raise NotImplementedError

    @abstractmethod
    def setVirtualPort(self, port: int):
        raise NotImplementedError

    @property
    @abstractmethod
    def gearRatio(self) -> float:
        raise NotImplementedError

    @gearRatio.setter
    @abstractmethod
    def gearRatio(self, gearRatio: float):
        raise NotImplementedError

    @property
    @abstractmethod
    def previousAngle(self) -> float:
        raise NotImplementedError

    @previousAngle.setter
    @abstractmethod
    def previousAngle(self, value: float):
        raise NotImplementedError

    @property
    @abstractmethod
    def currentAngle(self) -> float:
        raise NotImplementedError

    @currentAngle.setter
    @abstractmethod
    def currentAngle(self, value: float):
        raise NotImplementedError

    @property
    @abstractmethod
    def upm(self) -> float:
        raise NotImplementedError

    @property
    @abstractmethod
    def lastError(self) -> int:
        raise NotImplementedError

    @lastError.setter
    @abstractmethod
    def lastError(self, error: int):
        raise NotImplementedError

    def CmdSND(self, name="CmdSND"):
        self.E_cmdsnd_STARTED.set()
        self.E_cmdsnd_STOPPED.clear()
        print("[{:02}]:[{}]-[SIG]: SENDER START COMPLETE...".format(self.port, name))

        while not self.E_PROCESSES_TERMINATE.is_set():
            if self.E_PROCESSES_TERMINATE.is_set():
                break

            if not self.Q_cmdsnd_WAITING.qsize() == 0:
                command: Command = self.Q_cmdsnd_WAITING.get(timeout=.4)
                if command.port == 0xff:  # discard, empty command
                    continue
            else:
                sleep(.1)
                continue

            with self.C_port_FREE:
                if self.debug:
                    print(Style.BRIGHT, Fore.YELLOW + "[{:02}]:[{}]-[SND]: WAITING TO SEND {} TO PORT [{:02}]".format(self.port,
                                                                                                                      name,
                                                                                                                      command.data.hex(),
                                                                                                                      command.port))
                    print(Style.RESET_ALL)
                self.C_port_FREE.wait_for(lambda: self.E_port_FREE.is_set() or self.E_PROCESSES_TERMINATE.is_set())
                if self.E_PROCESSES_TERMINATE.is_set():
                    print(
                        Style.BRIGHT + Fore.RED + "[{:02}]:[{}]-[MSG]: ABORTING COMMAND {} FOR PORT [{:02}]...".format(self.port,
                                                                                                                       name,
                                                                                                                       command.data.hex(),
                                                                                                                       command.port))
                    print(Style.RESET_ALL)
                    self.E_port_FREE.set()
                    self.C_port_FREE.notify_all()
                    break
                print(Style.BRIGHT + Fore.RED + "[{:02}]:[{}]-[SND]: LOCKING PORT [{:02}]".format(self.port, name, command.port))
                print(Style.RESET_ALL)
                self.E_port_FREE.clear()
                if self.debug:
                    print(Style.BRIGHT + Fore.BLUE +
                          "[{:02}]:[{}]-[SND]: SENDING COMMAND {} FOR PORT [{:02}]".format(self.port, name, command.data.hex(),
                                                                                           command.port))
                self.Q_cmd_EXEC.put(command)
                if self.debug:
                    print(Style.BRIGHT + Fore.BLUE + "[{:02}]:[{}]-[SND]: COMMAND SENT {} FOR PORT [{:02}]".format(self.port,
                                                                                                                   name,
                                                                                                                   command.data.hex(),
                                                                                                                   command.port))
                self.C_port_FREE.notify_all()
            # sleep(.001)  # to make sending and receiving (port freeing) more evenly distributed

        print(Style.BRIGHT + Fore.RED + "[{:02}]:[{}]-[MSG]: COMMENCE CMD SENDER SHUT DOWN...".format(self.port, name))
        with self.C_port_FREE:
            self.E_port_FREE.set()
            self.C_port_FREE.notify_all()
        self.E_cmdsnd_STARTED.clear()
        self.E_cmdsnd_STOPPED.set()
        return

    def RsltRCV(self, name="rsltRCV"):
        self.E_rsltrcv_STARTED.set()
        self.E_rsltrcv_STOPPED.clear()
        print("[{:02}]:[{}]-[SIG]: RECEIVER START COMPLETE...".format(self.port, name))

        while not self.E_PROCESSES_TERMINATE.is_set():
            if self.E_PROCESSES_TERMINATE.is_set():
                break
            result: Command
            try:
                result = self.Q_rsltrcv_RCV.get(timeout=.4)
            except Empty:
                continue
            else:
                sleep(.01)

            with self.C_port_FREE:
                if self.debug:
                    print(Fore.BLUE + "[{}]:[{:02}]:[{}]-[MSG]: RECEIVED DATA: {} FOR PORT [{:02}]...".format(self.name,
                                                                                                              result.port,
                                                                                                              name,
                                                                                                              result.data.hex(),
                                                                                                              result.port))
                    print(Style.RESET_ALL)

                if (result.data[2] == 0x82) and (result.data[4] == 0x0a):
                    if self.debug:
                        print(Style.BRIGHT + Fore.GREEN +
                              "[{}]:[{:02}]:[{}]-[MSG]: 0x0a FREEING PORT {:02}...".format(self.name, result.port, name,
                                                                                           result.port))
                        print(Style.RESET_ALL)
                    self.E_port_FREE.set()
                    sleep(uniform(0.001, 0.01))
                    self.C_port_FREE.notify_all()
                    continue

                if result.error:  # error
                    self.lastError = result.data.hex()
                    if self.debug:
                        print(Style.BRIGHT + Fore.GREEN +
                              "[{:02}]:[{}]-[MSG]: ERROR RESULT MESSAGE freeing port {:02}...".format(self.port, name,
                                                                                                      self.port))
                        print(Style.RESET_ALL)
                    self.E_port_FREE.set()
                    sleep(uniform(0.001, 0.01))
                    self.C_port_FREE.notify_all()
                    continue

                if result.data[2] == 0x04:
                    self.setVirtualPort(result.port)
                    if self.debug:
                        print(Style.BRIGHT + Fore.GREEN +
                              "[{:02}]:[{}]-[MSG]: ERROR RESULT MESSAGE freeing port {:02}...".format(self.port, name,
                                                                                                      self.port))
                        print(Style.RESET_ALL)
                    self.E_port_FREE.set()
                    sleep(uniform(0.001, 0.01))
                    self.C_port_FREE.notify_all()
                    continue

                if result.data[2] == 0x45:
                    self.previousAngle = self.currentAngle
                    self.currentAngle = int(''.join('{:02}'.format(m) for m in result.data[4:7][::-1]), 16) / self.gearRatio
                    sleep(uniform(0.001, 0.01))
                    self.C_port_FREE.notify_all()
                    continue
            sleep(uniform(0.001, 0.01))
        print("[{:02}]:[{}]-[SIG]: COMMENCE RECEIVER SHUT DOWN...".format(self.port, name))

        self.E_rsltrcv_STARTED.clear()
        self.E_rsltrcv_STOPPED.set()
        return

    def startMotor(self):
        self.E_MOTOR_STARTED.clear()
        self.E_MOTOR_TERMINATED.clear()
        self.E_PROCESSES_TERMINATE.clear()

        if self.debug:
            print("[{}]-[MSG]: COMMENCE START...".format(self.name))
            print("[{}]:[{}]-[MSG]: COMMENCE RECEIVER START...".format(self.name, self.T_RSLTReceiver.name))
        self.T_RSLTReceiver.start()
        self.E_rsltrcv_STARTED.wait()
        if self.debug:
            print("[{}]:[{}]-[MSG]: RESULT RECEIVER START COMPLETE...".format(self.name, self.T_RSLTReceiver.name))
            print("[{}]:[{}]-[MSG]: COMMENCE COMMAND SENDER START...".format(self.name, self.T_CMDSender.name))
        self.T_CMDSender.start()
        self.E_cmdsnd_STARTED.wait()
        if self.debug:
            print("[{}]-[MSG]: COMMAND SENDER {} START COMPLETE...".format(self.name, self.T_CMDSender.name))

        sleep(1)
        self.E_MOTOR_STARTED.set()
        self.T_Listener_STOP.start()
        return

    def stopMotor(self):
        self.E_TERMINATE.wait()
        self.E_PROCESSES_TERMINATE.set()

        if self.debug:
            print("[{}]-[SIG]: COMMENCE SHUT DOWN...".format(self.name))
            print("[{}]:[{}]-[SIG]: COMMENCE SHUT DOWN...".format(self.name, self.T_RSLTReceiver.name))
        self.E_rsltrcv_STOPPED.wait()
        self.T_RSLTReceiver.join()
        if self.debug:
            print("[{}]:[{}]-[SIG]: SHUT DOWN COMPLETE...".format(self.name, self.T_RSLTReceiver.name))
        if self.debug:
            print("[{}]:[{}]-[SIG]: COMMENCE SHUT DOWN...".format(self.name, self.T_CMDSender.name))
        self.E_cmdsnd_STOPPED.wait()
        self.T_CMDSender.join()
        if self.debug:
            print("[{}]:[{}]-[SIG]: SHUT DOWN COMPLETE...".format(self.name, self.T_CMDSender.name))
            print("[{}]-[SIG]: SHUT DOWN COMPLETE...".format(self.name))

        self.E_MOTOR_TERMINATED.set()
        return

    # Commands available
    def turnForT(self, milliseconds: int, direction: int = MotorConstant.FORWARD, power: int = 50,
                 finalAction: int = MotorConstant.BREAK, withFeedback=True):
        """This method can be used to calculate the data to turn a motor for a specific time period and send it to the
        command waiting multiprocessing.Queue of the Motor.

            :param milliseconds:
                The duration for which the motor type should turn.
            :param direction:
                Either the driving direction (MotorConstant.FORWARD or MotorConstant.BACKWARD) or the steering direction
                (MotorConstant.LEFT or MotorConstant.RIGHT).
            :param power:
                A value between 0 and 100 (%).
            :param finalAction:
                Determines how the motor should behave once the specified time has been reached,
                i.e.,
                    * MotorConstant.COAST = the motor does not stop immediately, but turns on its own until
                    coming to a standstill (through friction working against movement)

                    * MotorConstant.BREAK = the motor is stopped, but can be turned by external force

                    * MotorConstant.HOLD = Motor is held in the end position, even if external forces try to
                    rotate the engine
            :param withFeedback:
                TRUE: Feedback is required.
                FALSE: No feedback required.
            :returns:
                None
        """

        power = direction.value * power if isinstance(direction, MotorConstant) else direction * power
        finalAction = finalAction.value if isinstance(finalAction, MotorConstant) else finalAction

        try:
            assert self.port is not None

            port = self.port

            data: bytes = bytes.fromhex('0c0081{:02x}1109'.format(port) + milliseconds.to_bytes(2, byteorder='little',
                                                                                                signed=False).hex() \
                                        + \
                                        power.to_bytes(1, byteorder='little', signed=True).hex() + '64{:02x}03'.format(
                    finalAction))
        except AssertionError:
            print('[{}]-[ERR]: Motor has no port assigned... Exit...'.format(self))
            self.Q_cmdsnd_WAITING.put(Command())
        else:
            self.Q_cmdsnd_WAITING.put(Command(data=data, port=port, withFeedback=withFeedback))
        return

    def turnForDegrees(self, degrees: float, direction: int = MotorConstant.FORWARD, power: int = 50,
                       finalAction: int = MotorConstant.BREAK, withFeedback: bool = True):
        """This method is used to calculate the data to turn a motor for a specific value of degrees (°) and send
        this command to the command waiting multiprocessing.Queue of the Motor.

        :param degrees:
            The angle in ° by which the motor, i.e. its shaft, is to be rotated. An integer value, e.g. 10,
            12, 99 etc.
        :param direction:
            Either the driving direction (MotorConstant.FORWARD or MotorConstant.BACKWARD) or the steering direction (
            MotorConstant.LEFT or MotorConstant.RIGHT).
        :param power:
            A value between 0 an 100 (%)
        :param finalAction:
            Determines how the motor should behave once the specified time has been reached,
            i.e.,
                * MotorConstant.COAST = the motor does not stop immediately, but turns on its own until
                coming to a standstill (through friction working against movement)

                * MotorConstant.BREAK = the motor is stopped, but can be turned by external force

                * MotorConstant.HOLD = Motor is held in the end position, even if external forces try to
                rotate the engine
        :param withFeedback:
                TRUE: Feedback is required.
                FALSE: No feedback required.
        :returns:
                None
        """
        power = direction.value * power if isinstance(direction, MotorConstant) else direction * power
        finalAction = finalAction.value if isinstance(finalAction, MotorConstant) else finalAction

        degrees = round(degrees * self.gearRatio)

        try:
            assert self.port is not None

            port = self.port

            data: bytes = bytes.fromhex('0e0081{:02x}110b'.format(port) + degrees.to_bytes(4,
                                                                                           byteorder='little',
                                                                                           signed=False).hex() \
                                        + power.to_bytes(1, byteorder='little',
                                                         signed=True).hex() + '64{:02x}03'.format(finalAction))
        except AssertionError:
            print('[{}]-[ERR]: Motor has no port assigned... Exit...'.format(self))
            self.Q_cmdsnd_WAITING.put(Command())
        else:
            self.Q_cmdsnd_WAITING.put(Command(data=data, port=port, withFeedback=withFeedback))
        return

    def turnMotor(self, SI: SIUnit, unitValue: float = 0.0, direction: int = MotorConstant.FORWARD,
                  power: int = 50, finalAction: int = MotorConstant.BREAK,
                  withFeedback: bool = True):
        """This method turns the Motor depending on the SI-Unit specified.

        :param SI:
            SI unit based on which the motor is to be turned (e.g. SIUnit.ANGLE).
        :param unitValue:
            By which value in the SI unit the motor is to be rotated.
        :param direction:
            Either the driving direction (MotorConstant.FORWARD or MotorConstant.BACKWARD) or the steering direction
            (MotorConstant.LEFT or MotorConstant.RIGHT).
        :param power: 
            A value between 0 and 100 (%).
        :param finalAction:
            Determines how the motor should behave after the rotations have ended,
            i.e.
            * MotorConstant.COAST = the motor does not stop immediately, but turns on its own until the
            Standstill;
            * MotorConstant.BREAK = the motor is stopped, but can be turned by external force
            will;
            * MotorConstant.HOLD = Motor is held in the end position, even if external forces try to
            to turn the engine.
        :param withFeedback:
                TRUE: Feedback is required.
                FALSE: No feedback required.
        :returns: 
            None
        """
        if SI == SI.ANGLE:
            self.turnForDegrees(unitValue, direction=direction, power=power, finalAction=finalAction,
                                withFeedback=withFeedback)
        elif SI == SI.TIME:
            self.turnForT(int(unitValue), direction=direction, power=power, finalAction=finalAction,
                          withFeedback=withFeedback)

    def reset(self, withFeedback: bool = True):
        """Reset the Motor to zero.

        :param withFeedback:
                TRUE: Feedback is required.
                FALSE: No feedback required.
        :returns:
            None
        """
        try:
            assert self.port is not None
            port = self.port

            data: bytes = bytes.fromhex('0b0081{:02}11510200000000'.format(port))
        except AssertionError:
            print('[{}]-[ERR]: Motor has no port assigned... Exit...'.format(self))
            self.Q_cmdsnd_WAITING.put(Command())
        else:
            self.currentAngle = 0.0
            self.previousAngle = 0.0
            self.Q_cmdsnd_WAITING.put(Command(data=data, port=port, withFeedback=withFeedback))


class SingleMotor(Motor):

    def __init__(self,
                 name: str = "SINGLE MOTOR",
                 port: int = 0x00,
                 gearRatio: float = 1.0,
                 cmdQ: Queue = None,
                 terminate: Event = None,
                 debug: bool = False):
        """The object that models a single motor at a certain port.

        :param name:
            A friendly name of the motor
        :param port:
            The port of the SingleMotor (LegoBTLE.Constants.Port can be utilised).
        :param gearRatio:
            The ratio of the number of teeth of the turning gear to the number of teeth of the turned gear.
        :param cmdQ:
            A common multiprocessing.Queue that queues all commands of all motors to be sent to the Hub for execution.
        :param terminate:
            The common terminate signal.
        :param debug:
            Setting
            * True: Debug messages on.
            * False: Debug messages off.
        """
        init()
        self._name: str = name
        if isinstance(port, Port):
            self._port: int = port.value
        else:
            self._port: int = port
        self._gearRatio: float = gearRatio

        self._Q_cmd_EXEC: Queue = cmdQ
        self._Q_rsltrcv_RCV: Queue = Queue(maxsize=-1)
        self._Q_cmdsnd_WAITING: Queue = Queue(maxsize=50)

        self._E_TERMINATE = terminate
        self._E_PROCESSES_TERMINATE: Event = Event()
        self._E_MOTOR_TERMINATED: Event = Event()
        self._E_MOTOR_STARTED: Event = Event()
        self._E_port_FREE: Event = Event()
        self._E_port_FREE.set()
        self._C_port_FREE: Condition = Condition()
        self._debug: bool = debug

        self._currentAngle: float = 0.00
        self._previousAngle: float = 0.00
        self._upm: float = 0.00

        self._lastError: int = 0xff

        self._T_RSLTReceiver: Thread = Thread(target=self.RsltRCV, name="{} RESULT RECEIVER".format(self._name),
                                              daemon=True)
        self._E_rsltrcv_STARTED: Event = Event()
        self._E_rsltrcv_STOPPED: Event = Event()

        self._T_CMDSender: Thread = Thread(target=self.CmdSND, name="{} COMMAND SENDER".format(self._name),
                                           daemon=True)
        self._E_cmdsnd_STARTED: Event = Event()
        self._E_cmdsnd_STOPPED: Event = Event()

        self._T_Listener_STOP: Thread = Thread(target=self.stopMotor, name="{} STOP LISTENER".format(self._name),
                                               daemon=True)
        return

    @property
    def T_Listener_STOP(self) -> Thread:
        return self._T_Listener_STOP

    @property
    def E_TERMINATE(self) -> Event:
        return self._E_TERMINATE

    @property
    def E_MOTOR_TERMINATED(self) -> Event:
        return self._E_MOTOR_TERMINATED

    @property
    def E_PROCESSES_TERMINATE(self) -> Event:
        return self._E_PROCESSES_TERMINATE

    @property
    def E_MOTOR_STARTED(self) -> Event:
        return self._E_MOTOR_STARTED

    @property
    def debug(self) -> bool:
        return self._debug

    @property
    def name(self) -> str:
        return self._name

    @property
    def port(self) -> int:
        return self._port

    def setVirtualPort(self, port: int):
        pass

    @property
    def T_RSLTReceiver(self) -> Thread:
        return self._T_RSLTReceiver

    @property
    def T_CMDSender(self) -> Thread:
        return self._T_CMDSender

    @property
    def Q_cmdsnd_WAITING(self) -> Queue:
        return self._Q_cmdsnd_WAITING

    @property
    def Q_rsltrcv_RCV(self) -> Queue:
        return self._Q_rsltrcv_RCV

    @property
    def Q_cmd_EXEC(self) -> Queue:
        return self._Q_cmd_EXEC

    @property
    def E_cmdsnd_STARTED(self) -> Event:
        return self._E_cmdsnd_STARTED

    @property
    def E_cmdsnd_STOPPED(self) -> Event:
        return self._E_cmdsnd_STOPPED

    @property
    def E_rsltrcv_STARTED(self) -> Event:
        return self._E_rsltrcv_STARTED

    @property
    def E_rsltrcv_STOPPED(self) -> Event:
        return self._E_rsltrcv_STOPPED

    @property
    def E_port_FREE(self) -> Event:
        return self._E_port_FREE

    @property
    def C_port_FREE(self) -> Condition:
        return self._C_port_FREE

    @property
    def gearRatio(self) -> float:
        return self._gearRatio

    @property
    def previousAngle(self) -> float:
        return self._previousAngle

    @previousAngle.setter
    def previousAngle(self, value: float):
        self._previousAngle = value
        return

    @property
    def currentAngle(self) -> float:
        return self._currentAngle

    @currentAngle.setter
    def currentAngle(self, value: float):
        self._currentAngle = value
        return

    @property
    def upm(self) -> float:
        return self._upm

    @property
    def lastError(self) -> int:
        return self._lastError

    @lastError.setter
    def lastError(self, error: int):
        self._lastError = error
        return

    def setToMid(self) -> float:
        """This method positions a motor in mid position between two (mechanical) boundaries.

        :rtype:
            float
        :return:
            The maximum degree to which the motor can turn in either direction.
        """
        self.turnForDegrees(degrees=180, direction=MotorConstant.LEFT, power=20, finalAction=MotorConstant.BREAK,
                            withFeedback=True)
        self.reset(withFeedback=True)
        self.turnForDegrees(degrees=180, direction=MotorConstant.RIGHT, power=20, finalAction=MotorConstant.BREAK,
                            withFeedback=True)

        maxSide2Side = abs(self.currentAngle)
        self.turnForDegrees(degrees=maxSide2Side / 2, direction=MotorConstant.LEFT, power=80, finalAction=MotorConstant.BREAK,
                            withFeedback=True)
        self.reset(withFeedback=True)

        return maxSide2Side / 2


class SynchronizedMotor(Motor):
    """Combination of two separate Motors that are operated in a synchronized manner.
    """
    def __init__(self, name: str,
                 port: int = 0xff,
                 firstMotor: SingleMotor = None,
                 secondMotor: SingleMotor = None,
                 gearRatio: float = 1.0,
                 execQ: Queue = None,
                 terminate: Event = None,
                 debug: bool = False):
        """

        :param name:
        :param port:
        :param firstMotor:
        :param secondMotor:
        :param gearRatio:
        :param execQ:
        :param terminate:
        :param debug:
        """
        init()
        self._name: str = name
        self._port = port  # f"{ersterMotor.port:02}{zweiterMotor.port:02}"
        self._firstMotor: SingleMotor = firstMotor
        self._portFreeFM: Event = self._firstMotor.E_port_FREE
        self._secondMotor: SingleMotor = secondMotor
        self._portFreeSM: Event = self._secondMotor.E_port_FREE
        self._gearRatio: float = gearRatio

        self._Q_cmd_EXEC: Queue = execQ
        self._Q_rsltrcv_RCV: Queue = Queue(maxsize=-1)
        self._Q_cmdsnd_WAITING: Queue = Queue(maxsize=50)

        self._T_RSLTReceiver: Thread = Thread(target=self.RsltRCV, name="{} RESULT RECEIVER".format(self._name),
                                              daemon=True)
        self._E_rsltrcv_STARTED: Event = Event()
        self._E_rsltrcv_STOPPED: Event = Event()

        self._T_CMDSender: Thread = Thread(target=self.CmdSND, name="{} COMMAND SENDER".format(self._name),
                                           daemon=True)
        self._E_cmdsnd_STARTED: Event = Event()
        self._E_cmdsnd_STOPPED: Event = Event()

        self._T_Listener_STOP: Thread = Thread(target=self.stopMotor, name="{} STOP LISTENER".format(self._name),
                                               daemon=True)

        self._E_TERMINATE: Event = terminate
        self._E_PROCESSES_TERMINATE: Event = Event()
        self._E_MOTOR_TERMINATED: Event = Event()
        self._E_MOTOR_STARTED: Event = Event()
        self._portSyncFree: Event = Event()
        self._portSyncFree.set()
        self._portSyncFreeCondition: Condition = Condition()
        self._debug: bool = debug

        self._currentAngle: float = 0.00
        self._previousAngle: float = 0.00
        self._upm: float = 0.00

        self._lastError: int = 0xff
        return

    @property
    def E_TERMINATE(self) -> Event:
        return self._E_TERMINATE

    @property
    def E_PROCESSES_TERMINATE(self) -> Event:
        return self._E_PROCESSES_TERMINATE

    @property
    def E_MOTOR_TERMINATED(self) -> Event:
        return self._E_MOTOR_TERMINATED

    @property
    def E_MOTOR_STARTED(self) -> Event:
        return self._E_MOTOR_STARTED

    @property
    def T_Listener_STOP(self) -> Thread:
        return self._T_Listener_STOP

    @property
    def T_RSLTReceiver(self) -> Thread:
        return self._T_RSLTReceiver

    @property
    def T_CMDSender(self) -> Thread:
        return self._T_CMDSender

    @property
    def Q_rsltrcv_RCV(self) -> Queue:
        return self._Q_rsltrcv_RCV

    @property
    def Q_cmdsnd_WAITING(self) -> Queue:
        return self._Q_cmdsnd_WAITING

    @property
    def Q_cmd_EXEC(self) -> Queue:
        return self._Q_cmd_EXEC

    @property
    def E_cmdsnd_STARTED(self) -> Event:
        return self._E_cmdsnd_STARTED

    @property
    def E_cmdsnd_STOPPED(self) -> Event:
        return self._E_cmdsnd_STOPPED

    @property
    def name(self) -> str:
        return self._name

    @property
    def E_port_FREE(self) -> Event:
        return self._portSyncFree

    @property
    def gearRatio(self) -> float:
        return self._gearRatio

    @property
    def port(self) -> int:
        return self._port

    @property
    def previousAngle(self) -> float:
        return self._previousAngle

    @property
    def currentAngle(self) -> float:
        return self._currentAngle

    @property
    def upm(self) -> float:
        return self._upm

    @property
    def debug(self) -> bool:
        return self._debug

    def setVirtualPort(self, port: int):
        self._port = port

    @property
    def firstMotor(self) -> SingleMotor:
        return self._firstMotor

    @property
    def secondMotor(self) -> SingleMotor:
        return self._secondMotor

    @property
    def lastError(self) -> int:
        return self._lastError

    @lastError.setter
    def lastError(self, error: int):
        self._lastError = error
        return

    @property
    def C_port_FREE(self) -> Condition:
        return self._portSyncFreeCondition

    @property
    def E_rsltrcv_STARTED(self) -> Event:
        return self._E_rsltrcv_STARTED

    @property
    def E_rsltrcv_STOPPED(self) -> Event:
        return self._E_rsltrcv_STOPPED

    def configureVirtualPort(self, port: int) -> None:
        """Issue the command to set a commonly used synchronized port (i.e. Virtual Port) for the synchronized Motor.

        :return:
            None
        """
        data: bytes = bytes.fromhex(
                '06006101' + '{:02}'.format(self._firstMotor.port) + '{:02}'.format(self._secondMotor.port))
        command: Command = Command(data=data, port=self._port, withFeedback=True)
        with self._portSyncFreeCondition:
            if self.debug:
                print("[{}]-[CMD]: WAITING: Port free for COMMAND SYNC PORT".format(self))
            self._portSyncFreeCondition.wait_for(
                    lambda: self._firstMotor.E_port_FREE.is_set() & self._secondMotor.E_port_FREE.is_set())

            if self.debug:
                print("[{}]-[SIG]: PASS: Port free for COMMAND SYNC PORT".format(self))
            self._portSyncFree.clear()
            self._firstMotor.E_port_FREE.clear()
            self._secondMotor.E_port_FREE.clear()

            if self.debug:
                print("[{}]-[SIG]: CMD SENT TO EXEC QUEUE for COMMAND SYNC PORT".format(self))
            self.Q_cmdsnd_WAITING.put(command)

            self._portSyncFreeCondition.notify_all()
            return

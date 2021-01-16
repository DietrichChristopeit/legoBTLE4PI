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
import queue
import threading
from abc import ABC, abstractmethod
from time import sleep

from LegoBTLE.Constants.Port import Port
from LegoBTLE.Constants.MotorConstant import MotorConstant
from LegoBTLE.Constants import SIUnit
from LegoBTLE.Device.Command import Command


class Motor(ABC):
    """Abstract base class for all Motor Types."""

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
    def rcvQ(self) -> queue.Queue:
        raise NotImplementedError

    @property
    @abstractmethod
    def portFree(self) -> threading.Event:
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
    def port(self) -> int:
        raise NotImplementedError

    @port.setter
    @abstractmethod
    def port(self, port: int):
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
    def debug(self) -> bool:
        raise NotImplementedError

    def receiver(self, terminate: threading.Event):
        print("[{}]-[MSG]: Receiver started...".format(threading.current_thread().getName()))

        while not terminate.is_set():
            if self.rcvQ.empty():
                sleep(1.0)
                continue
            result: Command = self.rcvQ.get()
            if result.data[len(result.data) - 1] == 0x0a:
                if self.debug:
                    print(
                        "[{}]-[MSG]: freeing port {:02x}...".format(threading.current_thread().getName(), self.port))
                self.portFree.set()
            if self.debug:
                print(
                    "[{:02x}]-[MSG]: received result: {:02x}".format(result.data[3], result.data[len(result.data) - 1]))

        print("[{}]-[SIG]: RECEIVER SHUT DOWN COMPLETE...".format(threading.current_thread().getName()))
        return

    # Commands available
    def turnForT(self, milliseconds: int, direction: MotorConstant = MotorConstant.FORWARD, power: int = 50,
                 finalAction: MotorConstant = MotorConstant.BREAK, withFeedback=True) -> Command:
        """This method can be used to calculate the data to turn a motor for a specific time period.

            :rtype:
                Command
            :param milliseconds:
                The duration for which the motor type should turn.
            :param direction:
                Either the driving direction (MotorConstant.FORWARD or MotorConstant.BACKWARD) or the steering direction (
                MotorConstant.LEFT or
                MotorConstant.RIGHT).
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
                The calculated command object.
        """
        power = direction.value * power

        try:
            assert self.port is not None

            port = self.port

            data: bytes = bytes.fromhex('0c0081{:02x}1109'.format(port) + milliseconds.to_bytes(2, byteorder='little',
                                                                                                signed=False).hex() \
                                        + \
                                        power.to_bytes(1, byteorder='little', signed=True).hex() + '64{:02x}03'.format(
                finalAction.value))
        except AssertionError:
            print('[{}]-[ERR]: Motor has no port assigned... Exit...'.format(self))
            return None
        else:
            command: Command = Command(data=data, port=port, withFeedback=withFeedback)
            return command

    def turnForDegrees(self, degrees: float, direction: MotorConstant = MotorConstant.FORWARD, power: int = 50,
                       finalAction: MotorConstant = MotorConstant.BREAK, withFeedback: bool = True) -> Command:
        """This method is used to calculate the data to turn a motor for a specific value of degrees (°).


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
        :rtype:
            Command
        :returns:
                The calculated command object.
        """

        power = direction.value * power
        degrees = round(degrees * self.gearRatio)

        try:
            assert self.port is not None

            port = self.port

            data: bytes = bytes.fromhex('0e0081{:02x}110b'.format(port) + degrees.to_bytes(4,
                                                                                           byteorder='little',
                                                                                           signed=False).hex() \
                                        + power.to_bytes(1, byteorder='little',
                                                         signed=True).hex() + '64{:02x}03'.format(
                finalAction.value))
        except AssertionError:
            print('[{}]-[ERR]: Motor has no port assigned... Exit...'.format(self))
            return None
        else:
            command: Command = Command(data=data, port=port, withFeedback=withFeedback)
            return command

    def turnMotor(self, SI: SIUnit, unitValue: float = 0.0, direction: MotorConstant = MotorConstant.FORWARD,
                  power: int = 50, finalAction: MotorConstant = MotorConstant.BREAK,
                  withFeedback: bool = True) -> Command:
        """Diese Methode dreht einen Motor, wobei der Aufrufer die Art durch die Angabe der Einheit spezifiziert.


        :rtype:
            str
        :param SI: 
            SI-Einheit, basierend auf welcher der Motor gedreht werden soll (z.B. SIUnit.ANGLE).
        :param unitValue:
            Um welchen Wert in der Einheit SI soll gedreht werden.
        :param direction:
            Entweder die Fahrrichtung (MotorConstant.FORWARD oder MotorConstant.BACKWARD) oder die Lenkrichtung (
            MotorConstant.LEFT oder
            MotorConstant.RIGHT).
        :param power: 
            Ein Wert von 0 bis 100.
        :param finalAction:
            Bestimmt, wie sich der Motor, nachdem die Drehungen beendet wurden, verhalten soll,
            d.h. 
            * MotorConstant.COAST = der Motor hält nicht sofort an, sodern dreht sich aus eigener Kraft bis zum
            Stillstand; 
            * MotorConstant.BREAK = der Motor wird angehalten, kann jedoch durch Krafteinwirkung von aussen gedreht
            werden; 
            * MotorConstant.HOLD = Motor wird in der Endposition gehalten, auch wenn Kräfte von aussen versuchen,
            den Motor zu drehen.
        :param withFeedback:
                TRUE: Feedback is required.
                FALSE: No feedback required.
        :returns: 
            Das aus den Angaben berechnete Kommando wird zurückgeliefert.
        """
        command: Command = None

        if SI == SI.ANGLE:
            command: Command = self.turnForDegrees(unitValue, direction=direction, power=power, finalAction=finalAction,
                                                   withFeedback=withFeedback)
        elif SI == SI.TIME:
            command: Command = self.turnForT(int(unitValue), direction=direction, power=power, finalAction=finalAction,
                                             withFeedback=withFeedback)

        try:
            assert command is not None
        except AssertionError:
            print('[{}]-[ERR]: Motor has no port assigned... Exit...'.format(self))
            return None
        else:
            return command

    def reset(self, withFeedback: bool = True) -> Command:

        try:
            assert self.port is not None
            port = self.port

            data: bytes = bytes.fromhex('0b0081{:02x}11510200000000'.format(port))
        except AssertionError:
            print('[{}]-[ERR]: Motor has no port assigned... Exit...'.format(self))
            return None
        else:
            self.currentAngle = 0.0
            self.previousAngle = 0.0
            command = Command(data=data, port=port, withFeedback=withFeedback)
            return command


class SingleMotor(threading.Thread, Motor):

    def __init__(self, name: str, port: Port, gearRatio: float = 1.0, execQ: queue.Queue = None,
                 terminateOn: threading.Event = None, debug: bool = False):
        """

        :param name:
        :param port:
        :param gearRatio:
        :param execQ:
        :param terminateOn:
        :param debug:
        """
        super().__init__()
        self._name: str = name
        self._port: int = port.value
        self._gearRatio: float = gearRatio

        self._execQ: queue.Queue = execQ
        self._rcvQ: queue.Queue = queue.Queue(maxsize=100)
        self._cmdQ: queue.Queue = queue.Queue()

        self._terminate: threading.Event = terminateOn
        self._portFree: threading.Event = threading.Event()
        self._portFree.set()
        self.setDaemon(True)
        self._debug: bool = debug

        self._currentAngle: float = 0.00
        self._previousAngle: float = 0.00
        self._upm: float = 0.00

    def run(self):
        if self._debug:
            print("[{}]-[MSG]: Started...".format(threading.current_thread().getName()))
        receiver = threading.Thread(target=self.receiver, args=(self._terminate,),
                                    name="{} RECEIVER".format(self._name), daemon=True)
        receiver.start()

        self._terminate.wait()
        if self._debug:
            print("[{}]-[SIG]: SHUTTING DOWN...".format(threading.current_thread().getName()))
        receiver.join()
        if self._debug:
            print("[{}]-[SIG]: SHUT DOWN COMPLETE...".format(threading.current_thread().getName()))
        return

    @property
    def name(self) -> str:
        return self._name

    @property
    def rcvQ(self) -> queue.Queue:
        return self._rcvQ

    @property
    def portFree(self) -> threading.Event:
        return self._portFree

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

    def setToMid(self) -> Command:
        """Mit dieser Methode wird der MotorTyp sozusagen in die Mitte gestellt.

        :rtype:
            float
        :return:
            Der maximale Winkel, den der MotorTyp in eine Richtung drehen kann.
        """

        command: Command = None

        return command


class KombinierterMotor(threading.Thread):
    """Combination of two seperate Motors that are operated in a synchronized manner.
    """
    def __init__(self, name: str, port: int, firstMotorPort: Port, secondMotorPort: Port, gearRatio: float = 1.0, execQ: queue.Queue = None,
                 terminateOn: threading.Event = None, debug: bool = False):
        """

        :param gemeinsamerMotorAnschluss:
        :param ersterMotorAnschluss:
        :param zweiterMotorAnschluss:
        """

        super().__init__()
        self._anschluss = gemeinsamerMotorAnschluss  # f"{ersterMotor.port:02}{zweiterMotor.port:02}"
        self._ersterMotorAnschluss = ersterMotorAnschluss
        self._zweiterMotorAnschluss = zweiterMotorAnschluss
        self._uebersetzung: float = uebersetzung

        self._nameMotor: str = name
        self._vorherigerWinkel: float = 0.00
        self._aktuellerWinkel: float = 0.00
        self._waitCmd = threading.Event()
        self._waitCmd.clear()
        self._upm: int = 0

    @property
    def name(self) -> str:
        pass

    @property
    def rcvQ(self) -> queue.Queue:
        pass

    @property
    def portFree(self) -> threading.Event:
        pass

    @property
    def gearRatio(self) -> float:
        pass

    @property
    def port(self) -> int:
        pass

    @property
    def previousAngle(self) -> float:
        pass

    @property
    def currentAngle(self) -> float:
        pass

    @property
    def upm(self) -> float:
        pass

    @property
    def debug(self) -> bool:
        pass



    @property
    def ersterMotorAnschluss(self) -> Port:
        return self._ersterMotorAnschluss

    @property
    def zweiterMotorAnschluss(self) -> Port:
        return self._zweiterMotorAnschluss

    def definiereGemeinsamenMotor(self):
        return bytes.fromhex(
            '06006101' + '{:02x}'.format(self._ersterMotorAnschluss) + '{:02x}'.format(self._zweiterMotorAnschluss))

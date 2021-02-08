# **************************************************************************************************
#  MIT License                                                                                     *
#                                                                                                  *
#  Copyright (c) 2021 Dietrich Christopeit                                                         *
#                                                                                                  *
#  Permission is hereby granted, free of charge, to any person obtaining a copy                    *
#  of this software and associated documentation files (the "Software"), to deal                   *
#  in the Software without restriction, including without limitation the rights                    *
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell                       *
#  copies of the Software, and to permit persons to whom the Software is                           *
#  furnished to do so, subject to the following conditions:                                        *
#                                                                                                  *
#  The above copyright notice and this permission notice shall be included in all                  *
#  copies or substantial portions of the Software.                                                 *
#                                                                                                  *
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR                      *
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,                        *
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE                     *
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER                          *
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,                   *
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE                   *
#  SOFTWARE.                                                                                       *
# **************************************************************************************************
import concurrent
from collections import deque
from concurrent import futures
from concurrent.futures._base import wait
from concurrent.futures.thread import ThreadPoolExecutor
from threading import Condition, Event, Timer, current_thread
from time import sleep

from LegoBTLE.Constants.MotorConstant import MotorConstant
from LegoBTLE.Constants.Port import Port
from LegoBTLE.Controller.THub import Hub
from LegoBTLE.Debug.messages import BBR, DBY, MSG
from LegoBTLE.Device.TMotor import Motor, SingleMotor, SynchronizedMotor


def submitMotors(motors: [Motor]) -> [futures.Future]:

    with ThreadPoolExecutor(max_workers=len(motors)*2) as executor:
        fut: [futures.Future] = []
        for motor in motors:
            F_CMD_SENDER_DEVICE = futures.Future()
            F_RSLT_RECEIVER_DEVICE = futures.Future()
            executor.submit(motor.CmdSND, F_CMD_SENDER_DEVICE)
            executor.submit(motor.RsltRCV, F_RSLT_RECEIVER_DEVICE)
            fut.extend([F_CMD_SENDER_DEVICE, F_RSLT_RECEIVER_DEVICE])
        return fut


def startSystem(hub: Hub, motors: [Motor]) -> Event:
    E_SYSTEM_STARTED: Event = Event()
    for motor in motors:
        hub.register(motor)
    with ThreadPoolExecutor() as executor:
        fut: [futures.Future] =[]
        listenerStarted: futures.Future = futures.Future()
        fut.append(listenerStarted)
        receiverStarted: futures.Future = futures.Future()
        fut.append(receiverStarted)
        senderStarted: futures.Future = futures.Future()
        fut.append(senderStarted)
        reqNotificationsStarted: futures.Future = futures.Future()
        fut.append(reqNotificationsStarted)
        executor.submit(hub.listenNotif, listenerStarted)
        executor.submit(hub.rslt_RCV, receiverStarted)
        executor.submit(hub.cmd_SND, senderStarted)
        executor.submit(hub.requestNotifications, reqNotificationsStarted)
        futures.wait([reqNotificationsStarted], return_when='ALL_COMPLETED')

        for motor in motors:
            F_CMD_SENDER_DEVICE: futures.Future = futures.Future()
            F_RSLT_RECEIVER_DEVICE: futures.Future = futures.Future()
            executor.submit(motor.CmdSND, F_CMD_SENDER_DEVICE)
            executor.submit(motor.RsltRCV, F_RSLT_RECEIVER_DEVICE)
            fut.append(F_CMD_SENDER_DEVICE)
            fut.append(F_RSLT_RECEIVER_DEVICE)
        futures.wait(fut, return_when='ALL_COMPLETED')
        print("ALL STARTED")
        dev_notif: [futures.Future] =[]
        for motor in motors:
            F_DEVICE_REQ_NOTIFICATIONS_SENT: futures.Future = futures.Future()
            executor.submit(motor.subscribeNotifications, F_DEVICE_REQ_NOTIFICATIONS_SENT)
            dev_notif.append(F_DEVICE_REQ_NOTIFICATIONS_SENT)
            # if f0.running() and f1.running():
            #     f2 = executor.submit(motor.subscribeNotifications())
           # motor.E_DEVICE_INIT.wait()
        futures.wait(dev_notif, return_when='ALL_COMPLETED')
        print(hub.r_d)
        futr = executor.submit(motors[0].reset, 0.0)
        print(futr.result())
        futr1 = executor.submit(motors[1].reset, 0.0)
        print(futr1.result())
        futures.wait([futr, futr1])

        fut1 = executor.submit(motors[0].turnForT,
                               5000,
                               MotorConstant.FORWARD,
                               100,
                               MotorConstant.HOLD,
                               False,
                               True)
        futures.wait([fut1], return_when='ALL_COMPLETED')
        
        fut2 = executor.submit(motors[1].turnForT,
                               5000,
                               MotorConstant.BACKWARD,
                               100,
                               MotorConstant.HOLD,
                               False,
                               True)

        futures.wait([fut1, fut2], return_when='ALL_COMPLETED')

        fut3 = executor.submit(motors[0].turnForT,
                               5000,
                               MotorConstant.BACKWARD,
                               100,
                               MotorConstant.HOLD,
                               False,
                               True)
        futures.wait([fut3], return_when='ALL_COMPLETED')
        # executor.submit(terminate.set)
    return E_SYSTEM_STARTED


def stopSystem():
    # terminate.set()
    MSG((current_thread().name,), msg="[{}]-[MSG]: COMMENCE SHUTDOWN...", doprint=True, style=DBY())
    
    hub.shutDown()
    E_SYSTEM_STOPPED.set()
    return


if __name__ == '__main__':
    
    E_SYSTEM_STOPPED: Event = Event()
    terminate: Event = Event()
    cmdQ: deque = deque(maxlen=80)
    
    #  BEGIN HUB Spec
    hub: Hub = Hub(address='90:84:2B:5E:CF:1F', name="Threaded Hub", cmdQ=cmdQ, terminate=terminate, debug=True)
    #  END HUB Spec
    
    #  BEGIN Motor Spec
    motors: [Motor] = [
        SingleMotor(name="Vorderradantrieb", port=Port.A, gearRatio=2.67, cmdQ=cmdQ, terminate=terminate, debug=True),
        SingleMotor(name="Hinterradantrieb", port=Port.B, gearRatio=2.67, cmdQ=cmdQ, terminate=terminate, debug=True)]
    
    # motors.append(SynchronizedMotor(name="4-Rad-Antrieb", firstMotor=motors[0], secondMotor=motors[1],
    #                               gearRatio=2.67,cmdQ=cmdQ, terminate=terminate, debug=True))
    E_JEEP_SYSTEMS_STARTED = startSystem(hub=hub, motors=motors)
    # E_JEEP_SYSTEMS_STARTED.wait()
    # #  END Motor Spec
    #
    # #  commands
    # motors[0].turnForT(milliseconds=2560, direction=MotorConstant.FORWARD, power=100, finalAction=MotorConstant.COAST,
    #                    withFeedback=True)
    # motors[1].turnForT(milliseconds=2560, direction=MotorConstant.FORWARD, power=100, finalAction=MotorConstant.COAST,
    #                    withFeedback=True)
    # motors[0].turnForT(milliseconds=2560, direction=MotorConstant.BACKWARD, power=100, finalAction=MotorConstant.COAST,
    #                    withFeedback=True)
    # motors[0].turnForT(milliseconds=5000, direction=MotorConstant.FORWARD, power=100, finalAction=MotorConstant.COAST,
    #                    withFeedback=True)
    #
    # stopp: Timer = Timer(120.0, stopSystem, args=())
    # stopp.start()
    
    # E_SYSTEM_STOPPED.wait(10)
    MSG((current_thread().name,), msg="[{}]-[MSG]: SHUTDOWN COMPLETE...", doprint=True, style=BBR())

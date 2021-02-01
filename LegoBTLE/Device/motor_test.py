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


if __name__ == '__main__':
    cmdQ: Queue = Queue(maxsize=-1)
    terminate: Event = Event()

    vorderradantrieb: SingleMotor = SingleMotor(name="Vorderradantrieb", port=Port.A, gearRatio=2.67, cmdQ=cmdQ,
                                                terminate=terminate, debug=True)

    T_SND_vorderradantrieb: Thread = Thread(name="PVorderrad", target=vorderradantrieb.CmdSND, daemon=True)

    T_RCV_vorderradantrieb: Thread = Thread(name="PVorderrad", target=vorderradantrieb.RsltRCV, daemon=True)
    T_RCV_vorderradantrieb.start()
    T_SND_vorderradantrieb.start()

    vorderradantrieb.turnForT(2560, MotorConstant.FORWARD, 80, MotorConstant.HOLD, True)
    vorderradantrieb.subscribeNotifications(withFeedback=True)
    sleep(20)

    terminate.set()
    T_SND_vorderradantrieb.join(2)
    T_RCV_vorderradantrieb.join(2)

    print("[{}]-[SIG]: SHUTDOWN COMPLETE".format(current_thread().name))

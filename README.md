# Controlling the Lego(c) Technics Hub (Hub 2) via Bluetooth (btle) using a Rasperry Pi 4B
A school project that shows how to control a Lego Jeep with Bluetooth on the Raspberry Pi 4B.

The project tries to give pupils at the age of around 11 years the ability to program their Lego bots on a Rasberry Pi 4B connecting via Bluetooth.

####Short Description: 
I am not sure if I could entirely reach that goal. 
However, this project models and implements:
* an *asyncio TCP streaming socket server* that 
    * receives commands from the attached devices
    * sends the commands to the Lego(c) Technic Hub 2.0 via Bluetooth connection
    * returns the feedback of the commands executed to the attached devices
* an abstraction layer that models the *attached device in general*
* an abstraction layer *modelling the greater part* of the *Lego(c) Wireless Protocol 3.0* (see: https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#document-index ) 
    * One can argue the design of course, but I tried to keep everything as simple to use as possible. Now and then the software engineer will notice few redundancies that could be avoided - I am aware of this, but I had good reasons for doing so. Of course, I appreciate and would love to get comments and suggestions regarding the design.
* a concrete device that models the *Hub Brick* and makes it functions accessible: any intelligent Brick that adheres to Lego's(c) Wireless Protocol should be usable without problems (I tested it on the Lego(c) Technic Hub 2.0)
* a concrete device that models a *Single Motor*
    * almost everything has been implemented here; only the Mode Setting/Selection stuff is a mystery to me still.
    * also custom functions to stop time between commands in order to calculate average the speed, or the distance are available and are added over time
* a concrete device that models a *Synchronized Motor*
* a class *Experiment* that could once be the basis for a GUI but currently gives the user the means to:
    * define the Device Instances
    * set up and execute a command sequence - the *Experiment*
    
As indicated earlier, this project uses Python's *asyncio*.
Python 3.7.3 is used as it is the Raspberry Pi's current supported Python version. However, the project has been tested on Python 3.9 as well.

This is my first Python project, and I have many more years experience in C/C++ and Java - so please be gentle if I failed to adhere to the pythonic way once in a while.

####Sources of information
1. [Lego Boost Roboter steuern mit Python unter Windows oder Linux](https://www.tec.reutlingen-university.de/fileadmin/user_upload/Fakultaet_TEC/LegoBoostPython_V4_final.pdf "LegoBoostPython_V4_final.pdf"), S. Mack, Vers. 4 22.3.20, Reutlingen University, 
2. [Lego's(c) Wireless Protocol](https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#document-index)
3. [Reverse engineering the LEGO BOOST Hub](https://github.com/JorgePe/BOOSTreveng), J. Pereira, 
4. Internet :-)
5. bruteforce: send possible commands and, see what happens

####Small example:
    async def main():
        e: Experiment = Experiment(name='Experiment0', measure_time=True, debug=True)
        
        HUB: Hub = Hub(name='LEGO HUB 2.0', server=('127.0.0.1', 8888))
        FWD: SingleMotor = SingleMotor(name='FWD', port=b'\x01', server=('127.0.0.1', 8888), gearRatio=2.67)
        STR: SingleMotor = SingleMotor(name='STR', port=b'\x02', server=('127.0.0.1', 8888), gearRatio=2.67)
        RWD: SingleMotor = SingleMotor(name='RWD', port=b'\x00', server=('127.0.0.1', 8888), gearRatio=1.00)
    
        experimentActions: List[e.Action] = [e.Action(cmd=HUB.connect_ext_srv),
                                             e.Action(cmd=RWD.connect_ext_srv, only_after=True),
    
                                             e.Action(cmd=HUB.GENERAL_NOTIFICATION_REQUEST),
                                             e.Action(cmd=RWD.REQ_PORT_NOTIFICATION, only_after=True),
    
                                             e.Action(cmd=RWD.START_SPEED_TIME, kwargs={'speed': 70,
                                                                                        'direction': MOVEMENT.FORWARD,
                                                                                        'on_completion': MOVEMENT.BREAK,
                                                                                        'power': 100, 'time': 5000}),

                                             e.Action(cmd=RWD.START_SPEED_TIME, kwargs={'speed': 65,
                                                                                        'direction': MOVEMENT.REVERSE,
                                                                                        'on_completion': MOVEMENT.COAST,
                                                                                        'power': 60, 'time': 5000}),
                                             ]
    
        e.append(experimentActions)
        taskList, runtime = e.runExperiment()
    
        print(f"Total execution time: {runtime}")
    
        # keep alive
        while True:
            await asyncio.sleep(.5)
    
    if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    asyncio.run(main())
    loop.run_forever()





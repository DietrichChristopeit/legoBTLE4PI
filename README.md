# Controlling the Lego(c) Technics Hub (Hub 2) via Bluetooth (btle) using a Rasperry Pi 4B

#### Summary:
A school project that shows how to control a Lego Jeep with Bluetooth on the Raspberry Pi 4B.

The project tries to give pupils at the age of around 11 years the ability to program their Lego bots on a Rasberry Pi 4B connecting via Bluetooth.

#### Short Description: 
I am not sure if I could entirely reach that goal. 
However, this project models and implements:
* an *asyncio TCP streaming socket server* that 
    * receives commands from the attached devices
    * sends the commands to the Lego(c) Technic Hub 2.0 via Bluetooth connection
    * returns the feedback of the commands executed to the attached devices
* an abstraction layer that models the *attached device in general*
* an abstraction layer *modelling the greater part* of the *Lego(c) Wireless Protocol 3.0* (see: [Lego(c) Wireless Protokoll](https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#document-index "Lego(c) Wireless Protocoll")) 
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

#### Sources of information:

1. [Lego Boost Roboter steuern mit Python unter Windows oder Linux](https://www.tec.reutlingen-university.de/fileadmin/user_upload/Fakultaet_TEC/LegoBoostPython_V4_final.pdf "LegoBoostPython_V4_final.pdf"), S. Mack, Vers. 4 22.3.20, Reutlingen University, 
2. [Lego's(c) Wireless Protocol](https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#document-index)
3. [Reverse engineering the LEGO BOOST Hub](https://github.com/JorgePe/BOOSTreveng), J. Pereira 
4. Internet :-)
5. bruteforce: send possible commands and, see what happens

#### Small example:

    loopy = asyncio.get_running_loop()
    e: Experiment = Experiment(name='Experiment0',
                               measure_time=False,
                               debug=True)
    # Device definitions
    HUB: Hub = Hub(name='LEGO HUB 2.0', # any string is allowed
                   server=('127.0.0.1', 8888),
                   debug=True)
    RWD: SingleMotor = SingleMotor(name='RWD', # any string is allowed
                                   server=('127.0.0.1', 8888),
                                   port=PORT.A,
                                   gearRatio=2.67, 
                                   debug=True)
    # ###################
    
    # Connect the Devices with the Server and make them get notifications
    t1 = await asyncio.wait_for(e.run(_setupNotifyConnect([HUB, RWD]),
                                                                   loop=loopy),
                                timeout=None)
    
    experimentActions_USE_ACC_DEACC_PROFILE = [
            
            {'cmd': RWD.SET_ACC_PROFILE,
             'kwargs': {'ms_to_full_speed': 2000, 'profile_nr': 1, },
             'task': {'tp_id': 'HUB_ACC_PROFILE', }
             },
            {'cmd': RWD.SET_DEC_PROFILE,
             'kwargs': {'ms_to_zero_speed': 300, 'profile_nr': 1, },
             'task': {'tp_id': 'HUB_DEACC_PROFILE', }
             },
            {'cmd': FWD.SET_ACC_PROFILE,
             'kwargs': {'ms_to_full_speed': 20, 'profile_nr': 2, },
             'task': {'tp_id': 'HUB_FWD_ACC_PROFILE', }
             },
            {'cmd': FWD.SET_DEC_PROFILE,
             'kwargs': {'ms_to_zero_speed': 3000, 'profile_nr': 2, },
             'task': {'tp_id': 'HUB_FWD_DEACC_PROFILE', }
             },
            {'cmd': RWD.SET_ACC_PROFILE,
             'kwargs': {'ms_to_full_speed': 2, 'profile_nr': 3, },
             'task': {'tp_id': 'HUB_ACC_PROFILE', }
             },
            {'cmd': RWD.SET_DEC_PROFILE,
             'kwargs': {'ms_to_zero_speed': 250, 'profile_nr': 3, },
             'task': {'tp_id': 'HUB_DEACC_PROFILE', }
             },
            
            {'cmd': RWD.START_SPEED_TIME,
             'kwargs': {'time': 10000,
                        'speed': 100,
                        'power': 100,
                        'on_completion': MOVEMENT.COAST,
                        'use_profile': 1,
                        'delay_before': 0.0,
                        'delay_after': 0.0,
                        },
             'task': {'tp_id': 'RWD_GOTO', }
             },
            {'cmd': RWD.START_SPEED_TIME,
             'kwargs': {'time': 10000,
                        'speed': -100,
                        'power': 100,
                        'on_completion': MOVEMENT.COAST,
                        'use_profile': 1,
                        'delay_before': 0.0,
                        'delay_after': 0.0,
                        },
             'task': {'tp_id': 'RWD_GOTO1', }
             },
            
            {'cmd': RWD.START_MOVE_DEGREES,
             'kwargs': {
                     'use_profile': 2,
                     'on_completion': MOVEMENT.HOLD,
                     'degrees': 360,
                     'delay_before': 3.0,
                     'speed': 100,
                     'abs_max_power': 100
                     },
             'task': {'tp_id': 'RWD_DEG1', }
             },




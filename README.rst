===========
legoBTLE4PI
===========

Prosa Introduction
==================

legoBTLE4PI aims to provide an easy solution to give almost the same access to the functionality of 'cheaper' hubs like
the Lego(c) `Technic Powered Up Hub <https://www.lego.com/de-ch/product/hub-88009>`_.

Such models are often used in cheaper Lego(c) Technic sets but have an amazing range of built-in functionality, e.g.,
tilt-sensors etc.

We wanted to achieve to connect and control the hub only using standard devices (no extra connectivity device etc.)
and free and open-source libraries on a standard Raspberry Pi4 model using Bluetooth.

This said, we ended up using:

*  *Lego*(c) *Technic Powered Up Hub #88012*
*  *Raspberry Pi 4, 8GB Ram (RAM size of 8 GB not required though)*
*  `DietPi 7.1 <https://dietpi.com/>`_ running (lightning fast, efficient and secure distribution, however, many things have to be tweaked and
   set and done to make some things happen; I definitively stay with it, and learn to, e.g., connect and mount my USB
   drive at boot time, has a great and helpful community :-) )
*  *Python 3.7.3* - later *Python 3.10*

   *  using :code:`asyncio`
   *  the library :code:`bluepy`

*  *pycharm*(c) *Community edition 2021.1.1*

   *  for no special reason pycharm(c) is used on Windows (I can't remember, but I guess it was too much for the
      Pi and some functionality I liked was not available on Linux).
   *  After overcoming the initial hurdles we could switch to an all out Linux development base thereby abandoning Windows platforms entirely.
   *  Later in the project I was happy and thankful to receive a licencse for the professional version of *pycharm*(c) through JetBrains' 
      Open Source Development program. This sped up the development massively. We then used the latest versions available.

Goals reached, goals not reached (so far) and additional goals
--------------------------------------------------------------

legoBTLE4Pi started out as a school project that aimed to show how to control a such a Lego(c) Jeep with Bluetooth on the Raspberry Pi.

The project tries to give pupils at the age of around 11 years the ability to program their Lego(c) bots on a Rasberry Pi 4B connecting via Bluetooth.

Goals Reached
-------------

This project models and implements:

*  an *asyncio TCP streaming socket server* that

   *  receives commands from the attached devices
   *  sends the commands to the Lego(c) Technic Hub 2.0 via Bluetooth connection
   *  returns the feedback of the commands executed to the attached devices

*  an abstraction layer that models the *attached device in general*
*  an abstraction layer *modelling the greater part* of the *Lego(c) Wireless Protocol 3.0* (see: `Lego(c) Wireless Protocol <https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#document-index>`_)

   *  One can argue the design of course, but I tried to keep everything as simple to use as possible. Now and then the software engineer will notice few redundancies that could be avoided - I am aware of this, but I had good reasons for doing so. Of course, I appreciate and would love to get comments and suggestions regarding the design.

*  a concrete device that models the *Hub Brick* and makes it functions accessible: any intelligent Brick that adheres to Lego's(c) Wireless Protocol should be usable without problems (I tested it on the Lego(c) Technic Hub 2.0)
*  a concrete device that models a *Single Motor*

   *  almost everything has been implemented here; only the Mode Setting/Selection stuff is a mystery to me still.
   *  also custom functions to stop time between commands in order to calculate average the speed, or the distance are available and are added over time

*  a concrete device that models a *Synchronized Motor*
*  a class *Experiment* that could once be the basis for a GUI but currently gives the user the means to:

   *  define the Device Instances
   *  set up and execute a command sequence - the *Experiment*

As indicated earlier, this project uses Python's :code:`asyncio`.
Python 3.7.3 is used as it is the Raspberry Pi's current supported Python version. However, the project has been tested
on Python 3.10 as well and works fine too.

This is my first Python project, and I have many more years experience in C/C++ and Java - so please be gentle if I failed to adhere to the pythonic way once in a while.

Goals not Reached
-----------------

*  I aimed to spark the interest in robotics and programming in general and the OO methodology in particular. I am not sure if I could entirely reach that goal - however the student presented the outcome and received the best mark.
*  I aimed and still pursue the goal to enable interested students to easily motorize and enhance their Lego(c) Robots. To reach that goal more work has to be done. However, this projects is the basis of further development.
*  Clearly the goal of a clear documentation has not been reached ONLINE, the code is fairly well documented. Due to a mistake made by me in Sphinx I lost the online version.

Additional Goals
----------------

*  As my knowledge grew, I will enhance the project so that even without having to buy the expensive Lego(c) hubs, sensors and motors students can motorize their creations with very cheap controllers, sensors and motors, e.g., Raspberry Pi Pico and the common variants. Therefore, I am building easy to use frameworks using Micropython - however, this is currently under heavy development.


Sources of information:
=======================

1. `Lego Boost Roboter steuern mit Python unter Windows oder Linux <https://www.tec.reutlingen-university.de/fileadmin/user_upload/Fakultaet_TEC/LegoBoostPython_V4_final.pdf>`_), S. Mack, Vers. 4 22.3.20, Reutlingen University,
2. `Lego's(c) Wireless Protocol <https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#document-index>`_
3. `Reverse engineering the LEGO BOOST Hub <https://github.com/JorgePe/BOOSTreveng>`_, J. Pereira
4. Internet :-)
5. bruteforce: send possible commands and, see what happens::

.. copyright:
.. license:

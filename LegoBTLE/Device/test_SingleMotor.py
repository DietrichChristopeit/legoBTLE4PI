# coding=utf-8
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
import asyncio
from asyncio import Condition
from asyncio import Event
from random import uniform
from time import monotonic
from time import sleep


class Motor:
    
    def __init__(self, name):
        self._portfree_condition: Condition = Condition()
        self._portfree: Event = Event()
        self._portfree.set()
        self._command_end: Event = Event()
        self._name = name
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def portfree_condition(self) -> Condition:
        return self._portfree_condition
    
    @property
    def portfree(self) -> Event:
        return self._portfree
    
    async def turn(self, sec, t_id):
        
        async with self._portfree_condition:
            await self._portfree_condition.wait_for(lambda: self._portfree.is_set())
            self._portfree.clear()
            self._command_end.clear()
            print(f"TASK: {t_id}    {self._name}: ENTERED") #  /  sleeping for {sec}")
            
            # i = 0
            # while i < sec:
            #     print(f"TASK: {t_id}    {self._name} turning {i}")
            #     await asyncio.sleep(1)
            #     i += 1
            
            await self._command_end.wait()
            print(f"TASK: {t_id}    {self._name}: LEAVING")
            self._portfree.set()
            self._portfree_condition.notify_all()
            
        return
    
    async def free(self, sec):
        sleep(sec)
        self._command_end.set()
    
class SynchronizedMotor:
    
    def __init__(self, name: str, motor_a: Motor, motor_b: Motor):
        
        self._portfree_condition: Condition = Condition()
        self._portfree: Event = Event()
        self._portfree.set()
        self._motor_a: Motor = motor_a
        self._motor_b: Motor = motor_b
        self._name: str = name
        self._command_end: Event = Event()
        
        
    async def turn(self, sec, t_id):
        
        async with self._motor_a.portfree_condition, self._motor_b.portfree_condition, self._portfree_condition:
            
            await self._portfree_condition.wait_for(lambda: self._portfree.is_set())
            self._portfree.clear()
            await self._motor_a.portfree_condition.wait_for(lambda: self._motor_a.portfree.is_set())
            self._motor_a.portfree.clear()
            await self._motor_b.portfree_condition.wait_for(lambda: self._motor_b.portfree.is_set())
            self._motor_b.portfree.clear()
            self._command_end.clear()
            
            print(f"TASK: {t_id}    {self._name} ENTERED")
            # i = 0
            # while i < sec:
            #     print(f"TASK: {t_id}    {self._name} turning {i}")
            #     await asyncio.sleep(1)
            #     i += 1

            await self._command_end.wait()
            print(f"TASK: {t_id}    {self._name} LEAVING")
            self._motor_a.portfree.set()
            self._motor_b.portfree.set()
            self._portfree.set()
            self._motor_a.portfree_condition.notify_all()
            self._motor_b.portfree_condition.notify_all()
            self._portfree_condition.notify_all()
            
        return
    
    async def free(self, sec):
        sleep(sec)
        self._command_end.set()
        return
        
        
async def main():
    
    motor_a: Motor = Motor("MOTOR A")
    motor_b: Motor = Motor("MOTOR_B")
    motor_c: Motor = Motor("MOTOR_C")
    
    motor_a_b: SynchronizedMotor = SynchronizedMotor("MOTOR_A_B", motor_a, motor_b)
    motor_c_a: SynchronizedMotor = SynchronizedMotor("MOTOR_C_A", motor_c, motor_a)
    
    t0 = asyncio.create_task(motor_a.turn(3, "t0"))
    asyncio.create_task(motor_a.free(4))
    t7 = asyncio.create_task(motor_a.turn(3, "t7"))
    asyncio.create_task(motor_a.free(3))
    t1 = asyncio.create_task(motor_a_b.turn(10, "t1"))
    asyncio.create_task(motor_a_b.free(11.5))
    t6 = asyncio.create_task(motor_c_a.turn(8, "t6"))
    asyncio.create_task(motor_c_a.free(8.5))
    t3 = asyncio.create_task(motor_b.turn(4, "t3"))
    asyncio.create_task(motor_c_a.free(8.5))
    t4 = asyncio.create_task(motor_a.turn(6, "t4"))
    asyncio.create_task(motor_a.free(8))
    t5 = asyncio.create_task(motor_a_b.turn(5, "t5"))
    asyncio.create_task(motor_a_b.free(5.5))
    t2 = asyncio.create_task(motor_c.turn(20, "t2"))
    asyncio.create_task(motor_c.free(21.5))
    
    print(f"CURRENT STATE: {*asyncio.all_tasks(), }")
    
    # results = await asyncio.gather(t0, t7, t2)
    
    results = await asyncio.gather(t0, t1, t5, t3, t7, t4, t2, t6)
    print(f"CURRENT STATE NOW: {*asyncio.all_tasks(),}")
    
    print(f"RESULTS: {*results, }")
    
if __name__ == '__main__':
    
    start = monotonic()
    asyncio.run(main())
    print(f"\r\nOVERALL RUN TIME: {monotonic() - start}")
    
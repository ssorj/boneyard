#!/usr/bin/python3

import asyncio
from time import sleep

async def print_1_2_3():
    for x in (1, 2, 3):
        await asyncio.sleep(0.5)
        print(x)

async def print_x_y_z():
    for x in ("x", "y", "z"):
        await asyncio.sleep(1.0)
        print(x)

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.gather(print_1_2_3(), print_x_y_z()))
loop.close()  

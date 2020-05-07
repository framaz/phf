import re
import time

import requests
import json
import asyncio
import aioconsole
import threading

from Sites.dvach import Dvach

class _Getch:
    """Gets a single character from standard input.  Does not echo to the
screen."""
    def __init__(self):
        self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch



getch = _Getch()

async def get_action() -> str:
    kek = await command_queue.get()
    return kek

async def updates_generator(period, target):
    while True:
        await command_lock.acquire()
        print(target.get_updated_text())
        command_lock.release()
        await asyncio.sleep(period)

async def start_all():
    global event_loop, command_queue, command_lock
    command_queue = asyncio.Queue()
    command_lock = asyncio.Lock()
    event_loop = asyncio.get_running_loop()

    tasks = list()
    while True:
        string = await get_action()
        if string.find("exit") != -1:
            for task in tasks:
                task.cancel()
            break
        tasks.append(asyncio.create_task(updates_generator(5, Dvach(string))))
    await asyncio.sleep(10)
event_loop = None
command_queue = asyncio.Queue()
command_lock = asyncio.Lock()
def thread_input_output():
    while True:
        if event_loop is None:
            time.sleep(2)
            continue
        getch()
        asyncio.run_coroutine_threadsafe(command_lock.acquire(), event_loop)
        addr = input("Enter site name:\n")
        asyncio.run_coroutine_threadsafe(command_queue.put(addr), event_loop)
        command_lock.release()
     #   asyncio.run_coroutine_threadsafe(command_queue.put(addr), event_loop)


threading.Thread(target=thread_input_output).start()
asyncio.run(start_all())

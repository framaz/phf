import asyncio
import threading
import time

from aioconsole import ainput


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


class ConsoleInput:
    def __init__(self, queue, lock, loop):
        self.queue = queue
        self.lock = lock
        self.loop = loop

        def thread_input_output():
            while True:
                if self.loop is None:
                    time.sleep(2)
                    continue
                getch()
                asyncio.run_coroutine_threadsafe(self.lock.acquire(), self.loop)
                addr = input("Enter site name:\n")
                asyncio.run_coroutine_threadsafe(self.queue.put(addr), self.loop)
                self.lock.release()

        threading.Thread(target=thread_input_output).start()
class ConsoleDebugInput:
    def __init__(self, queue, lock, loop):
        self.queue = queue
        self.lock = lock
        self.loop = loop

        def thread_input_output():
            async def func():
                while True:
                    if self.loop is None:
                        time.sleep(2)
                        continue
                    addr = await ainput("Enter site name:\n")
                    asyncio.run_coroutine_threadsafe(self.queue.put(addr), self.loop)
            asyncio.run(func())

        threading.Thread(target=thread_input_output).start()
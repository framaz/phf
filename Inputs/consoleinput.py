import asyncio
import threading
import time

from aioconsole import ainput

from commandinput import AbstractCommandInput


class ConsoleDebugInput(AbstractCommandInput):
    async def get_command(self):
        return await ainput("Enter site name:\n")

    async def output_command_result(self, command_result):
        print(command_result)

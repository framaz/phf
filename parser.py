import asyncio

from Inputs.consoleinput import ConsoleInput
from Sites.dvach import Dvach


async def get_action(command_queue) -> str:
    kek = await command_queue.get()
    return kek

async def updates_generator(period, target, command_lock):
    while True:
        await command_lock.acquire()
        print(target.get_updated_text())
        print("Press any button to add new stuff")
        command_lock.release()
        await asyncio.sleep(period)

async def start_all():
    command_queue = asyncio.Queue()
    command_lock = asyncio.Lock()
    event_loop = asyncio.get_running_loop()

    input_class = ConsoleInput(command_queue, command_lock, event_loop)
    tasks = list()
    while True:
        string = await get_action(command_queue)
        if string.find("exit") != -1:
            for task in tasks:
                task.cancel()
            break
        tasks.append(asyncio.create_task(updates_generator(5, Dvach(string), command_lock)))
    await asyncio.sleep(10)


asyncio.run(start_all())

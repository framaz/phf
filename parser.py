import asyncio
from Inputs.consoleinput import ConsoleInput, ConsoleDebugInput
from Sites.dvach import Dvach
from hooks.dvachhooks import DvachShowHook


async def get_action(command_queue) -> str:
    kek = await command_queue.get()
    return kek


async def start_all():
    command_queue = asyncio.Queue()
    command_lock = asyncio.Lock()
    event_loop = asyncio.get_running_loop()

    input_class = ConsoleDebugInput(command_queue, command_lock, event_loop)
    tasks = list()
    while True:
        string = await get_action(command_queue)
        if not isinstance(string, str):
            continue
        if string.find("exit") != -1:
            for task in tasks:
                task.cancel()
            break
        hook = DvachShowHook(command_lock)
        dvach = Dvach(string)
        dvach.add_hook(hook)
        tasks.append(asyncio.create_task(dvach.cycle()))
    await asyncio.sleep(10)


asyncio.run(start_all())

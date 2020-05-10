import asyncio


class AbstractCommandInput:
    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls)
        obj._asyncio_command_queue = None
        obj._task = None
        return obj

    def __init__(self, *args, **kwargs):
        self._asyncio_command_queue = None
        self._task = None

    async def get_command(self):
        raise NotImplementedError(f"Get command call of {self.__class__}")

    async def _cycle(self):
        while True:
            new_command = await self.get_command()
            self._asyncio_command_queue.put_nowait(new_command)

    def start(self, queue):
        self._asyncio_command_queue = queue
        self._task = asyncio.create_task(self._cycle())

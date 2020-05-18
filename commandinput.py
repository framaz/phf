import asyncio


class AbstractCommandInput:
    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls)
        obj._asyncio_command_queue = None
        obj._asyncio_result_queue = None
        obj._command_input_task = None
        return obj

    def __init__(self, *args, **kwargs):
        self._asyncio_command_queue = None
        self._asyncio_result_queue = None
        self._command_input_task = None

    async def get_command(self):
        raise NotImplementedError(f"Get command call of {self.__class__}")

    async def output_command_result(self, command_result):
        pass

    async def set_command_result(self, result):
        self._asyncio_result_queue.put_nowait(result)

    async def _cycle(self):
        while True:
            new_command = await self.get_command()
            self._asyncio_command_queue.put_nowait((new_command, self))
            result = await self._asyncio_result_queue.get()
            await self.output_command_result(result)

    def start(self, command_queue, result_queue):
        self._asyncio_command_queue = command_queue
        self._asyncio_result_queue = result_queue
        self._command_input_task = asyncio.create_task(self._cycle())

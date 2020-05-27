import asyncio

import typing


class AbstractCommandInput:
    """A class for command inputs.

    This class provides means to input commands to AsyncParser.
    It is a bit similar to ConsistentDataProvider, but no hooks can be attached to it.

    Attributes:
        _asyncio_command_queue: asyncio.Queue to send command to AsyncParser.
        _asyncio_result_queue: asyncio.Queue receive result from AsyncParser.
        _command_input_task: asyncio.Task for input's running.
    """

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

    # TODO command class
    async def get_command(self) -> typing.Union[dict]:
        """Retrieve command from source.

        Returns:
            A command formed into specially formatted dict or (not implemented now) a Command object.
        """
        raise NotImplementedError(f"Get command call of {self.__class__}")

    # TODO command execution result class
    async def output_command_result(self, command_result) -> None:
        """Do smth after result from executing a command is received."""
        pass

    async def set_command_result(self, result) -> None:
        """Send command result to the source.

        Args:
            result: result of command execution.
        """
        self._asyncio_result_queue.put_nowait(result)

    async def _cycle(self) -> None:
        """Main CommandInput work in cycle."""
        while True:
            new_command = await self.get_command()
            self._asyncio_command_queue.put_nowait((new_command, self))
            result = await self._asyncio_result_queue.get()
            await self.output_command_result(result)

    def start(self, command_queue: asyncio.Queue, result_queue: asyncio.Queue) -> None:
        """Start current command input source when in event loop.

        Args:
            command_queue: queue to send command to AsyncParser.
            result_queue: queue to receive command execution result from AsyncParser.
        """
        self._asyncio_command_queue = command_queue
        self._asyncio_result_queue = result_queue
        self._command_input_task = asyncio.create_task(self._cycle())

import asyncio
import typing

from aioconsole import ainput


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


class ConsoleDebugInput(AbstractCommandInput):
    """Class for getting inputs from console command line.

    Will be overwritten to contain Command class.
    """

    async def get_command(self):
        input_command = await ainput("Enter site name:\n")
        input_array = input_command.split(" ")
        res = dict()

        # hello yandereDev
        if input_array[0] == "new_hook":
            res["type"] = "new_hook"
            res["target_provider_num"] = int(input_array[2])
            res["target_class"] = input_array[1]
            pos_args, keyword_args = self.get_arguments(input_array[3:])
            res["positionals"] = pos_args
            res["keywords"] = keyword_args

        elif input_array[0] == "new_provider":
            res["type"] = "new_provider"
            res["target_class"] = input_array[1]
            pos_args, keyword_args = self.get_arguments(input_array[2:])
            res["positionals"] = pos_args
            res["keywords"] = keyword_args

        elif input_array[0] == "list_providers":
            res["type"] = "list_providers"

        elif input_array[0] == "list_hooks":
            res["type"] = "list_hooks"
            res['target_provider_num'] = int(input_array[1])

        return res

    def get_arguments(self, input_array):
        positional_arguments = []
        keyword_arguments = {}
        for argument in input_array:
            eq_position = argument.find("=")
            if eq_position != -1:
                keyword = argument[0:eq_position]
                value = argument[eq_position + 1:]
                keyword_arguments[keyword] = value
            else:
                positional_arguments.append(argument)
        return positional_arguments, keyword_arguments

    async def output_command_result(self, command_result):
        print(str(command_result))

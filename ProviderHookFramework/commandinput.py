from __future__ import annotations

import asyncio
import datetime
import typing
from typing import TYPE_CHECKING

from aioconsole import ainput

if TYPE_CHECKING:
    from asyncparser import AsyncParser


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
            A command formed into specially formatted dict or
            (not implemented now) a Command object.
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

    def start(self,
              command_queue: asyncio.Queue,
              result_queue: asyncio.Queue) -> None:
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


class Command:
    """A class for commands.

    To implement a command one should override it's _apply method.
    Apply method takes a single argument - parser, somehow modifies it
    and returns result of executing the operation.
    Execute_command should be used for running the command on AsyncParser.

    Attributes:
        _cur_time: datetime, time when the command was created.
        _source: AbstractCommandInput, at which the command has been created.
        _executed: bool flag whether the command was executed.
    """

    def __init__(self, source: AbstractCommandInput = None):
        """Create a Command.

        Args:
            source: what created the command.
        """
        self._cur_time = datetime.datetime.now()
        self._source = source
        self._executed = False

    def execute_command(self, parser: AsyncParser):
        """Execute a command."""
        self._apply(parser)
        self._executed = True

    def _apply(self, parser: AsyncParser):
        """What exactly the command does.

        Override this when you create new command.

        Args:
            parser: on which AsyncParser to execute the command.
        """
        raise NotImplementedError(f"Call of unimplemented "
                                  f"{self.__class__.__name__}.apply(...)")


class ListProvidersCommand(Command):
    """Command to retrieve all providers list.

    Attributes:
        _data: List[AbstractContentProvder], copy of providers list at the time
            of command execution.
    """

    def __init__(self, source: AbstractCommandInput = None):
        """Create the command.

        Args:
            source: what created the command.
        """
        super().__init__(source)
        self._data = None

    def _apply(self, parser: AsyncParser):
        """Get all providers of parser.

        Args:
            parser: on which AsyncParser to execute the command.
        """
        self._data = parser.get_providers()
        return self._data


class ListHooksCommand(Command):
    """Command to retrieve all hooks list of a provider by it's number.

    Attributes:
        _provider: AbstractContentProvider, whose hooks to get.
        _hooks: List[AbstractHook], list of hooks.
        _target_provider_num: int, targeted provider's number in parser's
            providers list.
    """

    def __init__(self,
                 target_provider_num: int,
                 source: AbstractCommandInput = None):
        """Create the command.

       Args:
           target_provider_num: targeted provider's number in parser's
                providers list.
           source: what created the command.
       """
        super().__init__(source)

        self._target_provider_num = target_provider_num
        self._provider = None
        self._hooks = None

    def _apply(self, parser: AsyncParser):
        """Get providers of concrete parser.

        Args:
            parser: on which AsyncParser to execute the command.
        """
        self._provider = parser.get_providers()[self._target_provider_num]
        self._hooks = self._provider.get_hooks()[:]
        return self._hooks


class NewProviderCommand(Command):
    """Create a new provider, add it to parser and start it.

    Attributes:
        _class_name: str, name/alias of provider class to create.
        _args: list, positional arguments for constructor.
        _kwargs: dict, keyword arguments for constructor.
        _provider: AbstractContentProvider, resulting provider.
    """

    def __init__(self,
                 class_name: str,
                 args: list = None,
                 kwargs: dict = None,
                 source: AbstractCommandInput = None):
        """Create the command.

        Args:
            class_name: name/alias of provider class to create.
            args: positional arguments for constructor.
            kwargs: keyword arguments for constructor.
            source: what created the command.
        """
        super().__init__(source)

        self._class_name = class_name
        self._args = args
        self._kwargs = kwargs
        self._provider = None

    def _apply(self, parser: AsyncParser):
        """Create provider and add it to parser.

        Args:
            parser: on which AsyncParser to execute the command.
        """
        self._provider = parser.create_provider(self._class_name,
                                                self._args,
                                                self._kwargs)
        parser.add_content_provider(self._provider)
        return "SUCCESS"


class NewHookCommand(Command):
    """Create a new hook, add it to provider and start it.

    Attributes:
        _class_name: str, name/alias of hook class to create.
        _provider_num: int, targeted provider's number in parser's
            providers list.
        _args: list, positional arguments for constructor.
        _kwargs: dict, keyword arguments for constructor.
        _provider: AbstractContentProvider, to which hook is added.
        _hook: AbstractHook, the created hook.
        """

    def __init__(self,
                 class_name: str,
                 provider_num: int,
                 args: list = None,
                 kwargs: dict = None,
                 source: AbstractCommandInput = None):
        """Create the command.

        Args:
            class_name: name/alias of hook class to create.
            provider_num: int, targeted provider's number in parser's
                providers list.
            args: list, positional arguments for constructor.
            kwargs: dict, keyword arguments for constructor.
            source: what created the command.
        """
        super().__init__(source)

        self._class_name = class_name
        self._provider_num = provider_num
        self._args = args
        self._kwargs = kwargs
        self._provider = None
        self._hook = None

    def _apply(self, parser: AsyncParser):
        """Create hook, add it to provider and start it.

        Args:
            parser: on which AsyncParser to execute the command.
        """
        self._provider = parser.get_providers()[self._provider_num]
        self._hook = parser.create_hook(self._class_name,
                                        self._args,
                                        self._kwargs)
        return "SUCCESS"

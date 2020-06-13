from __future__ import annotations

import asyncio
import datetime
import typing
from abc import ABC
from typing import TYPE_CHECKING

import aioconsole

if TYPE_CHECKING:
    from phfsystem import PHFSystem

T = typing.TypeVar('T')


class AbstractCommandInput:
    """A class for command inputs.

    This class provides means to input commands to PHFSystem.
    It is a bit similar to ConsistentDataProvider, but no hooks can be attached to it.

    Attributes:
        _asyncio_command_queue: asyncio.Queue to send command to PHFSystem.
        _asyncio_result_queue: asyncio.Queue receive result from PHFSystem.
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
    async def retrieve_command_from_source(self) -> T:
        """Retrieve data from source.

        The data is then passed to form_command, which translates the data to command.

        Returns:
            A command formed into Command object.
        """
        raise NotImplementedError(f"retrieve_command_from_source call of {self.__class__}")

    def form_command(self, data: T) -> Command:
        raise NotImplementedError(f"form_command call of {self.__class__}")

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
            data = await self.retrieve_command_from_source()
            new_command = self.form_command(data)
            self._asyncio_command_queue.put_nowait((new_command, self))
            result = await self._asyncio_result_queue.get()
            await self.output_command_result(result)

    def start(self,
              command_queue: asyncio.Queue,
              result_queue: asyncio.Queue) -> None:
        """Start current command input source when in event loop.

        Args:
            command_queue: queue to send command to PHFSystem.
            result_queue: queue to receive command execution result from PHFSystem.
        """
        self._asyncio_command_queue = command_queue
        self._asyncio_result_queue = result_queue
        self._command_input_task = asyncio.create_task(self._cycle())


class ConsoleDebugInput(AbstractCommandInput, ABC):
    """Class for getting inputs from console command line.

    Notice that there's gonna be problems with writing if some output is printed on
    the command line.

    Attributes:
        class._input:
    """
    _input = "Enter command data:\n"

    async def retrieve_command_from_source(self):
        """Get command data from command line."""
        input_command = await aioconsole.ainput(self._input)
        return input_command

    async def output_command_result(self, command_result):
        """Print the command result."""
        print(str(command_result))


class Command:
    """A class for commands.

    To implement a command one should override it's _apply method.
    Apply method takes a single argument - PHFsystem, somehow modifies it
    and returns result of executing the operation.
    Execute_command should be used for running the command on PHFSystem.

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

    def execute_command(self, phfsys: PHFSystem):
        """Execute a command."""
        result = self._apply(phfsys)
        self._executed = True
        return result

    def _apply(self, phfsys: PHFSystem):
        """What exactly the command does.

        Override this when you create new command.

        Args:
            phfsys: on which PHFSystem to execute the command.
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

    def _apply(self, phfsys: PHFSystem):
        """Get all providers of phfsys.

        Args:
            phfsys: on which PHFSystem to execute the command.
        """
        self._data = phfsys.get_providers()
        return self._data


class ListHooksCommand(Command):
    """Command to retrieve all hooks list of a provider by it's number.

    Attributes:
        _provider: AbstractContentProvider, whose hooks to get.
        _hooks: List[AbstractHook], list of hooks.
        _target_provider_num: int, targeted provider's number in phfsys's
            providers list.
    """

    def __init__(self,
                 target_provider_num: int,
                 source: AbstractCommandInput = None):
        """Create the command.

       Args:
           target_provider_num: targeted provider's number in phfsys's
                providers list.
           source: what created the command.
       """
        super().__init__(source)

        self._target_provider_num = target_provider_num
        self._provider = None
        self._hooks = None

    def _apply(self, phfsys: PHFSystem):
        """Get providers of concrete phfsys.

        Args:
            phfsys: on which PHFSystem to execute the command.
        """
        self._provider = phfsys.get_providers()[self._target_provider_num]
        self._hooks = self._provider.get_hooks()[:]
        return self._hooks


class NewProviderCommand(Command):
    """Create a new provider, add it to phfsys and start it.

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

    def _apply(self, phfsys: PHFSystem):
        """Create provider and add it to phfsys.

        Args:
            phfsys: on which PHFSystem to execute the command.
        """
        self._provider = phfsys.create_provider(self._class_name,
                                                self._args,
                                                self._kwargs)
        phfsys.add_provider(self._provider)
        return self._provider


class NewHookCommand(Command):
    """Create a new hook, add it to provider and start it.

    Attributes:
        _class_name: str, name/alias of hook class to create.
        _provider_num: int, targeted provider's number in phfsys's
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
            provider_num: int, targeted provider's number in phfsys's
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

    def _apply(self, phfsys: PHFSystem):
        """Create hook, add it to provider and start it.

        Args:
            phfsys: on which PHFSystem to execute the command.
        """
        self._provider = phfsys.get_providers()[self._provider_num]
        self._hook = phfsys.create_hook(self._class_name,
                                        self._args,
                                        self._kwargs)
        self._provider.add_hook(self._hook)
        return self._hook


def get_arguments(input_array):
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

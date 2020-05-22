from __future__ import annotations

import asyncio
import copy
import typing


class AbstractHook:
    """Base hook class for all other hooks.

    To make a hook, user should inherit this class and override async method hook_action(self, data).

    It can be created manually before the start of AsyncParser work and connected to a provider
    or it can be created dynamically with help AbstractCommandInput's inhabitants.
    To make dynamical creation of hooks, they can have aliases set in _alias as a list of string.

    Class attributes:
        _alias: List of strings, alases for the class.

    Attributes:
        _asyncio_queue: asyncio.Queue obj to transport data from provider to hook.
        _callback_queue: asyncio.Queue obj to transport data from hook to provider.
        _provider: provider.AbstractContentProvider obj, hooks target.

    Example:
        Creating a simple MyHook class with some aliases that prints "MyHook!" every
        time provider sends it data and returns "MyHook!".

        class MyHook:
            _alias = ["my_hook", "MYHOOK", "MH"]

            async def hook_action(self, data):
                print("MyHook!")
                return "MyHook!
    """
    _alias = []

    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls)
        obj._asyncio_queue = None
        obj._callback_queue = None
        obj._provider = None
        return obj

    def __init__(self, *args, **kwargs):
        pass

    def get_straight_queue(self) -> asyncio.Queue:
        """Create if not created and return provider -> hook queue.

        Returns:
            Queue to transfer data from provider to hook's action.
        """
        if self._asyncio_queue is None:
            self._asyncio_queue = asyncio.Queue()
        return self._asyncio_queue

    def get_callback_queue(self) -> asyncio.Queue:
        """Create if not created and return hook -> provider queue.

        Returns:
             queue to transfer data returned by hook's action to provider
        """
        if self._callback_queue is None:
            self._callback_queue = asyncio.Queue()
        return self._callback_queue

    async def cycle_call(self) -> None:
        """Make hook start doing its work.

        In a cycle hook gets data from provider, executes hook_action and sends it's result
        to provider.
        """
        while True:
            target = await self.get_straight_queue().get()
            result = await self.hook_action(target)
            self.get_callback_queue().put_nowait(result)
        pass

    async def hook_action(self, data: typing.Any) -> typing.Any:
        """Do hook action on the data provided by provider.

        User has to override it in subclasses.
        This method specifies what exactly the hook does. It may return some resulting data
        which will be sent to provider's result_callback(self, results) method as an element
        of results list.

        Args:
            data: data received from provider.

        Returns:
            Any data you want to be sent to provider.

        """
        raise NotImplementedError(f"hook_action of {self.__class__} not overridden")

    @classmethod
    def get_aliases(cls) -> typing.List[str]:
        """Returns a copy of aliases list.

        Returns:
            list of class's aliases.
        """
        return copy.deepcopy(cls._alias)


class BasicPrintHook(AbstractHook):
    """Simple hook that just prints and returns received data."""

    async def hook_action(self, output: typing.Any) -> typing.Any:
        print(output)
        return output

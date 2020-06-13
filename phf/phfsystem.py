"""Main module of the framework.

Contains PHFSystem class, which is environment of the framework.
"""
from __future__ import annotations

import asyncio
import typing
from typing import TYPE_CHECKING

from commandinput import AbstractCommandInput, Command
from factory import HookAndProviderFactory
from provider import AbstractContentProvider

if TYPE_CHECKING:
    from abstracthook import AbstractHook


class PHFSystem:
    """PHFSystem is environment and main facade of framework.

    Attributes:
        _providers: list of all providers.
        _running_state: state, shows if framework is running now.
        _input_sources: list of all input sources.
        _providers_and_hooks_factory: factory for hook and provider creation.
        _asyncio_loop: eventloop, in which the system is running.
        _command_queue: asyncio.Queue, to which the commands go.
    """

    def __init__(self):
        self._providers = []
        self._running_state = False
        self._input_sources = []
        self._providers_and_hooks_factory = HookAndProviderFactory()
        self._asyncio_loop = None
        self._command_queue = None

    def get_providers(self) -> typing.List[AbstractContentProvider]:
        return self._providers[:]

    def import_provider_sources(self, *args) -> None:
        """Read providers from paths

        Args:
            *args: str paths to files/directories/packages.
        """
        self._providers_and_hooks_factory.import_provider_classes(*args)

    def import_hook_sources(self, *args) -> None:
        """Read hooks from paths

        Args:
            *args: str paths to files/directories/packages.
        """
        self._providers_and_hooks_factory.import_hook_classes(*args)

    def create_provider(self,
                        class_name: str,
                        args: list,
                        kwargs: dict) -> AbstractContentProvider:
        """Create a provider.

        Just a wrapper around _providers_and_hooks_factory.create_provider
        Args:
            class_name: name/alias of provider class to create
            args: positional arguments for constructor
            kwargs: keyword arguments for constructor

        Returns:
            Created provider.
        """
        return self._providers_and_hooks_factory.create_provider(
            class_name,
            args,
            kwargs
        )

    def create_hook(self,
                    class_name: str,
                    args: list,
                    kwargs: dict) -> AbstractHook:
        """Create a hook.

        Just a wrapper around _providers_and_hooks_factory.create_hook
        Args:
            class_name: name/alias of hook class to create
            args: positional arguments for constructor
            kwargs: keyword arguments for constructor

        Returns:
            Created hook.
        """
        return self._providers_and_hooks_factory.create_hook(
            class_name,
            args,
            kwargs
        )

    def add_provider(self,
                     content_provider: AbstractContentProvider) -> None:
        """Add a content provider and run it if PHFSystem is running.

        Args:
            content_provider: provider to add.
        """
        self._providers.append(content_provider)
        if self._running_state:
            self._run_content_provider(content_provider)

    def add_input_source(self, input_source: AbstractCommandInput):
        """Add an input source.

        Note that input sources have to be created before starting PHFSystem.

        Args:
            input_source: input source to add.
        """
        self._input_sources.append(input_source)

    def _run_content_provider(self,
                              content_provider: AbstractContentProvider) -> None:
        """Run content provider's work coroutine."""
        content_provider.start()

    async def _get_command(self, command_queue):
        """Get command"""
        kek, target = await command_queue.get()
        return kek, target

    async def _start_main_coroutine(self) -> None:
        """Main framework's work coroutine.

        It starts all providers and hooks, then it executes commands from
        command sources.
        """
        self._running_state = True
        self._asyncio_loop = asyncio.get_running_loop()
        # TODO change it so each inputsource has it's own queues.
        self._command_queue = asyncio.Queue()
        result_queue = asyncio.Queue()

        for input_source in self._input_sources:
            input_source.start(self._command_queue, result_queue)

        for provider in self._providers:
            self._run_content_provider(provider)

        while True:
            command, evoker = await self._get_command(self._command_queue)
            output = await self._execute_command(command)
            await evoker.set_command_result(output)

    # TODO overrite to get Command as an argument
    async def _execute_command(self, command: Command):
        res = command.execute_command(self)
        return res

    def start(self):
        """Start work of the framework.

        It is blocking, so if you want to keep code outside of framework running,
        you should start it in different thread.
        """
        asyncio.run(self._start_main_coroutine())

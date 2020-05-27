"""Main module of the framework.

Contains AsyncParser class, which is environment of the framework.
"""
from __future__ import annotations

import asyncio

from commandinput import AbstractCommandInput
from factory import HookAndProviderFactory
from provider import AbstractContentProvider


class AsyncParser:
    """AsyncParser is environment and main facade of framework.

    Attributes:
        _providers: list of all providers.
        _running_state: state, shows if framework is running now.
        _input_sources: list of all input sources.
        _providers_and_hooks_factory: factory for hook and provider creation.
    """

    def __init__(self):
        self._providers = []
        self._running_state = False
        self._input_sources = []
        self._providers_and_hooks_factory = HookAndProviderFactory()

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

    def add_content_provider(self, content_provider: AbstractContentProvider) -> None:
        """Add a content provider and run it if AsyncParser is running.

        Args:
            content_provider: provider to add.
        """
        self._providers.append(content_provider)
        if self._running_state:
            self._run_content_provider(content_provider)

    def add_input_source(self, input_source: AbstractCommandInput):
        """Add an input source.

        Note that input sources have to be created before starting AsyncParser.

        Args:
            input_source: input source to add.
        """
        self._input_sources.append(input_source)

    def _run_content_provider(self, content_provider: AbstractContentProvider) -> None:
        """Run content provider's work coroutine."""
        # TODO provider run itself, not from outside
        content_provider._asyncio_task = asyncio.create_task(content_provider.cycle())

    # TODO add convertion to command from dict
    async def _get_command(self, command_queue):
        """Get command"""
        kek, target = await command_queue.get()
        return kek, target

    async def _start_main_coroutine(self) -> None:
        """Main framework's work coroutine.

        It starts all providers and hooks, then it executes commands from command sources.
        """
        self._running_state = True
        # TODO change it so each inputsource has it's own queues.
        command_queue = asyncio.Queue()
        result_queue = asyncio.Queue()

        for input_source in self._input_sources:
            input_source.start(command_queue, result_queue)

        for provider in self._providers:
            self._run_content_provider(provider)

        while True:
            command_dict, evoker = await self._get_command(command_queue)
            output = await self._execute_command(command_dict)
            await evoker.set_command_result(output)

    # TODO overrite to get Command as an argument
    async def _execute_command(self, command_dict):
        output = dict()
        output['type'] = command_dict['type']
        output['input_command'] = command_dict
        if command_dict['type'] == "new_provider":
            provider = self._providers_and_hooks_factory.create_provider(command_dict['target_class'],
                                                                         (command_dict['positionals']),
                                                                         (command_dict['keywords']))
            self.add_content_provider(provider)
            output['status'] = "SUCCESS"
            output['message'] = f"Successfully created {str(provider)}"

        elif command_dict['type'] == "new_hook":
            target = command_dict['target_provider_num']

            hook = self._providers_and_hooks_factory.create_hook(command_dict['target_class'],
                                                                 (command_dict['positionals']),
                                                                 (command_dict['keywords']))
            self._providers[target].add_hook(hook)
            output['status'] = "SUCCESS"
            output['message'] = f"Successfully created {str(hook)} and linked" + \
                                f"to {self._providers[target]}"

        elif command_dict['type'] == "list_providers":
            output['status'] = "SUCCESS"
            msgs = []
            for provider in self._providers:
                msgs.append(str(provider))
            output['providers'] = msgs

        elif command_dict['type'] == 'list_hooks':
            output['status'] = "SUCCESS"
            provider = self._providers[command_dict['target_provider_num']]
            output['provider'] = str(provider)
            hooks = []
            for hook in provider.get_hooks():
                hooks.append(str(hook))
            output['hooks'] = hooks
        return output

    def start(self):
        """Start work of the framework.

        It is blocking, so if you want to keep code outside of framework running, you should
        start it in different thread.
        """
        asyncio.run(self._start_main_coroutine())

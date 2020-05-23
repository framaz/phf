from __future__ import annotations

import asyncio

from factory import HookAndProviderFactory
from provider import AbstractContentProvider


class AsyncParser:
    def __init__(self):
        self._providers = []
        self._running_state = False
        self._input_sources = []
        self._providers_and_hooks_factory = HookAndProviderFactory()

    def import_provider_sources(self, *args):
        self._providers_and_hooks_factory.import_provider_classes(*args)

    def import_hook_sources(self, *args):
        self._providers_and_hooks_factory.import_hook_classes(*args)

    def add_content_provider(self, content_provider: AbstractContentProvider):
        self._providers.append(content_provider)
        if self._running_state:
            self._run_content_provider(content_provider)

    def add_input_source(self, input_source):
        self._input_sources.append(input_source)

    def _run_content_provider(self, content_provider):
        content_provider._asyncio_task = asyncio.create_task(content_provider.cycle())

    async def _get_action(self, command_queue):
        kek, target = await command_queue.get()
        return kek, target

    async def _start_main_coroutine(self):
        self._running_state = True

        command_queue = asyncio.Queue()
        result_queue = asyncio.Queue()

        for input_source in self._input_sources:
            input_source.start(command_queue, result_queue)

        for provider in self._providers:
            self._run_content_provider(provider)

        while True:
            command_dict, evoker = await self._get_action(command_queue)
            output = await self._execute_command(command_dict)
            await evoker.set_command_result(output)

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
            for hook in provider._get_hooks():
                hooks.append(str(hook))
            output['hooks'] = hooks
        return output

    def start(self):
        asyncio.run(self._start_main_coroutine())

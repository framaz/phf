from __future__ import annotations
import asyncio

from Inputs.consoleinput import ConsoleDebugInput
from Sites.dvach import Dvach
from hooks.dvachhooks import DvachFileDownloader
from provider import AbstractContentProvider
from factory import HookAndProviderFactory

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

    async def _get_action(self, command_queue) -> str:
        kek = await command_queue.get()
        return kek

    async def _start_main_coroutine(self):
        self._running_state = True

        command_queue = asyncio.Queue()
        command_lock = asyncio.Lock()
        event_loop = asyncio.get_running_loop()

        for input_source in self._input_sources:
            input_source.start(command_queue)

        for provider in self._providers:
            self._run_content_provider(provider)

        while True:
            string = await self._get_action(command_queue)
            strings = string.split(" ")
            if string.find("exit") != -1:
                break

            if strings[0] == "p":
                strings = strings[1:]
                provider = self._providers_and_hooks_factory.create_providers(*strings)
                self.add_content_provider(provider)

            elif strings[0] == "h":
                target = int(strings[1])
                strings = strings[2:]
                hook = self._providers_and_hooks_factory.create_hooks(*strings)
                self._providers[target].add_hook(hook)

    def start(self):
        asyncio.run(self._start_main_coroutine())

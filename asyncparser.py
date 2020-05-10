from __future__ import annotations
import asyncio

from Inputs.consoleinput import ConsoleDebugInput
from Sites.dvach import Dvach
from hooks.dvachhooks import DvachFileDownloader
from provider import AbstractContentProvider


class AsyncParser:
    def __init__(self):
        self._providers = []
        self._running_state = False
        self._input_sources = []

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
            kek = Dvach(string)
            downloader = DvachFileDownloader()
            kek.add_hook(downloader)
            self.add_content_provider(kek)

            if not isinstance(string, str):
                continue
            if string.find("exit") != -1:
                break

    def start(self):
        asyncio.run(self._start_main_coroutine())

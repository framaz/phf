from __future__ import annotations
import asyncio

from Inputs.consoleinput import ConsoleDebugInput
from Sites.dvach import Dvach
from hooks.dvachhooks import DvachFileDownloader
from provider import AbstractContentProvider


class AsyncParser:
    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls)
        obj._providers = []
        obj._running_state = False
        return obj

    def __init__(self):
        self._providers = []
        self._running_state = False

    def add_content_provider(self, content_provider: AbstractContentProvider):
        self._providers.append(content_provider)
        if self._running_state:
            self._run_content_provider(content_provider)

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

        dv = Dvach("https://2ch.hk/po/res/37650692.html")
        hook = DvachFileDownloader()
        dv.add_hook(hook)
        self.add_content_provider(dv)

        for provider in self._providers:
            self._run_content_provider(provider)

        input_class = ConsoleDebugInput(command_queue, command_lock, event_loop)
        while True:
            string = await self._get_action(command_queue)
            if not isinstance(string, str):
                continue
            if string.find("exit") != -1:
                break

    def start(self):
        asyncio.run(self._start_main_coroutine())

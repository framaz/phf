import asyncio
import os

import pytest

from factory_obj.file1 import Provider1, Hook1
from phf import commandinput
from phf.phfsystem import PHFSystem


class TestPHFSystem:
    @pytest.mark.asyncio
    async def test_get_add_providers(self, started_phfsys, periodic_provider_factory):
        started_phfsys, _ = started_phfsys

        assert started_phfsys.get_providers() == []

        provider = periodic_provider_factory.get_provider()
        started_phfsys.add_provider(provider)
        await asyncio.sleep(0.01)

        assert started_phfsys.get_providers() == [provider]
        assert provider._asyncio_running

    def test_import_provider_sources(self, started_phfsys):
        started_phfsys, _ = started_phfsys

        started_phfsys.import_provider_sources(
            os.path.join("factory_obj", "hooks_package", "hook3.py")
        )
        assert "Provider3" in started_phfsys._providers_and_hooks_factory. \
            _provider_analyser.get_providers()

    def test_import_hook_classes(self, started_phfsys):
        started_phfsys, _ = started_phfsys

        started_phfsys.import_hook_sources(
            os.path.join("factory_obj", "hooks_package", "hook3.py")
        )

        assert "Hook3" in started_phfsys._providers_and_hooks_factory. \
            _hook_analyser.get_hooks()

    def test_create_provider(self, started_phfsys):
        started_phfsys, _ = started_phfsys

        provider = started_phfsys.create_provider("Provider1",
                                                  args=[2],
                                                  kwargs={"b": 2})

        assert provider.a == 2
        assert provider.b == 2
        assert isinstance(provider, Provider1)

    def test_create_hook(self, started_phfsys):
        started_phfsys, _ = started_phfsys

        hook = started_phfsys.create_hook("Hook1",
                                          args=[2],
                                          kwargs={"b": 2})

        assert hook.a == 2
        assert hook.b == 2
        assert isinstance(hook, Hook1)

    def test_add_provider_nonstarted(self, periodic_provider_factory, monkeypatch):
        phfsys = PHFSystem()

        def _fake_run(content_provider):
            raise RuntimeError("_run_content_provider isn't supposed to be called")

        provider = periodic_provider_factory.get_provider()

        monkeypatch.setattr(phfsys, "_run_content_provider", _fake_run)

        phfsys.add_provider(provider)

    @pytest.mark.asyncio
    async def test_add_provider_nonstarted(self, started_phfsys, periodic_provider_factory):
        started_phfsys, _ = started_phfsys

        provider = periodic_provider_factory.get_provider()

        started_phfsys.add_provider(provider)
        await asyncio.sleep(0.01)

        assert provider._asyncio_running

    @pytest.mark.asyncio
    async def test_command_execute(self, started_phfsys):
        started_phfsys, controller = started_phfsys

        command = commandinput.NewProviderCommand("Provider1", [2, 2])
        controller.send_command_to_phfsys(command)
        await asyncio.sleep(0.01)

        provider = controller.logs[0]
        assert provider.a == 2
        assert provider._asyncio_running

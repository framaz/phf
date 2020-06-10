import asyncio

import pytest

from phf import commandinput


class TestCommands:
    """Tests for different command classes."""

    def test_abstract_command_execute(self, fake_started_async_phfsys):
        command = commandinput.Command()
        with pytest.raises(NotImplementedError):
            command.execute_command(fake_started_async_phfsys)

    def test_Command_execute_state(self, fake_started_async_phfsys, monkeypatch):
        command = commandinput.Command()
        monkeypatch.setattr(command, "_apply", lambda x: "a")
        res = command.execute_command(fake_started_async_phfsys)
        assert res == "a"
        assert command._executed

    @pytest.mark.asyncio
    async def test_ListProvidersCommand(self,
                                        fake_started_async_phfsys,
                                        periodic_provider_factory):
        command1 = commandinput.ListProvidersCommand()

        res1 = command1.execute_command(fake_started_async_phfsys)
        assert command1._data == []
        assert res1 == []

        command2 = commandinput.ListProvidersCommand()
        provider1 = periodic_provider_factory.get_provider()
        provider2 = periodic_provider_factory.get_provider()
        fake_started_async_phfsys.add_content_provider(provider1)
        fake_started_async_phfsys.add_content_provider(provider2)

        res2 = command2.execute_command(fake_started_async_phfsys)
        assert res2 == [provider1, provider2]
        assert command2._data == [provider1, provider2]
        assert res1 == []

    @pytest.mark.asyncio
    async def test_ListHooksCommand(self,
                                    fake_started_async_phfsys,
                                    periodic_provider_factory,
                                    hook_factory):
        for i in range(3):
            provider = periodic_provider_factory.get_provider()
            fake_started_async_phfsys.add_content_provider(provider)

        hook1 = hook_factory.get_hook()
        fake_started_async_phfsys.get_providers()[1].add_hook(hook1)

        command1 = commandinput.ListHooksCommand(0)
        res1 = command1.execute_command(fake_started_async_phfsys)
        assert res1 == []

        command2 = commandinput.ListHooksCommand(1)
        res2 = command2.execute_command(fake_started_async_phfsys)
        assert res2 == [hook1]

        hook2 = hook_factory.get_hook()
        fake_started_async_phfsys.get_providers()[1].add_hook(hook2)

        command3 = commandinput.ListHooksCommand(1)
        res3 = command3.execute_command(fake_started_async_phfsys)
        assert res3 == [hook1, hook2]

    @pytest.mark.asyncio
    async def test_NewProviderCommand(self, fake_started_async_phfsys):
        command = commandinput.NewProviderCommand("Provider1",
                                                  args=[0],
                                                  kwargs={"b": 1})
        assert command._class_name == "Provider1"
        assert command._args == [0]
        assert command._kwargs == {"b": 1}

        assert fake_started_async_phfsys.get_providers() == []

        res = command.execute_command(fake_started_async_phfsys)
        await asyncio.sleep(0.01)

        assert command._provider == res
        assert fake_started_async_phfsys.get_providers() == [res]
        assert res._asyncio_running
        assert res.a == 0
        assert res.b == 1

    @pytest.mark.asyncio
    async def test_NewHookCommand(self, fake_started_async_phfsys):
        command = commandinput.NewHookCommand("hook",
                                              1,
                                              args=[0],
                                              kwargs={"b": 1})
        assert command._class_name == "hook"
        assert command._provider_num == 1
        assert command._args == [0]
        assert command._kwargs == {"b": 1}

        for i in range(3):
            provider_command = commandinput.NewProviderCommand("Provider1",
                                                               args=[0],
                                                               kwargs={"b": 1})
            provider_command.execute_command(fake_started_async_phfsys)
            await asyncio.sleep(0.01)

        res = command.execute_command(fake_started_async_phfsys)
        await asyncio.sleep(0.01)

        assert res.a == 0
        assert res.b == 1
        assert res._running

        providers = fake_started_async_phfsys.get_providers()

        assert providers[0].get_hooks() == []
        assert providers[2].get_hooks() == []
        assert providers[1].get_hooks() == [res]

import asyncio

import pytest

from ProviderHookFramework.provider import BlockingContentProvider


class TestBasicForAllProviders:
    """Tests that all providers should pass."""
    def test_aliases(self, any_abstract_provider):
        assert any_abstract_provider.get_aliases() == \
               any_abstract_provider.__class__._alias

    def test_all_vars(self, any_abstract_provider):
        assert "_asynio_hooks" in any_abstract_provider.__dict__
        assert "_asyncio_hook_tasks" in any_abstract_provider.__dict__
        assert "_asyncio_straight_queues" in any_abstract_provider.__dict__
        assert "_asyncio_callback_queues" in any_abstract_provider.__dict__
        assert "_asyncio_task" in any_abstract_provider.__dict__
        assert "_asyncio_running" in any_abstract_provider.__dict__
        assert "_asyncio_loop" in any_abstract_provider.__dict__
        assert "_is_with_callback" in any_abstract_provider.__dict__

    def test_hook_addition_and_retrieve_nonstarted_provider(self,
                                                            any_abstract_provider,
                                                            hook):
        any_abstract_provider.add_hook(hook)
        assert any_abstract_provider._asyncio_straight_queues == []
        assert any_abstract_provider.get_hooks() == [hook]


amount_of_hooks = [0, 1, 2]


class TestConsistentProviders:
    """Tests for consistent providers.

    Include tests for hook addition before/after start of providers
    """

    @pytest.mark.asyncio
    @pytest.mark.parametrize("hook_amount", amount_of_hooks)
    async def test_consistent_provider_workflow_hooks_addition_before_cycle(
            self,
            hook_amount,
            hook_factory,
            any_nonabstract_consistent_provider,
            capsys,
            monkeypatch,
            run_smth_once
    ):
        monkeypatch.setattr(any_nonabstract_consistent_provider,
                            "_is_running",
                            run_smth_once)

        for i in range(hook_amount):
            hook = await hook_factory.get_hook()
            any_nonabstract_consistent_provider.add_hook(hook)
        await any_nonabstract_consistent_provider.cycle()

        if isinstance(any_nonabstract_consistent_provider, BlockingContentProvider):
            await asyncio.sleep(0.2)
        assert any_nonabstract_consistent_provider.logs[-1] == [0] * hook_amount

    @pytest.mark.asyncio
    @pytest.mark.parametrize("hook_amount", amount_of_hooks)
    async def test_consistent_provider_workflow_hooks_addition_after_cycle(
            self,
            hook_amount,
            hook_factory,
            controlled_result_callback_provider
    ):
        any_nonabstract_consistent_provider, control_func = \
            controlled_result_callback_provider
        asyncio.Task(any_nonabstract_consistent_provider.cycle())

        for i in range(hook_amount):
            hook = await hook_factory.get_hook()
            any_nonabstract_consistent_provider.add_hook(hook)

        await control_func()
        assert any_nonabstract_consistent_provider.logs[-1] == [0] * hook_amount

    @pytest.mark.asyncio
    @pytest.mark.parametrize("hook_amount", amount_of_hooks)
    async def test_multiple_evokes_in_order(
            self,
            hook_amount,
            hook_factory,
            controlled_result_callback_provider
    ):
        times = 3
        any_nonabstract_consistent_provider, control_func = \
            controlled_result_callback_provider
        asyncio.Task(any_nonabstract_consistent_provider.cycle())

        for i in range(hook_amount):
            hook = await hook_factory.get_hook()
            any_nonabstract_consistent_provider.add_hook(hook)

        expected_res = []
        for i in range(times):
            await control_func()
            expected_res.append([i] * hook_amount)

        assert any_nonabstract_consistent_provider.logs == expected_res


class TestComplexContentProvider:
    """Tests for ComplexContentProvider.

    Also includes MessageSystem tests."""

    class TestMessageSystem:
        """Message system tests.

        Include tests for remembering messages before message system init,
        right mapping of msg_id and msg answer.
        """

        @pytest.mark.asyncio
        async def test_message_system_uninit_message_queueing(self,
                                                              message_system):
            msg_amount = 3
            for i in range(msg_amount):
                message_system.send_to_provider(i + 1)

            assert message_system._tmp_queue.qsize() == msg_amount

            await message_system.initialize()

            assert message_system._tmp_queue.qsize() == 0
            assert message_system._input_queue.qsize() == msg_amount

            for i in range(3):
                assert (await message_system._input_queue.get())[0] == i + 1

        @pytest.mark.asyncio
        async def test_message_system_message_and_answer(self,
                                                         message_system):
            await message_system.initialize()
            for i in range(3):
                message_system.send_to_provider(i + 1)

            for i in range(3):
                msg = await message_system._input_queue.get()
                assert isinstance(msg, tuple)
                assert msg[1] == i
                assert msg[0] == i + 1
                await message_system._output_queue.put(msg)

            await asyncio.sleep(1)  # needed as everything is executed in the same loop

            assert message_system.retrieve_result(1) == 2
            assert message_system.retrieve_result(2) == 3
            assert message_system.retrieve_result(0) == 1

    def test_nonstarted_complex_provider(self, complex_provider_nonstarted):
        message_system = complex_provider_nonstarted.get_message_system()
        message_system.send_to_provider(0)

        assert message_system._tmp_queue.qsize() == 1
        assert message_system._input_queue is None
        assert message_system._output_queue is None

    @pytest.mark.asyncio
    @pytest.mark.parametrize("hook_amount", amount_of_hooks)
    async def test_complex_provider(self,
                                    complex_provider,
                                    hook_factory,
                                    hook_amount):
        for i in range(hook_amount):
            hook = await hook_factory.get_hook()
            complex_provider.add_hook(hook)

        message_system = complex_provider.get_message_system()
        for i in range(3):
            res = message_system.send_wait_answer(i + 1)
            assert res == [i + 1] * hook_amount

    @pytest.mark.asyncio
    @pytest.mark.parametrize("hook_amount", amount_of_hooks)
    async def test_complex_provider_nonconsistent_message_order(self,
                                                                complex_provider,
                                                                hook_factory,
                                                                hook_amount):
        for i in range(hook_amount):
            hook = await hook_factory.get_hook()
            complex_provider.add_hook(hook)

        message_system = complex_provider.get_message_system()
        for i in range(3):
            msg_id = message_system.send_to_provider(i + 1)
            assert msg_id == i

        assert message_system.retrieve_result(1) == [2] * hook_amount
        assert message_system.retrieve_result(2) == [3] * hook_amount
        assert message_system.retrieve_result(0) == [1] * hook_amount

    @pytest.mark.slow_test
    @pytest.mark.asyncio
    @pytest.mark.parametrize("hook_amount", amount_of_hooks)
    async def test_long_working_hook(self,
                                     complex_provider,
                                     hook_factory,
                                     hook_amount,
                                     monkeypatch):
        async def _long_hook_action(data):
            await asyncio.sleep(3)
            return data

        for i in range(hook_amount):
            hook = await hook_factory.get_hook()
            monkeypatch.setattr(hook, "hook_action", _long_hook_action)
            complex_provider.add_hook(hook)

        message_system = complex_provider.get_message_system()
        for i in range(3):
            msg_id = message_system.send_to_provider(i + 1)
            assert msg_id == i

        assert message_system.retrieve_result(1) == [2] * hook_amount
        assert message_system.retrieve_result(2) == [3] * hook_amount
        assert message_system.retrieve_result(0) == [1] * hook_amount

import asyncio

import pytest

from ProviderHookFramework.provider import BlockingContentProvider


def test_aliases(any_abstract_provider):
    assert any_abstract_provider.get_aliases() == \
           any_abstract_provider.__class__._alias


def test_all_vars(any_abstract_provider):
    assert "_asynio_hooks" in any_abstract_provider.__dict__
    assert "_asyncio_hook_tasks" in any_abstract_provider.__dict__
    assert "_asyncio_straight_queues" in any_abstract_provider.__dict__
    assert "_asyncio_callback_queues" in any_abstract_provider.__dict__
    assert "_asyncio_task" in any_abstract_provider.__dict__
    assert "_asyncio_running" in any_abstract_provider.__dict__
    assert "_asyncio_loop" in any_abstract_provider.__dict__
    assert "_is_with_callback" in any_abstract_provider.__dict__


def test_hook_addition_and_retrieve_nonstarted_provider(any_abstract_provider,
                                                        hook):
    any_abstract_provider.add_hook(hook)
    assert any_abstract_provider._asyncio_straight_queues == []
    assert any_abstract_provider.get_hooks() == [hook]


amount_of_hooks = [0, 1, 2]


@pytest.mark.asyncio
@pytest.mark.parametrize("hook_amount", amount_of_hooks)
async def test_consistent_provider_workflow_hooks_addition_before_cycle(
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
        hook = await hook_factory.get()
        any_nonabstract_consistent_provider.add_hook(hook)
    await any_nonabstract_consistent_provider.cycle()

    if isinstance(any_nonabstract_consistent_provider, BlockingContentProvider):
        await asyncio.sleep(0.2)
    assert any_nonabstract_consistent_provider.logs[-1] == [0] * hook_amount


@pytest.mark.asyncio
@pytest.mark.parametrize("hook_amount", amount_of_hooks)
async def test_consistent_provider_workflow_hooks_addition_after_cycle(
        hook_amount,
        hook_factory,
        controlled_result_callback_provider
):
    any_nonabstract_consistent_provider, control_func = \
        controlled_result_callback_provider
    task = asyncio.Task(any_nonabstract_consistent_provider.cycle())

    for i in range(hook_amount):
        hook = await hook_factory.get()
        any_nonabstract_consistent_provider.add_hook(hook)

    await control_func()
    assert any_nonabstract_consistent_provider.logs[-1] == [0] * hook_amount


@pytest.mark.asyncio
@pytest.mark.parametrize("hook_amount", amount_of_hooks)
async def test_multiple_in_order(
        hook_amount,
        hook_factory,
        controlled_result_callback_provider
):
    times = 3
    any_nonabstract_consistent_provider, control_func = \
        controlled_result_callback_provider
    task = asyncio.Task(any_nonabstract_consistent_provider.cycle())

    for i in range(hook_amount):
        hook = await hook_factory.get()
        any_nonabstract_consistent_provider.add_hook(hook)

    expected_res = []
    for i in range(times):
        await control_func()
        expected_res.append([i] * hook_amount)

    assert any_nonabstract_consistent_provider.logs == expected_res


@pytest.mark.asyncio
async def test_message_system_uninit_message_queueing(message_system):
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
async def test_message_system_message_and_answer(message_system):
    await message_system.initialize()
    for i in range(3):
        message_system.send_to_provider(i + 1)

    for i in range(3):
        await message_system._output_queue.put(await message_system._input_queue.get())

    await asyncio.sleep(1)  # needed as everything is executed in the same loop

    assert message_system.retrieve_result(1) == 2
    assert message_system.retrieve_result(2) == 3
    assert message_system.retrieve_result(0) == 1

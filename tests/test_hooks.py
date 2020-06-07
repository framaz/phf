import asyncio

import pytest


@pytest.mark.asyncio
async def test_hook_action(hook_factory):
    hook = await hook_factory.get_started_hook()
    in_queue = hook.get_straight_queue()
    out_queue = hook.get_callback_queue()
    message = "test"
    await in_queue.put(message)
    res = await out_queue.get()
    assert message == res


@pytest.mark.asyncio
async def test_hook_queues_creation_retrieve(hook):
    in_queue = hook.get_straight_queue()
    assert isinstance(in_queue, asyncio.Queue)
    assert in_queue is hook.get_straight_queue()
    out_queue = hook.get_callback_queue()
    assert isinstance(out_queue, asyncio.Queue)
    assert out_queue is hook.get_callback_queue()


@pytest.mark.asyncio
async def test_alias_and_change(hook):
    alias = hook.get_aliases()
    assert alias == hook.__class__._alias
    alias.append("azaza")
    assert alias != hook.get_aliases()


@pytest.mark.asyncio
async def test_hook_no_init_call(hook):
    assert "_asyncio_queue" in hook.__dict__
    assert "_callback_queue" in hook.__dict__
    assert "_provider" in hook.__dict__


@pytest.mark.asyncio
async def test_hook_stopping(hook):
    task = asyncio.Task(hook.cycle_call())
    await asyncio.sleep(1)
    hook.stop()
    await hook.get_straight_queue().put("kek")
    res = task


@pytest.mark.asyncio
async def test_multiple_unconsistent_add_and_retrieve(hook_factory):
    hook = await hook_factory.get_started_hook()
    in_queue = hook.get_straight_queue()
    out_queue = hook.get_callback_queue()
    results = []
    in_queue.put_nowait(0)
    in_queue.put_nowait(1)
    results.append(await out_queue.get())
    in_queue.put_nowait(2)
    results.append(await out_queue.get())
    results.append(await out_queue.get())
    assert results == [0, 1, 2]

import asyncio
import pytest
from utils.job_queue import PipelineQueue


@pytest.mark.anyio
async def test_job_queue_immediate_execution():
    queue = PipelineQueue(max_concurrent=2)
    job1, pos1 = await queue.enqueue("job1")
    job2, pos2 = await queue.enqueue("job2")

    assert pos1 == 0
    assert pos2 == 0
    assert job1.event.is_set()
    assert job2.event.is_set()

    await queue.complete(job1)
    await queue.complete(job2)


@pytest.mark.anyio
async def test_job_queue_waiting_and_promotion():
    queue = PipelineQueue(max_concurrent=1)
    job1, pos1 = await queue.enqueue("job1")
    job2, pos2 = await queue.enqueue("job2")
    job3, pos3 = await queue.enqueue("job3")

    assert pos1 == 0
    assert pos2 == 1
    assert pos3 == 2
    assert job1.event.is_set()
    assert not job2.event.is_set()
    assert not job3.event.is_set()

    # Track progress updates
    positions = []
    async def cb(p):
        positions.append(p)

    wait_task = asyncio.create_task(queue.wait_for_turn(job2, progress_callback=cb))
    await asyncio.sleep(0.1)
    assert positions == [1]

    # Complete job1, job2 should be promoted
    await queue.complete(job1)
    await wait_task
    assert job2.event.is_set()

    await queue.complete(job2)
    await queue.complete(job3)


@pytest.mark.anyio
async def test_job_queue_cancellation_safety():
    queue = PipelineQueue(max_concurrent=1)
    job1, pos1 = await queue.enqueue("job1")
    job2, pos2 = await queue.enqueue("job2")
    job3, pos3 = await queue.enqueue("job3")

    wait_task = asyncio.create_task(queue.wait_for_turn(job2))
    await asyncio.sleep(0.1)

    # Cancel job2 wait task
    wait_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await wait_task

    assert job2 not in queue.waiting
    assert len(queue.waiting) == 1
    assert queue.waiting[0] == job3

    await queue.complete(job1)
    await queue.complete(job3)

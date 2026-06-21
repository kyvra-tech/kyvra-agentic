import asyncio
import logging

logger = logging.getLogger(__name__)


class Job:
    def __init__(self, name: str) -> None:
        self.name = name
        self.event = asyncio.Event()


class PipelineQueue:
    def __init__(self, max_concurrent: int = 2) -> None:
        self.max_concurrent = max_concurrent
        self.active: list[Job] = []
        self.waiting: list[Job] = []
        self._lock = asyncio.Lock()

    async def enqueue(self, job_name: str) -> tuple[Job, int]:
        """Add job to queue. Returns (job, initial_position)."""
        job = Job(job_name)
        async with self._lock:
            if len(self.active) < self.max_concurrent:
                self.active.append(job)
                job.event.set()
                logger.debug("[JobQueue] Job '%s' started immediately.", job_name)
                return job, 0
            else:
                self.waiting.append(job)
                pos = len(self.waiting)
                logger.info("[JobQueue] Job '%s' queued at position %d.", job_name, pos)
                return job, pos

    async def wait_for_turn(self, job: Job, progress_callback=None) -> None:
        """Block until it is the job's turn."""
        if job.event.is_set():
            return

        last_pos = -1
        try:
            while not job.event.is_set():
                async with self._lock:
                    if job in self.waiting:
                        pos = self.waiting.index(job) + 1
                    else:
                        pos = 0

                if pos != last_pos:
                    if progress_callback:
                        await progress_callback(pos)
                    last_pos = pos

                await asyncio.sleep(0.2)
        except asyncio.CancelledError:
            logger.info("[JobQueue] Job '%s' cancelled while waiting.", job.name)
            async with self._lock:
                if job in self.waiting:
                    self.waiting.remove(job)
                if job in self.active:
                    self.active.remove(job)
                self._promote_next()
            raise

    def _promote_next(self) -> None:
        """Promote the next job from waiting to active. Call under lock."""
        while len(self.active) < self.max_concurrent and self.waiting:
            next_job = self.waiting.pop(0)
            self.active.append(next_job)
            next_job.event.set()
            logger.info("[JobQueue] Job '%s' promoted to active.", next_job.name)

    async def complete(self, job: Job) -> None:
        """Mark a job as finished and promote next."""
        async with self._lock:
            if job in self.active:
                self.active.remove(job)
                logger.debug("[JobQueue] Job '%s' completed.", job.name)
            elif job in self.waiting:
                self.waiting.remove(job)
                logger.debug("[JobQueue] Job '%s' removed from waiting.", job.name)
            self._promote_next()

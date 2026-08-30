import asyncio
import random
from dataclasses import dataclass, field


@dataclass(frozen=True)
class RetryStrategy:
    """سياسة إعادة محاولة بتراجع أسّي مع jitter."""

    max_attempts: int = 3
    base_delay: float = 0.5
    max_delay: float = 8.0
    retry_on_status: frozenset[int] = field(
        default_factory=lambda: frozenset({408, 429, 500, 502, 503, 504})
    )

    def should_retry(self, attempt: int, status_code: int | None) -> bool:
        if attempt >= self.max_attempts:
            return False
        if status_code is None:
            return True
        return status_code in self.retry_on_status

    def compute_delay(self, attempt: int) -> float:
        delay = min(self.base_delay * (2 ** (attempt - 1)), self.max_delay)
        return delay * random.uniform(0.5, 1.0)

    async def wait(self, attempt: int) -> None:
        await asyncio.sleep(self.compute_delay(attempt))

"""共享重试与限流工具 — 指数退避 + 模型级并发控制"""

import time
import random
import threading
import logging
from functools import wraps
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retryable_exceptions: tuple = (Exception,),
) -> Callable:
    """指数退避重试装饰器。

    延迟策略: base_delay * (2 ** attempt) + random jitter
    遇到非 retryable 异常直接抛出，不重试。
    """
    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @wraps(fn)
        def wrapper(*args, **kwargs) -> T:
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    return fn(*args, **kwargs)
                except retryable_exceptions as e:
                    last_error = e
                    if attempt >= max_retries:
                        logger.error(f"[retry] {fn.__name__} 重试{max_retries}次后仍失败: {e}")
                        raise
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    jitter = random.uniform(0, delay * 0.3)
                    total_delay = delay + jitter
                    logger.warning(
                        f"[retry] {fn.__name__} 第{attempt+1}/{max_retries}次重试, "
                        f"等待 {total_delay:.1f}s, 原因: {e}"
                    )
                    time.sleep(total_delay)
            raise last_error  # type: ignore[misc]
        return wrapper
    return decorator


class RateLimiter:
    """模型级并发限流器（信号量实现）。

    用法:
        limiter = RateLimiter("deepseek", max_concurrent=3)
        with limiter:
            result = llm_call()
    """

    _instances: dict[str, "RateLimiter"] = {}

    def __init__(self, name: str, max_concurrent: int = 3):
        self.name = name
        self._semaphore = threading.BoundedSemaphore(max_concurrent)
        self._lock = threading.Lock()
        self._active_count = 0

    @classmethod
    def get(cls, name: str, max_concurrent: int = 3) -> "RateLimiter":
        """获取或创建指定模型的限流器"""
        if name not in cls._instances:
            cls._instances[name] = cls(name, max_concurrent)
        return cls._instances[name]

    def acquire(self) -> bool:
        acquired = self._semaphore.acquire(timeout=120)
        if acquired:
            with self._lock:
                self._active_count += 1
            logger.debug(f"[ratelimit] {self.name} acquire (active={self._active_count})")
        return acquired

    def release(self) -> None:
        with self._lock:
            self._active_count = max(0, self._active_count - 1)
        self._semaphore.release()
        logger.debug(f"[ratelimit] {self.name} release (active={self._active_count})")

    @property
    def active(self) -> int:
        with self._lock:
            return self._active_count

    def __enter__(self):
        if not self.acquire():
            raise RuntimeError(f"[ratelimit] {self.name} 获取许可超时")
        return self

    def __exit__(self, *args):
        self.release()


def run_with_timeout(fn: Callable[..., T], timeout: float = 60.0, *args, **kwargs) -> T:
    """在线程中执行函数，超时抛出 TimeoutError。"""
    result_holder: list = []
    error_holder: list = []

    def target():
        try:
            result_holder.append(fn(*args, **kwargs))
        except Exception as e:
            error_holder.append(e)

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        raise TimeoutError(f"{fn.__name__} 执行超时 ({timeout}s)")

    if error_holder:
        raise error_holder[0]

    return result_holder[0] if result_holder else None  # type: ignore[return-value]

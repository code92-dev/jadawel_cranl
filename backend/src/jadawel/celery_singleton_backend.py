from django.conf import settings
from django.core.cache import cache

from celery_singleton.backends import RedisBackend
from django_redis import get_redis_connection

# Compare-and-act on the flag in a single round-trip so we never touch a lock a newer
# holder has taken over between a read and the write (TOCTOU). `expire` takes seconds.
_EXTEND_IF_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("expire", KEYS[1], ARGV[2])
end
return 0
"""

_CLEAR_IF_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
end
return 0
"""


class RedisBackendForSingleton(RedisBackend):
    def __init__(self, *args, **kwargs):
        """
        Use the existing redis connection instead of creating a new one.
        """

        self.redis = get_redis_connection("default")

    def extend_lock_if(self, lock: str, task_id: str, expiry: int) -> bool:
        """
        Re-arms the expiry of a lock this task still holds. A lock taken over by a
        newer task in the meantime is left alone.

        :param lock: The key returned by `Singleton.generate_lock`.
        :param task_id: The id of the task that acquired the lock.
        :param expiry: The new lifetime in seconds, counted from now.
        :return: Whether the lock was still held and extended.
        """

        return bool(self.redis.eval(_EXTEND_IF_SCRIPT, 1, lock, task_id, expiry))

    def release_lock_if(self, lock: str, task_id: str) -> bool:
        """
        Releases a lock only while this task still holds it. A task whose lease
        expired must not remove the lock a newer task acquired since.

        :param lock: The key returned by `Singleton.generate_lock`.
        :param task_id: The id of the task that acquired the lock.
        :return: Whether the lock was still held and released.
        """

        return bool(self.redis.eval(_CLEAR_IF_SCRIPT, 1, lock, task_id))


class SingletonAutoRescheduleFlag:
    """
    Flag is used to indicate that a task of this type is pending reschedule.

    When the task ends, if this flag is set, it will re-schedule itself to
    ensure that task is eventually run.
    """

    def __init__(self, key: str):
        self.key = key

    def is_set(self) -> bool:
        """
        Checks if the flag is set.

        :return: True if the lock is set, False otherwise.
        """

        return cache.get(key=self.key) or False

    def set(self) -> bool:
        """
        Sets the flag for the task, indicating it needs to be rescheduled.

        :return: True if the flag was set, False if it was already set.
        """

        return cache.set(
            key=self.key,
            value=True,
            timeout=settings.AUTO_INDEX_LOCK_EXPIRY * 2,
        )

    def clear(self) -> bool:
        """
        Clears the flag for the task.
        :return: True if the flag was cleared, False otherwise.
        """

        return cache.delete(key=self.key)

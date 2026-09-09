# backend/src/jadawel/core/redis.py

- RedisQueue · class · L8-L102 — class RedisQueue
- __init__ · method · L13-L26 — def __init__( self, queue_key: str, redis_connection: Redis, max_length: Optional[int] = None )
- enqueue_task · method · L28-L74 — def enqueue_task(self, task_object: Any) -> bool
- get_and_pop_next · method · L76-L95 — def get_and_pop_next(self) -> Any
- clear · method · L97-L102 — def clear(self)
- WebhookRedisQueue · class · L105-L119 — class WebhookRedisQueue(RedisQueue)
- enqueue_task · method · L108-L110 — def enqueue_task(self, task_object)
- get_and_pop_next · method · L112-L116 — def get_and_pop_next(self)
- clear · method · L118-L119 — def clear(self)

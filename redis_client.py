import redis, json



CHAT_KEY = "admin_chat"

class RedisClient:
    def __init__(self):
        import os
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            self.client = redis.from_url(redis_url)
        else:
            host = os.getenv("REDIS_HOST", "localhost")
            port = int(os.getenv("REDIS_PORT", 6379))
            self.client = redis.Redis(host=host, port=port, db=0)

    def add_message(self, msg: dict):
        self.client.rpush(CHAT_KEY, json.dumps(msg))
        self.client.ltrim(CHAT_KEY, -60, -1)  # keep last 60 messages
        self.client.expire(CHAT_KEY, 3*24*3600)  # 3 days TTL

    def get_last_messages(self):
        msgs = self.client.lrange(CHAT_KEY, 0, -1)
        messages = [json.loads(m) for m in msgs]
        print("All messages in Redis:", messages)
        return messages

    def clear_history(self):
        """Clear the chat history from Redis."""
        try:
            self.client.delete(CHAT_KEY)
            print("Redis chat history cleared.")
        except Exception as e:
            print(f"Error clearing Redis history: {e}")
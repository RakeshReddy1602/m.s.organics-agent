import redis, json



CHAT_KEY = "admin_chat"

class RedisClient:
    def __init__(self):
        self.client = redis.Redis(host="localhost", port=6379, db=0)
        self.client.flushall()

    def add_message(self, msg: dict):
        self.client.rpush(CHAT_KEY, json.dumps(msg))
        self.client.ltrim(CHAT_KEY, -40, -1)  # keep last 40 messages
        self.client.expire(CHAT_KEY, 3*24*3600)  # 3 days TTL

    def get_last_messages(self):
        msgs = self.client.lrange(CHAT_KEY, 0, -1)
        messages = [json.loads(m) for m in msgs]
        print("All messages in Redis:", messages)
        return messages
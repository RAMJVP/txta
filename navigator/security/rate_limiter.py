import time
from collections import defaultdict, deque
class RateLimiter:
    def __init__(self,limit=30,window=60): self.limit=limit; self.window=window; self.hits=defaultdict(deque)
    def allow(self,key:str)->bool:
        now=time.monotonic(); q=self.hits[key]
        while q and q[0] <= now-self.window: q.popleft()
        if len(q)>=self.limit: return False
        q.append(now); return True
rate_limiter=RateLimiter()

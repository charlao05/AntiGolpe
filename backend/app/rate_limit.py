import hashlib,os,time
from collections import defaultdict,deque
class RateLimiter:
    def __init__(self,limit:int=30,window_seconds:int=3600):
        self.limit=limit; self.window=window_seconds; self.events=defaultdict(deque); self.salt=os.getenv('RATE_LIMIT_SALT','development-only-change-me')
    def allowed(self,ip:str)->bool:
        key=hashlib.sha256((self.salt+ip).encode()).hexdigest(); now=time.time(); q=self.events[key]
        while q and q[0]<now-self.window:q.popleft()
        if len(q)>=self.limit:return False
        q.append(now); return True

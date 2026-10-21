import hashlib, re
class SessionMemoryService:
    def __init__(self,repo): self.repo=repo
    @staticmethod
    def h(session_id): return hashlib.sha256(session_id.encode()).hexdigest()
    async def append(self,session_id,turn): await self.repo.append(self.h(session_id),turn)
    async def clear(self,session_id): await self.repo.delete(self.h(session_id))
    async def resolve(self,session_id,query):
        if not re.fullmatch(r'(the )?(first|second|one|that)( one)?|show more( about)? (that|it)',query,re.I): return query
        doc=await self.repo.get(self.h(session_id))
        turns=(doc or {}).get('turns',[])
        return turns[-1].get('normalizedQuery',query) if turns else query

import time, uuid
from navigator.schemas.navigator import SearchResponse, NavigatorResult
from navigator.security.input_policy import InvalidQuery

class NavigatorService:
    def __init__(self,validator,pii,safety,hybrid,confidence,url_policy,memory,logger): self.validator=validator; self.pii=pii; self.safety=safety; self.hybrid=hybrid; self.confidence=confidence; self.url_policy=url_policy; self.memory=memory; self.logger=logger
    async def search(self,request):
        rid=str(uuid.uuid4()); started=time.perf_counter()
        try: q=self.validator.validate(request.query)
        except InvalidQuery:
            return SearchResponse(requestId=rid,status='invalid',message='Please enter a valid search query.')
        redacted,pii_types=self.pii.redact(request.query)
        safe_q=self.validator.validate(redacted)
        decision=self.safety.decide(safe_q)
        safe_q=await self.memory.resolve(request.sessionId,safe_q)
        if decision in ('block','safe_redirect'):
            msg='This navigator cannot help with that request.' if decision=='block' else 'If you may be in immediate danger, contact local emergency services or a trusted person now.'
            await self.logger.log({'sessionIdHash':self.memory.h(request.sessionId),'question':redacted,'normalizedQuestion':safe_q,'safetyDecision':decision,'outcome':'blocked','latencyMs':int((time.perf_counter()-started)*1000)})
            return SearchResponse(requestId=rid,status='blocked',message=msg)
        try:
            rows,vector_ok=await self.hybrid.search(safe_q)
        except Exception:
            return SearchResponse(requestId=rid,status='temporary_error',message='Search is temporarily unavailable. Please try again.')
        rows=self.url_policy.filter(rows); chosen=self.confidence.select(rows,vector_ok,2)
        results=[NavigatorResult(pageId=str(r.get('_id','')),title=r.get('title',''),description=r.get('description','')[:240],url=r.get('url') or r.get('canonicalUrl'),confidence=c,matchReasons=r.get('matchReasons',[])) for r,c in chosen]
        status='results' if results else 'not_found'; msg='I found these pages on InspireMe.in.' if results else "I couldn't find a relevant page on InspireMe.in."
        await self.memory.append(request.sessionId,{'query':redacted[:300],'normalizedQuery':safe_q,'resultPageIds':[x.pageId for x in results],'at':time.time()})
        await self.logger.log({'sessionIdHash':self.memory.h(request.sessionId),'question':redacted,'normalizedQuestion':safe_q,'piiTypes':pii_types,'safetyDecision':'allow','resultPageIds':[x.pageId for x in results],'outcome':status,'latencyMs':int((time.perf_counter()-started)*1000)})
        return SearchResponse(requestId=rid,status=status,results=results,message=msg)

import asyncio
from navigator.retrieval.reciprocal_rank_fusion import rrf
from navigator.retrieval.query_boosts import boost
from navigator.retrieval.page_deduplicator import dedupe
from navigator.retrieval.match_reason_builder import build_reasons

class HybridSearch:
    def __init__(self,repo,embedder,candidate_limit=10): self.repo=repo; self.embedder=embedder; self.limit=candidate_limit
    async def search(self,q):
        lexical_task=asyncio.create_task(self.repo.lexical_search(q,self.limit))
        vector_ok=True; vector=[]
        try:
            emb=await self.embedder.embed_query(q)
            vector_task=asyncio.create_task(self.repo.vector_search(emb,self.limit))
            lexical,vector=await asyncio.gather(lexical_task,vector_task)
        except Exception:
            vector_ok=False
            lexical=await lexical_task if not lexical_task.done() else lexical_task.result()
        scores=rrf(lexical,vector)
        lmap={str(x.get('canonicalUrl') or x.get('_id')):x for x in lexical}; vmap={str(x.get('canonicalUrl') or x.get('_id')):x for x in vector}
        out=[]
        for key,base in scores.items():
            d=(lmap.get(key) or vmap.get(key)).copy()
            d['lexicalMatched']=key in lmap
            d['vectorMatched']=key in vmap
            d['lexicalScore']=float(lmap[key].get('score',0.0)) if key in lmap else 0.0
            d['vectorScore']=float(vmap[key].get('score',0.0)) if key in vmap else 0.0
            extra,br=boost(d,q); d['fusedScore']=base+extra; d['matchReasons']=build_reasons(key in lmap,key in vmap,br); out.append(d)
        out.sort(key=lambda x:x['fusedScore'],reverse=True)
        return dedupe(out),vector_ok

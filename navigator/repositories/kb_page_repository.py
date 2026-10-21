from navigator.core.config import get_settings
class KbPageRepository:
    def __init__(self,db): self.db=db; self.c=db.kb_pages if db is not None else None
    async def lexical_search(self,q:str,limit:int):
        if self.c is None: raise ConnectionError('database unavailable')
        s=get_settings()
        pipeline=[{'$search':{'index':s.atlas_lexical_index,'compound':{'filter':[{'equals':{'path':'status','value':'published'}}],'should':[
          {'text':{'query':q,'path':'title','score':{'boost':{'value':8}}}}, {'text':{'query':q,'path':'keywords','score':{'boost':{'value':6}}}},
          {'text':{'query':q,'path':'headings','score':{'boost':{'value':4}}}}, {'text':{'query':q,'path':'description','score':{'boost':{'value':3}}}},
          {'text':{'query':q,'path':'content'}}], 'minimumShouldMatch':1}}}, {'$limit':limit},
          {'$project':{'_id':1,'canonicalUrl':1,'url':1,'title':1,'description':1,'keywords':1,'category':1,'score':{'$meta':'searchScore'}}}]
        return await self.c.aggregate(pipeline, maxTimeMS=900).to_list(length=limit)
    async def vector_search(self,embedding:list[float],limit:int):
        if self.c is None: raise ConnectionError('database unavailable')
        s=get_settings(); n=max(limit*10,100)
        pipeline=[{'$vectorSearch':{'index':s.atlas_vector_index,'path':'embedding','queryVector':embedding,'numCandidates':n,'limit':limit,'filter':{'status':'published'}}},
          {'$project':{'_id':1,'canonicalUrl':1,'url':1,'title':1,'description':1,'keywords':1,'category':1,'score':{'$meta':'vectorSearchScore'}}}]
        return await self.c.aggregate(pipeline, maxTimeMS=900).to_list(length=limit)
    async def upsert_page(self,doc:dict):
        return await self.c.update_one({'canonicalUrl':doc['canonicalUrl']},{'$set':doc},upsert=True)
    async def find_by_canonical(self,url:str): return await self.c.find_one({'canonicalUrl':url})

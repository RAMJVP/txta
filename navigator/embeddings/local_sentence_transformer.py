import asyncio
from threading import Lock
from navigator.embeddings.query_embedding_cache import LRUCache
class LocalSentenceTransformer:
    def __init__(self,model_name:str,cache_size:int=1000):
        self.model_name=model_name
        self._model=None
        self._load_lock=Lock()
        self.cache=LRUCache(cache_size)
    def _load(self):
        if self._model is None:
            # Several requests can arrive together after startup. Load the
            # model exactly once; duplicate model loads consume substantial
            # memory and make every request exceed the API timeout.
            with self._load_lock:
                if self._model is None:
                    from sentence_transformers import SentenceTransformer
                    self._model=SentenceTransformer(self.model_name)
        return self._model
    async def warmup(self):
        await asyncio.to_thread(self._load)
    async def embed_query(self,text):
        key='q:'+text; hit=self.cache.get(key)
        if hit is not None:return hit
        prefix='query: ' if 'e5' in self.model_name.lower() else ''
        vec=await asyncio.to_thread(lambda:self._load().encode(prefix+text,normalize_embeddings=True).tolist())
        self.cache.put(key,vec); return vec
    async def embed_documents(self,texts):
        prefix='passage: ' if 'e5' in self.model_name.lower() else ''
        return await asyncio.to_thread(lambda:self._load().encode([prefix+t for t in texts],normalize_embeddings=True).tolist())

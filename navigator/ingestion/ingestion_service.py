from datetime import datetime, timezone
from navigator.ingestion.page_fetcher import fetch_page
from navigator.ingestion.html_cleaner import clean_html
from navigator.ingestion.metadata_extractor import extract_metadata
from navigator.ingestion.content_hasher import content_hash
from navigator.ingestion.content_chunker import chunk_text
from navigator.ingestion.page_validator import validate_page
class IngestionService:
    def __init__(self,page_repo,embedder,model_name,dimension,chunk_repo=None): self.repo=page_repo; self.embedder=embedder; self.model=model_name; self.dim=dimension; self.chunk_repo=chunk_repo
    async def ingest_url(self,url):
        final,html=await fetch_page(url); meta=extract_metadata(html); text=clean_html(html); canonical=validate_page(final,meta['canonical']); h=content_hash(text); old=await self.repo.find_by_canonical(canonical)
        if old and old.get('contentHash')==h: return 'unchanged'
        emb=(await self.embedder.embed_documents([text[:12000]]))[0]
        now=datetime.now(timezone.utc); doc={'canonicalUrl':canonical,'url':canonical.replace('https://inspireme.in','') or '/','title':meta['title'],'description':meta['description'],'keywords':meta['keywords'],'headings':meta['headings'],'category':'','content':text,'contentHash':h,'locale':'en-IN','status':'published','embedding':emb,'embeddingModel':self.model,'embeddingDimension':self.dim,'indexedAt':now}
        result=await self.repo.upsert_page(doc)
        current=await self.repo.find_by_canonical(canonical); page_id=current['_id']
        if self.chunk_repo is not None:
            parts=chunk_text(text) if len(text.split())>500 else []
            vectors=await self.embedder.embed_documents(parts) if parts else []
            chunks=[{'pageId':page_id,'canonicalUrl':canonical,'chunkNumber':i,'content':part,'headingPath':[],'contentHash':content_hash(part),'embedding':vectors[i],'embeddingModel':self.model,'embeddingDimension':self.dim,'status':'published','indexedAt':now} for i,part in enumerate(parts)]
            await self.chunk_repo.replace_for_page(page_id,chunks)
        return 'updated'

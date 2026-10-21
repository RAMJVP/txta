import asyncio
from fastapi import Request
from navigator.core.config import get_settings
from navigator.repositories.kb_page_repository import KbPageRepository
from navigator.repositories.session_repository import SessionRepository
from navigator.repositories.visitor_question_repository import VisitorQuestionRepository
from navigator.embeddings.factory import create_embedding_provider
from navigator.retrieval.hybrid_search import HybridSearch
from navigator.services.query_validation_service import QueryValidationService
from navigator.services.pii_redaction_service import PiiRedactionService
from navigator.services.safety_service import SafetyService
from navigator.services.session_memory_service import SessionMemoryService
from navigator.services.question_logging_service import QuestionLoggingService
from navigator.services.url_policy_service import UrlPolicyService
from navigator.services.confidence_service import ConfidenceService
from navigator.services.navigator_service import NavigatorService

def get_db(request:Request): return request.app.state.db

async def get_navigator_service(request:Request):
    """Create one Navigator service/model per FastAPI process, not per request."""
    state=request.app.state
    existing=getattr(state,'navigator_service',None)
    if existing is not None: return existing

    lock=getattr(state,'navigator_service_lock',None)
    if lock is None:
        lock=asyncio.Lock()
        state.navigator_service_lock=lock

    async with lock:
        existing=getattr(state,'navigator_service',None)
        if existing is not None: return existing

        s=get_settings(); db=get_db(request); page=KbPageRepository(db)
        session=SessionRepository(db,s.navigator_session_ttl_minutes,s.navigator_session_max_turns)
        embedder=create_embedding_provider()
        # Dependency resolution occurs before the route's search timeout. The
        # first request may take longer while the model is loaded/downloaded,
        # but subsequent searches reuse the warm model and query cache.
        await embedder.warmup()
        service=NavigatorService(
            QueryValidationService(s.navigator_query_max_length),
            PiiRedactionService(),SafetyService(),
            HybridSearch(page,embedder,s.navigator_candidate_limit),
            ConfidenceService(s.navigator_min_rrf_score,s.navigator_high_rrf_score,s.navigator_min_vector_score),
            UrlPolicyService(),SessionMemoryService(session),
            QuestionLoggingService(VisitorQuestionRepository(db),s.navigator_log_retention_days))
        state.navigator_service=service
        return service

from navigator.core.config import get_settings
from navigator.embeddings.local_sentence_transformer import LocalSentenceTransformer
def create_embedding_provider():
    s=get_settings()
    # Query and document vectors must come from the exact same model. A silent
    # fallback can have the same dimension but an incompatible vector space.
    return LocalSentenceTransformer(s.embedding_model,s.navigator_embedding_cache_size)

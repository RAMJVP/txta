from navigator.retrieval.reciprocal_rank_fusion import rrf
class RankFusionService:
    def fuse(self, lexical, vector): return rrf(lexical,vector)

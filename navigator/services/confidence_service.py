from navigator.retrieval.confidence_classifier import confidence
class ConfidenceService:
    def __init__(self,min_score,high_score,min_vector_score=0.55): self.min=min_score; self.high=high_score; self.min_vector=min_vector_score
    def select(self,rows,vector_ok,limit=2):
        out=[]
        for r in rows:
            # RRF measures rank, not semantic relevance. Without checking the
            # raw cosine score, vector search always has a "nearest" page and
            # unrelated finance pages can be returned as false positives.
            if vector_ok and r.get('vectorScore',0.0) < self.min_vector:
                boosts=set(r.get('matchReasons',[]))
                if not ({'exact_title','exact_keyword'} & boosts):
                    continue
            c=confidence(r['fusedScore'],vector_ok,self.high,self.min)
            if c: out.append((r,c))
            if len(out)>=limit: break
        return out

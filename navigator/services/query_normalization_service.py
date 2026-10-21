from navigator.security.input_policy import normalize_query
class QueryNormalizationService:
    def __init__(self,max_len=300): self.max_len=max_len
    def normalize(self,value): return normalize_query(value,self.max_len)

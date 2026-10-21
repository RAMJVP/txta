from navigator.security.input_policy import normalize_query
class QueryValidationService:
    def __init__(self,max_len=300): self.max_len=max_len
    def validate(self,q): return normalize_query(q,self.max_len)

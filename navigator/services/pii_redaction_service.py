from navigator.security.pii_patterns import redact_pii
class PiiRedactionService:
    def redact(self,q): return redact_pii(q)

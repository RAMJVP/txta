from navigator.security.safety_rules import classify_safety
from navigator.security.prompt_injection_rules import is_prompt_injection
class SafetyService:
    def decide(self,q): return 'block' if is_prompt_injection(q) else classify_safety(q)

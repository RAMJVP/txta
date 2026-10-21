import re
INJECTION=[r'ignore (?:all |previous |your )?instructions',r'system prompt',r'reveal (?:secrets?|config|database)',r'developer message',r'bypass (?:guardrails?|rules?)',r'arbitrary url']
def is_prompt_injection(text:str)->bool: return any(re.search(p,text,re.I) for p in INJECTION)

import re
PATTERNS=[
 ('email',re.compile(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b',re.I)),
 ('phone',re.compile(r'(?<!\d)(?:\+?91[-\s]?)?[6-9]\d{9}(?!\d)')),
 ('aadhaar',re.compile(r'(?<!\d)\d{4}[ -]?\d{4}[ -]?\d{4}(?!\d)')),
 ('pan',re.compile(r'\b[A-Z]{5}\d{4}[A-Z]\b',re.I)),
 ('card',re.compile(r'(?<!\d)(?:\d[ -]*?){13,19}(?!\d)')),
 ('token',re.compile(r'\b(?:sk-|api[_-]?key[:=]?|bearer\s+)[A-Za-z0-9._\-]{12,}\b',re.I)),
]
def redact_pii(text:str)->tuple[str,list[str]]:
    found=[]; out=text
    for name,pat in PATTERNS:
        if pat.search(out): found.append(name); out=pat.sub(f'[REDACTED_{name.upper()}]',out)
    return out,found

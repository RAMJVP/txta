import re
BLOCK=[r'credential theft',r'steal passwords?',r'build ransomware',r'malware payload',r'child sexual',r'kill (?:a|the) person',r'make a bomb']
SELF=[r'kill myself',r'end my life',r'suicide']
def classify_safety(text:str)->str:
    if any(re.search(p,text,re.I) for p in SELF): return 'safe_redirect'
    if any(re.search(p,text,re.I) for p in BLOCK): return 'block'
    return 'allow'

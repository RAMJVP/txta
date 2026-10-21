import re, unicodedata
class InvalidQuery(ValueError): pass
CONTROL=re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')
REPEAT=re.compile(r'(.)\1{14,}', re.DOTALL)
def normalize_query(value:str,max_len:int=300)->str:
    if not isinstance(value,str): raise InvalidQuery('query must be text')
    value=unicodedata.normalize('NFKC', value).strip()
    if not value: raise InvalidQuery('empty query')
    if len(value)>max_len: raise InvalidQuery('query too long')
    if CONTROL.search(value): raise InvalidQuery('control characters')
    if REPEAT.search(value): raise InvalidQuery('repeated-character abuse')
    return ' '.join(value.split()).casefold()

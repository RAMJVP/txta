def dedupe(rows):
    seen=set(); out=[]
    for r in rows:
        key=(r.get('canonicalUrl') or r.get('url') or str(r.get('_id',''))).strip().rstrip('/').casefold()
        if key not in seen: seen.add(key); out.append(r)
    return out

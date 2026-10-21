def boost(candidate:dict,q:str)->tuple[float,list[str]]:
    score=0.0; reasons=[]; nq=q.casefold().strip()
    if candidate.get('title','').casefold().strip()==nq: score+=0.02; reasons.append('exact_title')
    kws=[str(x).casefold() for x in candidate.get('keywords',[])]
    if nq in kws: score+=0.012; reasons.append('exact_keyword')
    if candidate.get('category','').casefold()==nq: score+=0.006; reasons.append('category_match')
    return score,reasons

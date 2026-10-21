def rrf(lexical:list[dict],vector:list[dict],k:int=60)->dict[str,float]:
    scores={}
    for docs in (lexical,vector):
        for rank,d in enumerate(docs,1):
            key=str(d.get('canonicalUrl') or d.get('_id')); scores[key]=scores.get(key,0)+1/(k+rank)
    return scores

def confidence(score:float,vector_ok:bool,high:float,min_score:float):
    if score < min_score: return None
    if vector_ok and score>=high: return 'High'
    return 'Medium' if vector_ok else 'Low'

def build_reasons(in_lex,in_vec,boost_reasons):
    r=[]
    if in_lex:r.append('lexical_match')
    if in_vec:r.append('semantic_match')
    r.extend(boost_reasons)
    return list(dict.fromkeys(r))

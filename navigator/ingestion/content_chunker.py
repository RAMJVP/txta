def chunk_text(text:str,size=400,overlap=60):
    words=text.split(); out=[]; step=max(1,size-overlap)
    for i in range(0,len(words),step):
        chunk=' '.join(words[i:i+size])
        if chunk: out.append(chunk)
        if i+size>=len(words): break
    return out

from collections import OrderedDict
class LRUCache:
    def __init__(self,maxsize=1000): self.max=maxsize; self.d=OrderedDict()
    def get(self,k):
        if k not in self.d: return None
        self.d.move_to_end(k); return self.d[k]
    def put(self,k,v):
        self.d[k]=v; self.d.move_to_end(k)
        while len(self.d)>self.max: self.d.popitem(last=False)

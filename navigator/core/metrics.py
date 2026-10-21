from time import perf_counter
class Timer:
    def __enter__(self): self.start=perf_counter(); return self
    def __exit__(self,*args): self.elapsed_ms=(perf_counter()-self.start)*1000

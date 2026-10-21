from dataclasses import dataclass, field
from typing import Any
@dataclass
class Candidate:
    page_id: str
    canonical_url: str
    title: str
    description: str=''
    url: str=''
    keywords: list[str]=field(default_factory=list)
    category: str=''
    lexical_score: float=0.0
    vector_score: float=0.0
    fused_score: float=0.0
    reasons: list[str]=field(default_factory=list)
    raw: dict[str,Any]=field(default_factory=dict)

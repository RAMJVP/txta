from typing import Literal
from pydantic import BaseModel, Field

Status=Literal['results','not_found','blocked','invalid','temporary_error']
Confidence=Literal['High','Medium','Low']
class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=300)
    sessionId: str = Field(min_length=8, max_length=128)
    locale: str = Field(default='en-IN', max_length=16)
class NavigatorResult(BaseModel):
    pageId: str
    title: str
    description: str
    url: str
    confidence: Confidence
    matchReasons: list[str]
class SearchResponse(BaseModel):
    requestId: str
    status: Status
    results: list[NavigatorResult]=[]
    message: str|None=None
    scope: str='inspireme.in'
class LinkClickRequest(BaseModel):
    requestId: str=Field(min_length=8,max_length=80)
    pageId: str=Field(min_length=1,max_length=100)

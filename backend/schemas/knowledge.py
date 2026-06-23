from pydantic import BaseModel


class KnowledgeIngestIn(BaseModel):
    text: str
    source: str | None = None


class KnowledgeIngestOut(BaseModel):
    success: bool
    message: str


class KnowledgeQueryIn(BaseModel):
    question: str
    mode: str = "hybrid"


class KnowledgeQueryOut(BaseModel):
    answer: str
    mode: str

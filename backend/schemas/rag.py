from typing import Literal, Optional

from pydantic import BaseModel, Field


class RAGDocumentIn(BaseModel):
    """
    写入知识库的请求体。

    text 是必填的原始资料；source 是可选来源，方便你之后扩展成“文件名/网页地址/备注”。
    """

    text: str = Field(..., min_length=1, description="需要写入 LightRAG 知识库的文本")
    source: Optional[str] = Field(default=None, description="资料来源，可选")


class RAGQueryIn(BaseModel):
    """
    查询知识库的请求体。
    """

    question: str = Field(..., min_length=1, description="用户问题")
    mode: Literal["naive", "local", "global", "hybrid"] = Field(
        default="hybrid",
        description="LightRAG 查询模式，默认 hybrid",
    )


class RAGQueryOut(BaseModel):
    """
    查询结果响应体。
    """

    answer: str
    mode: str


class RAGWriteOut(BaseModel):
    """
    写入知识库后的响应体。
    """

    success: bool
    message: str

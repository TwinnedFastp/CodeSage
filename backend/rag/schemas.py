from typing import Literal, Optional

from pydantic import BaseModel, Field


class RAGDocumentIn(BaseModel):
    """
    写入知识库的请求体。

    text 是必填的原始资料；source 是可选来源，方便你之后扩展成"文件名/网页地址/备注"。
    """

    text: str = Field(..., min_length=1, description="需要写入 LightRAG 知识库的文本")
    source: Optional[str] = Field(default=None, description="资料来源，可选")


class FileUploadIn(BaseModel):
    """
    文件上传请求体（前端读取文件文本内容后上传）。
    """

    filename: str = Field(..., description="原始文件名，如 notes.md")
    content: str = Field(..., min_length=1, description="文件文本内容")
    source: Optional[str] = Field(default=None, description="来源标注，可选")


class RAGQueryIn(BaseModel):
    """
    查询知识库的请求体。
    """

    question: str = Field(..., min_length=1, description="用户问题")
    # 6 种模式对齐 backend/rag/service.py:361 的 LightRAG 原生支持
    # - naive：普通向量检索
    # - local / global：局部实体关系 / 全局图谱关系（依赖知识图谱）
    # - hybrid：local + global 混合
    # - mix：知识图谱 + 向量检索（最全面，最慢）
    # - bypass：跳过检索直接调 LLM（调试用）
    mode: Literal["naive", "local", "global", "hybrid", "mix", "bypass"] = Field(
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


class FileUploadOut(BaseModel):
    """
    文件上传后的响应体。
    """

    success: bool
    message: str

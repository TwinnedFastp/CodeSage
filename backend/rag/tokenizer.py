"""
离线分词器：替代 tiktoken，避免 o200k_base 词表远程下载

背景
----
LightRAG 默认使用 TiktokenTokenizer（tiktoken.encoding_for_model("gpt-4o-mini")），
首次调用会从 https://openaipublic.blob.core.windows.net/encodings/o200k_base.tiktoken
下载词表文件。国内网络环境下该域名 SSL 握手失败（SSLEOFError），导致知识库
初始化时报错，前端表现为点击「知识库」就 503。

方案
----
实现一个纯 Python 的 Tokenizer 子类（OfflineTokenizer），用启发式估算 token 数：
  - 中文 / 日文 / 韩文：约 1.5 字符 / token
  - 其他（英文 / 标点 / 空白）：约 4 字符 / token
LightRAG 仅用 len(tokenizer.encode(text)) 控制分块大小，不依赖真实 token id，
因此估算值完全够用，且整个过程零网络请求。

启用方式
--------
在 backend/rag/service.py 构造 LightRAG 时传入 tokenizer=OfflineTokenizer()。
受 config.RAG_OFFLINE_TOKENIZER 开关控制（默认开启，适合国内部署）。
"""
from __future__ import annotations

import re
from typing import List

from lightrag.utils import Tokenizer

# CJK 统一表意文字 + 假名 + 谚文 + 全角符号区段
# 命中这些字符按 1.5 字符/token 估算，其余按 4 字符/token
_CJK_RE = re.compile(
    r"[\u3040-\u30ff"  # 平假名 / 片假名
    r"\u3400-\u4dbf"   # CJK 扩展 A
    r"\u4e00-\u9fff"   # CJK 基本区
    r"\uf900-\ufaff"   # CJK 兼容表意
    r"\uff00-\uffef]"  # 全角符号
)

# 启发式系数，对齐 GPT 系列经验估值
_CJK_CHARS_PER_TOKEN = 1.5
_OTHER_CHARS_PER_TOKEN = 4.0


class _HeuristicCore:
    """
    离线分词核心：真正干活的 encode/decode 实现。

    作为 Tokenizer 基类内部的 tokenizer 属性使用（基类会把 encode/decode
    委托给 self.tokenizer），因此这里的方法签名需要兼容基类的调用方式，
    包括 tiktoken 风格的 disallowed_special 等 kwargs（这里直接忽略）。
    """

    def encode(self, content, **_kwargs) -> List[int]:
        """根据启发式估算 token 数，返回长度等于估算值的伪 token id 列表。"""
        if not content:
            return []
        text = content if isinstance(content, str) else str(content)
        cjk_count = len(_CJK_RE.findall(text))
        other_count = len(text) - cjk_count
        estimated = int(cjk_count / _CJK_CHARS_PER_TOKEN + other_count / _OTHER_CHARS_PER_TOKEN) + 1
        # 返回 list(range(n)) 而非 [0]*n，避免 decode 端误解为同一 token 重复
        return list(range(estimated))

    def decode(self, _tokens) -> str:
        """LightRAG 极少调用 decode；返回空串占位即可。"""
        return ""


class OfflineTokenizer(Tokenizer):
    """
    纯 Python 离线分词器。

    继承 LightRAG 的 Tokenizer 基类以保持接口兼容（encode/decode/model_name），
    内部委派给 _HeuristicCore，整个过程不导入 tiktoken、不触发任何网络请求。
    """

    def __init__(self) -> None:
        super().__init__(model_name="offline-heuristic", tokenizer=_HeuristicCore())

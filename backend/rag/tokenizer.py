"""
离线分词器：替代 tiktoken，避免 o200k_base 词表远程下载

背景
----
LightRAG 默认使用 TiktokenTokenizer（tiktoken.encoding_for_model("gpt-4o-mini")），
首次调用会从 https://openaipublic.blob.core.windows.net/encodings/o200k_base.tiktoken
下载词表文件。国内网络环境下该域名 SSL 握手失败（SSLEOFError），导致知识库
初始化时报错。

方案
----
实现一个**字符级可逆**分词器（OfflineTokenizer）：
  - encode(text) = [ord(c) for c in text]   —— 每个字符一个 token，token id 即 Unicode code point
  - decode(tokens) = "".join(chr(t) for t in tokens)   —— 完全可逆

为什么必须可逆：
  LightRAG 的 chunker（chunking_by_token_size）在分块时会调
  tokenizer.decode(_tokens[start:end_token]) 重建每块文本。
  如果 decode 返回空串，chunk 内容就是空的，pipeline 会丢弃所有 chunk，
  导致 "Set of coroutines/Futures is empty." 错误，文档 status 变 failed。

代价：
  len(encode(text)) == len(text)（字符数），比真实 token 数偏大约 1.5 倍
  （CJK 经验值 1.5 字符/token）。LightRAG 默认 chunk_token_size=1200，
  会变成约 1200 字符/块。这只影响分块粒度（块偏大），不影响功能正确性。
  如需更小分块，可在 LightRAG 构造时调小 chunk_token_size（本次不动）。

启用方式
--------
在 backend/rag/service.py 构造 LightRAG 时传入 tokenizer=OfflineTokenizer()。
受 config.RAG_OFFLINE_TOKENIZER 开关控制（默认开启，适合国内部署）。
"""
from __future__ import annotations

from typing import List

from lightrag.utils import Tokenizer


class _CharCodePointCore:
    """
    字符级可逆分词核心。

    作为 Tokenizer 基类内部的 tokenizer 属性使用（基类会把 encode/decode
    委托给 self.tokenizer），方法签名兼容 tiktoken 风格的 kwargs（直接忽略）。

    设计：encode 把每个字符映射为它的 Unicode code point，decode 反向还原。
    这样 LightRAG 的 chunker 切 token 等价于切字符，内容可完美重建。
    """

    def encode(self, content, **_kwargs) -> List[int]:
        """
        把文本编码为 token id 列表。

        每个字符 → 它的 Unicode code point（int）。
        - 空文本返回 []
        - len(返回值) == len(text)，与字符一一对应
        """
        if not content:
            return []
        text = content if isinstance(content, str) else str(content)
        return [ord(c) for c in text]

    def decode(self, tokens) -> str:
        """
        把 token id 列表解码回文本。

        反向操作：每个 token id → chr(id) → 拼接。
        LightRAG 的 chunker 用它重建分块后的文本，必须可逆。
        非法 code point（超出 0x10FFFF）跳过，避免 chr() 抛错。
        """
        if not tokens:
            return ""
        chars = []
        for t in tokens:
            try:
                chars.append(chr(int(t)))
            except (ValueError, OverflowError):
                # 非法 code point，跳过（不应出现，但防御性处理）
                continue
        return "".join(chars)


class OfflineTokenizer(Tokenizer):
    """
    纯 Python 离线分词器（字符级可逆）。

    继承 LightRAG 的 Tokenizer 基类以保持接口兼容（encode/decode/model_name），
    内部委派给 _CharCodePointCore，整个过程不导入 tiktoken、不触发任何网络请求。
    """

    def __init__(self) -> None:
        super().__init__(model_name="offline-charcode", tokenizer=_CharCodePointCore())

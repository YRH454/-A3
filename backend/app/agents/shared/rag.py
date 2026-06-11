"""RAG 检索层 — 真实搜索 + NotebookLM 式内容合成

支持后端:
  - Perplexity API (推荐，学术搜索+实时信息)
  - SerpAPI (通用网页搜索)
  - 本地教材库（向量检索，预留）
"""

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# ─── 数据模型 ──────────────────────────────────────────

@dataclass
class SearchResult:
    title: str
    snippet: str
    url: str = ""
    source: str = ""
    relevance_score: float = 0.0


@dataclass
class RetrievalContext:
    query: str
    results: list[SearchResult] = field(default_factory=list)
    source_description: str = ""

    def to_prompt_text(self, max_results: int = 5) -> str:
        """将检索结果格式化为可注入 LLM prompt 的文本"""
        if not self.results:
            return ""

        lines = [f"## 检索结果（来源：{self.source_description}）"]
        for i, r in enumerate(self.results[:max_results], 1):
            lines.append(f"\n### {i}. {r.title}")
            lines.append(f"来源: {r.url or r.source}")
            lines.append(f"摘要: {r.snippet}")
        return "\n".join(lines)


# ─── 搜索后端 ──────────────────────────────────────────

class SearchBackend:
    """搜索后端基类"""

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        raise NotImplementedError


class PerplexityBackend(SearchBackend):
    """Perplexity API — 实时学术搜索，自带引用

    注意: Perplexity 的 API 基于 OpenAI 兼容格式。
    """

    def __init__(self, api_key: str = "", base_url: str = ""):
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY", "")
        self.base_url = base_url or os.getenv("PERPLEXITY_BASE_URL", "https://api.perplexity.ai")
        self._client = httpx.Client(timeout=30) if self.api_key else None

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        if not self._client:
            logger.warning("Perplexity API key 未配置，跳过搜索")
            return []

        try:
            resp = self._client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "sonar-pro",
                    "messages": [
                        {"role": "system", "content": "搜索学术资源并返回结果。每个结果包含标题、摘要和链接。"},
                        {"role": "user", "content": f"搜索: {query}\n请返回{top_k}个最相关的学术资源。"},
                    ],
                    "max_tokens": 2000,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return self._parse_results(content, top_k)
        except Exception as e:
            logger.warning(f"Perplexity 搜索失败: {e}")
            return []

    def _parse_results(self, content: str, top_k: int) -> list[SearchResult]:
        """尽力从 Perplexity 返回内容中提取结构化结果"""
        results = []
        # 简单的按段落分割，提取标题行
        paragraphs = content.split("\n\n")
        for para in paragraphs[:top_k]:
            lines = para.strip().split("\n")
            if not lines:
                continue
            title = lines[0].lstrip("#-• ").strip()[:200]
            snippet = "\n".join(lines[1:])[:500] if len(lines) > 1 else ""
            results.append(SearchResult(
                title=title, snippet=snippet, source="Perplexity"
            ))
        return results


class SerpAPIBackend(SearchBackend):
    """SerpAPI — Google 搜索"""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY", "")
        self._client = httpx.Client(timeout=15) if self.api_key else None

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        if not self._client:
            logger.warning("SerpAPI key 未配置，跳过搜索")
            return []

        try:
            resp = self._client.get("https://serpapi.com/search", params={
                "q": query,
                "api_key": self.api_key,
                "num": top_k,
                "engine": "google",
            })
            resp.raise_for_status()
            data = resp.json()
            results = []
            for r in data.get("organic_results", [])[:top_k]:
                results.append(SearchResult(
                    title=r.get("title", ""),
                    snippet=r.get("snippet", ""),
                    url=r.get("link", ""),
                    source="Google",
                ))
            return results
        except Exception as e:
            logger.warning(f"SerpAPI 搜索失败: {e}")
            return []


class SemanticScholarBackend(SearchBackend):
    """Semantic Scholar API — 免费学术论文搜索，无需 API Key

    文档: https://api.semanticscholar.org/api-docs/
    速率限制: 无 API Key 时 1 req/s，建议批量使用。
    """

    BASE = "https://api.semanticscholar.org/graph/v1"

    def __init__(self):
        self._client = httpx.Client(
            timeout=15,
            headers={"User-Agent": "Scholarium/1.0 (Learning Platform)"},
        )

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        try:
            resp = self._client.get(
                f"{self.BASE}/paper/search",
                params={
                    "query": query,
                    "limit": top_k,
                    "fields": "title,abstract,url,year,venue",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            results = []
            for paper in data.get("data", [])[:top_k]:
                title = paper.get("title", "")
                year = paper.get("year", "")
                venue = paper.get("venue", "")
                title_line = f"{title} ({year})" if year else title
                if venue:
                    title_line += f" — {venue}"

                abstract = paper.get("abstract") or ""
                url = paper.get("url") or f"https://www.semanticscholar.org/paper/{paper.get('paperId','')}"

                results.append(SearchResult(
                    title=title_line,
                    snippet=abstract[:500] if abstract else "无摘要",
                    url=url,
                    source="Semantic Scholar",
                ))
            return results
        except Exception as e:
            logger.warning(f"Semantic Scholar 搜索失败: {e}")
            return []


class CoreAPIBackend(SearchBackend):
    """CORE API — 免费开放获取论文搜索，无需 API Key

    文档: https://api.core.ac.uk/docs/
    """

    BASE = "https://api.core.ac.uk/v3/search/works/"

    def __init__(self):
        self._client = httpx.Client(
            timeout=15,
            headers={"User-Agent": "Scholarium/1.0 (Learning Platform)"},
        )

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        try:
            resp = self._client.get(
                self.BASE,
                params={
                    "q": query,
                    "limit": top_k,
                    "scroll": "false",
                },
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()
            results = []
            for work in data.get("results", [])[:top_k]:
                title = work.get("title", "")
                abstract = work.get("abstract", "") or ""
                download_url = work.get("downloadUrl", "") or work.get("sourceFulltextUrls", [""])[0] or ""

                results.append(SearchResult(
                    title=title,
                    snippet=abstract[:500] if abstract else "无摘要",
                    url=download_url or f"https://core.ac.uk/search?q={query}",
                    source="CORE",
                ))
            return results
        except Exception as e:
            logger.warning(f"CORE 搜索失败: {e}")
            return []


# ─── 检索编排 ──────────────────────────────────────────

# 搜索后端注册（按优先级排列）
_SEARCH_BACKENDS: list[SearchBackend] = []


def _init_backends():
    """延迟初始化搜索后端。免费后端始终可用。"""
    global _SEARCH_BACKENDS
    if _SEARCH_BACKENDS:
        return

    # 免费学术搜索（无需 API Key，始终可用）
    _SEARCH_BACKENDS.append(SemanticScholarBackend())
    _SEARCH_BACKENDS.append(CoreAPIBackend())

    # 付费搜索（需 API Key，优先级更高）
    perplexity_key = os.getenv("PERPLEXITY_API_KEY", "")
    serpapi_key = os.getenv("SERPAPI_API_KEY", "")

    if perplexity_key:
        _SEARCH_BACKENDS.insert(0, PerplexityBackend(perplexity_key))
    if serpapi_key:
        _SEARCH_BACKENDS.insert(0, SerpAPIBackend(serpapi_key))

    logger.info(f"搜索后端就绪: {[b.__class__.__name__ for b in _SEARCH_BACKENDS]}")


def search_documents(
    query: str,
    top_k: int = 5,
    backend: Optional[SearchBackend] = None,
) -> RetrievalContext:
    """搜索文档/资源，返回检索上下文。

    如果指定 backend，仅使用该后端；
    否则按优先级尝试所有已配置的后端。
    """
    _init_backends()

    backends = [backend] if backend else _SEARCH_BACKENDS
    all_results: list[SearchResult] = []
    source_desc = "网络搜索"

    for be in backends:
        try:
            results = be.search(query, top_k)
            if results:
                all_results = results
                source_desc = be.__class__.__name__.replace("Backend", "")
                break
        except Exception as e:
            logger.warning(f"搜索后端 {be.__class__.__name__} 异常: {e}")

    return RetrievalContext(
        query=query,
        results=all_results,
        source_description=source_desc,
    )


def inject_context(prompt: str, context: RetrievalContext, max_results: int = 5) -> str:
    """将检索结果注入提示词"""
    context_text = context.to_prompt_text(max_results)
    if not context_text:
        return prompt
    return prompt + "\n\n" + context_text

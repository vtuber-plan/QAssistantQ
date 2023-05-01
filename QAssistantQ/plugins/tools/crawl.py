"""Tool for the Crawl API."""

import re
from pydantic import Field

from langchain.tools.base import BaseTool

import requests

from bs4 import BeautifulSoup


class CrawlTool(BaseTool):
    """Tool that adds the capability to crawl website."""

    name = "Crawl Tool"
    description = (
        "A wrapper around web page crawler. "
        "Useful for when you need to crawl the text of page. "
        "Input should be a valid url."
    )

    def _run(self, query: str) -> str:
        """Use the tool."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        response = requests.get(query, headers=headers)

        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

        # 获取所有标题标签
        titles = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p'])

        # 根据标签顺序排序
        titles_sorted = sorted(titles, key=lambda tag: tag.name)

        # 提取标题文本并合并为字符串
        summary = ' '.join([title.text for title in titles_sorted])
        summary = summary.replace("\n", ".")
        summary = re.sub(r'\s+', ' ', summary)
        return summary[:1000]

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("MathTool does not support async")

"""Tool for the direct output API."""

from pydantic import Field

from langchain.tools.base import BaseTool


class DirectTool(BaseTool):
    """Tool that adds the capability to direct output question."""

    name = "Direct Output Tool"
    description = (
        "A wrapper around passby function. "
        "Useful for when the question belongs to chit chat and can be answered directly without tools. "
        "Input should be the original question query."
    )

    def _run(self, query: str) -> str:
        """Use the tool."""
        return query

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("DirectTool does not support async")

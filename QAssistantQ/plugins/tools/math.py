"""Tool for the Math API."""

from pydantic import Field

from langchain.tools.base import BaseTool

class MathTool(BaseTool):
    """Tool that adds the capability to evaluate math expressions."""

    name = "Math Tool"
    description = (
        "A wrapper around Math. "
        "Useful for when you need to evaluate a math expression. "
        "Input should be a valid python expression."
    )

    def _run(self, query: str) -> str:
        """Use the tool."""
        return eval(query)

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("MathTool does not support async")

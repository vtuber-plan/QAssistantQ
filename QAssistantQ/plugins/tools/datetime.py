"""Tool for the datetime API."""

from pydantic import Field

from langchain.tools.base import BaseTool

import datetime

class DatetimeTool(BaseTool):
    """Tool that adds the capability to get current date and time."""

    name = "Datetime Tool"
    description = (
        "A wrapper around Python datetime. "
        "Useful for when you need to get current date or time. "
        "Input should be a valid python strftime parameter."
    )

    def _run(self, query: str) -> str:
        """Use the tool."""
        return datetime.datetime.now().strftime(query)

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("DatetimeTool does not support async")

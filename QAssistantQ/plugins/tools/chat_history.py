"""Tool for the Chat History API."""

from pydantic import Field

from langchain.tools.base import BaseTool

import random

class ChatHistoryTool(BaseTool):
    """Tool that adds the capability to search in chat history."""

    name = "Chat History Tool"
    description = (
        "A wrapper around chat history. "
        "Useful for when you need to search in chat history. "
        "Input should be some words with blanks to search."
    )

    def _run(self, query: str) -> str:
        """Use the tool."""
        with open("qaq.log", "r", encoding="utf-8") as f:
            lines = f.readlines()
        words = query.split()
        out = []
        for line in lines:
            if all([w in line for w in words]):
                out.append(line)
        random.shuffle(out)
        return "\n".join(out[:20])

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("MathTool does not support async")

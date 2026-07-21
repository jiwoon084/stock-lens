from typing import Literal

from pydantic import BaseModel

ChecklistTag = Literal["positive", "negative", "earnings", "caution", "neutral"]


class ChecklistItem(BaseModel):
    id: str
    tag: ChecklistTag
    headline: str
    description: str
    source_count: int
    url: str = ""


class ChecklistResponse(BaseModel):
    ticker: str
    date: str
    total_article_count: int
    items: list[ChecklistItem]

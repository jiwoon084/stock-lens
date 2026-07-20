from typing import Optional, TypedDict


class AssistantState(TypedDict):
    """종목 Q&A 챗봇 LangGraph 상태 (스켈레톤, 노드 구현 시 확정)"""

    messages: list
    corp_name: Optional[str]
    retrieved_docs: list
    answer: Optional[str]
    sources: list

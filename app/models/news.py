from pydantic import BaseModel
from typing import Optional

class NewsItem(BaseModel):
    """
    新闻数据模型 (Data Schema)
    定义了一条新闻必须包含哪些字段
    """
    title: str
    link: str
    source: str
    summary: str
    publish_date: Optional[str] = None
    
    # 以后我们有了 AI 分析，会填充下面这些字段
    category: Optional[str] = "Uncategorized"
    score: int = 0
    ai_summary: Optional[str] = None
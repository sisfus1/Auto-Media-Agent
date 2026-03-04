import feedparser
from typing import List
from app.core.config import settings  # 引用刚才写的配置
from app.models.news import NewsItem  # 引用刚才写的数据模型

class NewsCrawler:
    def __init__(self):
        self.sources = settings.RSS_SOURCES

    def fetch_all(self) -> List[NewsItem]:
        """
        遍历所有 RSS 源，抓取并清洗数据
        """
        print(f"🕵️  Crawler Service Started: 正在扫描 {len(self.sources)} 个资讯源...")
        
        all_news = []
        
        for source in self.sources:
            try:
                # 关键：加上 agent 参数，伪装成浏览器，否则有些网站会拒绝访问
                feed = feedparser.parse(
                    source["url"], 
                    agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                )
                
                # 检查是否成功抓取
                if feed.bozo:
                    print(f"⚠️  [警告] {source['name']} 解析可能存在问题: {feed.bozo_exception}")
                
                # 提取前 5 条
                for entry in feed.entries[:5]:
                    # 数据清洗 (ETL中的 Transform)
                    # 有些 RSS 的摘要在 'summary' 里，有些在 'description' 里
                    raw_summary = getattr(entry, "summary", getattr(entry, "description", ""))
                    
                    # 简单过滤：如果标题里不包含 AI 关键词 (针对 HN 这种大杂烩)
                    if source["name"] == "Hacker News":
                        keywords = ["ai", "gpt", "llm", "model", "cursor"]
                        if not any(k in entry.title.lower() for k in keywords):
                            continue

                    # 构建标准模型对象
                    item = NewsItem(
                        title=entry.title,
                        link=entry.link,
                        source=source["name"],
                        summary=raw_summary[:200] + "..." if len(raw_summary) > 200 else raw_summary,
                        publish_date=getattr(entry, "published", "")
                    )
                    all_news.append(item)
                    
            except Exception as e:
                print(f"❌ [错误] 抓取 {source['name']} 失败: {e}")
                
        print(f"✅ Crawler Service Finished: 共收集到 {len(all_news)} 条有效资讯")
        return all_news
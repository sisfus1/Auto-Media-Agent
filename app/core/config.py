import os
from dotenv import load_dotenv

# 1. 强制加载 .env 文件
load_dotenv()

class Settings:
    # 基础配置
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Auto-Media-Agent")
    VERSION: str = os.getenv("VERSION", "0.1.0")
    
    # AI 模型配置
    DEEPSEEK_API_KEY: str = os.getenv("OPENAI_API_KEY")
    DEEPSEEK_BASE_URL: str = os.getenv("OPENAI_BASE_URL")
    
    # 资讯源列表 (可以在这里统一管理)
    RSS_SOURCES: list = [
        {"name": "OpenAI", "url": "https://openai.com/blog/rss.xml"},
        {"name": "The Verge", "url": "https://www.theverge.com/rss/ai/index.xml"},
        {"name": "Hacker News", "url": "https://news.ycombinator.com/rss"},
        {"name": "MIT Tech Review", "url": "https://www.technologyreview.com/feed/"},
    ]

# 实例化配置对象，方便其他文件直接引用
settings = Settings()
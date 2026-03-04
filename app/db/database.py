import sqlite3
import datetime
from typing import List
from app.models.news import NewsItem

DB_NAME = "news_data.db"

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.cursor = self.conn.cursor()
        self._init_tables()

    def _init_tables(self):
        """初始化数据库表结构"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                link TEXT UNIQUE,  -- 链接必须唯一，用于去重
                source TEXT,
                summary TEXT,
                publish_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def save_news_batch(self, news_list: List[NewsItem]) -> int:
        """批量保存新闻，返回成功保存的条数"""
        count = 0
        for item in news_list:
            try:
                self.cursor.execute('''
                    INSERT INTO news (title, link, source, summary, publish_date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (item.title, item.link, item.source, item.summary, item.publish_date))
                count += 1
            except sqlite3.IntegrityError:
                # 如果链接重复 (IntegrityError)，则跳过
                continue
            except Exception as e:
                print(f"❌ 数据库写入错误: {e}")
        
        self.conn.commit()
        return count

    def get_recent_news(self, limit=10):
        """获取最近入库的新闻"""
        self.cursor.execute('SELECT title, summary, link FROM news ORDER BY created_at DESC LIMIT ?', (limit,))
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()
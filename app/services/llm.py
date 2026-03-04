import json
from openai import AsyncOpenAI  # 【核心修改 1】导入异步客户端
from app.core.config import settings

class LLMService:
    def __init__(self):
        # 【核心修改 2】初始化 AsyncOpenAI
        self.client = AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL
        )

    # 【核心修改 3】函数定义前加上 async，使其变为协程函数
    async def generate_daily_report(self, news_text_list: list) -> dict:
        """
        输入：新闻列表文本
        输出：结构化的 JSON 日报
        """
        print("🧠 Brain Service: 正在调用 DeepSeek 进行深度思考...")

        if not news_text_list:
            return {"error": "没有足够的新闻数据"}

        content_block = "\n".join(news_text_list)
        
        prompt = f"""
        你是一个专业的科技主编。请分析以下今日抓取到的 AI 新闻，并生成一份 JSON 格式的日报。

        【新闻源数据】：
        {content_block}

        【输出要求】：
        1. 请挑选出最重要的 3-5 条新闻。
        2. 返回格式必须是纯 JSON，不要包含 markdown 标记。
        3. JSON 结构如下：
        {{
            "date": "YYYY-MM-DD",
            "top_news": [
                {{
                    "title": "新闻标题(中文)",
                    "summary": "一句话核心摘要(中文)",
                    "tag": "分类(如: 模型/应用/行业)",
                    "score": 8 (热度评分1-10)
                }}
            ],
            "editor_comment": "一句话整体点评"
        }}
        """

        try:
            # 【核心修改 4】在网络请求前加上 await，把控制权交还给事件循环
            response = await self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个输出 JSON 格式的 AI 助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={ 'type': 'json_object' }
            )
            
            result = response.choices[0].message.content
            if result.startswith("```json"):
                result = result.replace("```json", "").replace("```", "")
                
            return json.loads(result)
            
        except Exception as e:
            print(f"❌ LLM 调用失败: {e}")
            return {"error": str(e)}
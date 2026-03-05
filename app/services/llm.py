import json
from openai import AsyncOpenAI  # 【核心修改 1】导入异步客户端
from app.core.config import settings

class LLMService:
    def __init__(self):
        # 【核心修改 2】初始化 AsyncOpenAI
        self.client = AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            timeout=120.0
        )

    # 【核心修改 3】函数定义前加上 async，使其变为协程函数
# 注意参数列表里多了一个 historical_context
    async def generate_daily_report(self, news_text_list: list, historical_context: str = "") -> dict:
        """
        输入：今日新闻列表、历史相关新闻上下文
        输出：结构化的 JSON 日报
        """
        print("🧠 Brain Service: 正在调用 DeepSeek 进行深度思考 (已启用 RAG 记忆增强)...")

        if not news_text_list:
            return {"error": "没有足够的新闻数据"}

        content_block = "\n".join(news_text_list)
        
        # 核心改造：在 Prompt 中引入历史记忆维度
        prompt = f"""
        你是一个专业的科技主编。请分析以下今日抓取到的 AI 新闻，并结合我提供的【历史背景库】，生成一份 JSON 格式的深度日报。

        【今日新闻源数据】：
        {content_block}

        【历史背景库 (记忆检索结果)】：
        {historical_context if historical_context else "暂无历史背景。"}

        【输出要求】：
        1. 请挑选出最重要的 3-5 条新闻。
        2. 在编写 summary (摘要) 时，请尽可能结合【历史背景库】中的信息，写出带有时间线或深度视角的连贯点评（例如：“继上周XX发布后，今日又...”）。
        3. 返回格式必须是纯 JSON，不要包含 markdown 标记。
        4. JSON 结构如下：
        {{
            "date": "YYYY-MM-DD",
            "top_news": [
                {{
                    "title": "新闻标题(中文)",
                    "summary": "一句话深度摘要(结合历史背景)",
                    "tag": "分类(如: 模型/应用/行业)",
                    "score": 8 
                }}
            ],
            "editor_comment": "一句话整体深度点评"
            "image_prompt": "A highly detailed, cinematic, cyberpunk style news studio background, high tech, glowing neon lights, 8k resolution, photorealistic" # 👈 【新增这一行】请根据今日新闻的主题，生成一句纯英文的 AI 绘画提示词，用于生成视频背景图，要求画面极具视觉冲击力。
        }}
        """

        try:
            response = await self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个输出 JSON 格式的资深 AI 科技主编。"},
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
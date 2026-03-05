import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv

# 确保加载 .env 文件中的环境变量
load_dotenv()

class LLMService:
    def __init__(self):
        print("🧠 神经元升级: 初始化 LangChain AI 大脑 (DeepSeek V3)...")
        
        # 1. 初始化 LangChain 的 ChatOpenAI 模型 (完美兼容 DeepSeek)
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            # 【修复】：直接从环境变量读取，如果没配 URL 则使用官方默认地址
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            timeout=120.0,
            max_retries=2, # 自带重试装甲，遇到网络闪断自动重试 2 次
            temperature=0.3,
            # 强制输出 JSON 模式
            model_kwargs={"response_format": {"type": "json_object"}} 
        )

    async def generate_daily_report(self, news_text_list: list, historical_context: str = "") -> dict:
        # ... 这里面剩下的代码完全保持不变 ...
        """
        使用 LangChain 链式调用生成日报
        """
        print("🧠 Brain Service: 正在使用 LangChain LCEL 链调用大模型 (已启用 RAG 记忆)...")

        if not news_text_list:
            return {"error": "没有足够的新闻数据"}

        content_block = "\n".join(news_text_list)
        
        # 2. 构建结构化的 Prompt Template (模板)
        # LangChain 允许我们用大括号 {变量名} 优雅地挖坑，稍后再填入数据
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "你是一个专业的科技主编。必须严格输出符合要求的 JSON 格式。"),
            ("user", """
            请分析以下今日抓取到的 AI 新闻，并结合我提供的【历史背景库】，生成一份 JSON 格式的深度日报。

            【今日新闻源数据】：
            {content_block}

            【历史背景库 (记忆检索结果)】：
            {historical_context}

            【输出要求】：
            1. 请挑选出最重要的 3-5 条新闻。
            2. 在编写 summary (摘要) 时，请尽可能结合【历史背景库】中的信息，写出带有时间线或深度视角的连贯点评。
            3. 返回格式必须是纯 JSON。
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
                "editor_comment": "一句话整体深度点评",
                "image_prompt": "A highly detailed, cinematic, cyberpunk style news studio background, high tech, glowing neon lights, 8k resolution, photorealistic"
            }}
            """)
        ])

        # 3. 初始化 JSON 输出解析器
        # 这个神器会自动帮我们把大模型返回的 JSON 字符串转成 Python 字典，
        # 甚至会自动剥离外面包裹的 ```json 标记，再也不用我们手动去 replace 了！
        parser = JsonOutputParser()

        # 4. 👑 见证奇迹的时刻：构建 LCEL (LangChain 表达式语言) 链
        # 就像工厂的流水线一样：填入变量的提示词 -> 流入大模型 -> 流入解析器
        chain = prompt_template | self.llm | parser

        try:
            # 5. 异步执行整条链 (ainvoke 代表 Async Invoke)
            result = await chain.ainvoke({
                "content_block": content_block,
                "historical_context": historical_context if historical_context else "暂无关联历史。"
            })
            return result
            
        except Exception as e:
            print(f"❌ LangChain 调用链断裂: {e}")
            return {"error": str(e)}
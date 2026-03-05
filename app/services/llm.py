import os
import json
from datetime import datetime  # 👈 【核心修复 1】：引入系统时间模块
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
        """
        使用 LangChain 链式调用生成日报
        """
        print("🧠 Brain Service: 正在使用 LangChain LCEL 链调用大模型 (已启用 RAG 记忆)...")

        if not news_text_list:
            return {"error": "没有足够的新闻数据"}

        content_block = "\n".join(news_text_list)
        
        # 👈 【核心修复 2】：获取服务器当前的真实时间锚点
        today_str = datetime.now().strftime("%Y年%m月%d日")
        print(f"🕒 注入时间钢印: {today_str}")
        
        # 2. 构建结构化的 Prompt Template (模板)
        # LangChain 允许我们用大括号 {变量名} 优雅地挖坑，稍后再填入数据
        prompt_template = ChatPromptTemplate.from_messages([
    ("system", "你是一个专业的科技主编，拥有绝对精准的时间观念。你必须严格按系统给定的当天时间进行新闻梳理，绝不能使用过时的记忆，并严格输出 JSON 格式。"),
    ("user", """
    【系统强制时间锚点】：今天是 {current_date}。请务必抛弃你内在的训练时间记忆，完全基于今天的时间线进行播报。

    请分析以下由实时搜索引擎抓取到的 AI 新闻，并结合【历史背景库】，生成一份 JSON 格式的深度日报。

    【今日实时新闻源数据】：
    {content_block}

    【历史背景库 (记忆检索结果)】：
    {historical_context}

    【输出要求】：
    1. 请挑选出最重要、最具前沿性的 3 条新闻。
    2. 在编写 summary 时，必须结合【历史背景库】进行对比或点评，体现出时间的推演（例如：“相比去年…”或“继上个月之后…”）。
    3. JSON 里的 date 字段，必须一字不差地填写为：{current_date}。
    4. 务必直接输出纯 JSON 字符串，不要带 ```json 这种 Markdown 标记，不要有任何多余的废话。
    5. JSON 结构如下：
    {{
        "date": "{current_date}",
        "top_news": [
            {{
                "title": "新闻标题(中文)",
                "summary": "一句话深度摘要(结合历史背景，体现行业洞察)",
                "tag": "分类(如: 模型/应用/硬件/政策)",
                "score": 8 
            }}
        ],
        "editor_comment": "一句话整体深度点评，并在最后带上类似'感谢收看今天的 AI 资讯'的结束语",
        "image_prompt": "A highly detailed, cinematic, cyberpunk style news studio background, high tech, glowing neon lights, 8k resolution, photorealistic"
    }}
    """)
])

        # 3. 初始化 JSON 输出解析器
        parser = JsonOutputParser()

        # 4. 👑 见证奇迹的时刻：构建 LCEL (LangChain 表达式语言) 链
        chain = prompt_template | self.llm | parser

        try:
            # 5. 异步执行整条链 (ainvoke 代表 Async Invoke)
            result = await chain.ainvoke({
                "current_date": today_str,  # 👈 【核心修复 3】：在触发大模型时，将时间变量填入提示词的坑位里
                "content_block": content_block,
                "historical_context": historical_context if historical_context else "暂无关联历史。"
            })
            return result
            
        except Exception as e:
            print(f"❌ LangChain 调用链断裂: {e}")
            return {"error": str(e)}
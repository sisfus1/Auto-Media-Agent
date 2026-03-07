import os
import asyncio
import shutil
from datetime import datetime
from celery import Celery
import redis

# 导入我们的服务
from app.db.database import DatabaseManager
from app.db.vector_db import VectorDBManager
from app.services.llm import LLMService
from app.services.media import MediaService
from app.services.subtitle import get_subtitle_segments, add_subtitles_to_video

# 1. 初始化 Celery 引擎与 Redis 客户端
celery_app = Celery(
    'video_worker',
    broker='redis://127.0.0.1:6379/0',
    backend='redis://127.0.0.1:6379/0'
)

redis_client = redis.Redis(host='127.0.0.1', port=6379, db=0, decode_responses=True)

OUTPUT_DIR = "test_videos"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@celery_app.task(name="generate_video_task")
def run_video_generation_pipeline(task_id: str):
    """独立的分布式多模态渲染后厨"""
    redis_client.set(task_id, "RUNNING")
    print(f"\n[Worker 节点] 🚀 接收到订单 [{task_id}]，后厨开始运转...")
    
    try: # <--- 【最外层兜底网：保证 Worker 永不崩溃】
        db = DatabaseManager()
        llm = LLMService()
        media = MediaService()
        vector_db = VectorDBManager()

        current_time = datetime.now().strftime("%Y%m%d%H%M")
        base_filename = f"{current_time}_{task_id[:4]}"
        
        audio_file_path = os.path.join(OUTPUT_DIR, f"{base_filename}.mp3")
        bg_image_path = os.path.join(OUTPUT_DIR, f"{base_filename}.jpg")
        video_file_path = os.path.join(OUTPUT_DIR, f"{base_filename}.mp4")

        # --- 实时网络情报局 ---
        from langchain_community.tools import DuckDuckGoSearchResults
        current_date_str = datetime.now().strftime("%Y年%m月%d日")
        print(f"[{task_id}] ⏳ 正在为 Agent 注入当前时间锚点: {current_date_str}")
        
        search_tool = DuckDuckGoSearchResults()
        search_query = f"{current_date_str} 人工智能 AI 大模型 OpenAI 最新重大新闻"
        print(f"[{task_id}] 🌐 正在全网搜寻最新情报: {search_query}")
        
        try:
            live_news_str = search_tool.run(search_query)
            news_for_ai = [
                f"【系统强制指令】：今天是 {current_date_str}。请务必在开场白中准确播报今天的日期。",
                f"【今日全网最新实时资讯抓取结果】：\n{live_news_str}"
            ]
        except Exception as e:
            redis_client.set(task_id, f"FAILED: 实时搜索引擎故障 - {str(e)}")
            return

        # --- 动态记忆镌刻 ---
        news_for_vector = [{
            "id": f"search_{task_id}", 
            "text": live_news_str, 
            "metadata": {"source": "duckduckgo", "date": current_date_str}
        }]
        vector_db.add_news_to_vector_db(news_for_vector)

        query_keyword = "AI 人工智能 大模型 突破"
        historical_docs = vector_db.search_related_news(query_text=query_keyword, n_results=3)
        historical_context = "\n".join(historical_docs) if historical_docs else "暂无关联历史。"

        # --- LLM 大脑推演 ---
        print(f"[{task_id}] 🤖 大模型深度思考中...")
        report = asyncio.run(llm.generate_daily_report(news_for_ai, historical_context=historical_context))
        
        if "error" in report:
            redis_client.set(task_id, f"FAILED: AI 生成失败 - {report['error']}")
            return
        
        script_lines = [f"大家好，今天是{report.get('date', '今天')}。"]
        for item in report.get('top_news', []):
            script_lines.append(item.get('title', ''))
            script_lines.append(item.get('summary', ''))
        script_lines.append(report.get('editor_comment', '感谢收看。'))
        script = "\n".join(script_lines)
        image_prompt = report.get("image_prompt", "A high tech news studio, abstract data flow, 8k resolution, cinematic lighting")
        
        # --- TTS 与生图引 ---
        print(f"[{task_id}] 🎙️ 正在调用 TTS...")
        temp_audio = media.generate_audio(script)
        if not temp_audio or not os.path.exists(temp_audio):
            redis_client.set(task_id, "FAILED: 语音生成失败")
            return
        shutil.move(temp_audio, audio_file_path)

        print(f"[{task_id}] 🎨 正在调用云端 FLUX...")
        generated_bg = media.generate_background_image(image_prompt, save_path=bg_image_path)
        
        # --- 终极视频合成阵列 (含字幕切割) ---
        # --- 终极视频合成阵列 (像素级字幕渲染) ---
        print(f"[{task_id}] 🎬 剪辑引擎合成中...")
        from moviepy.editor import ImageClip, AudioFileClip, ColorClip
        
        try:
            audio_clip = AudioFileClip(audio_file_path)
            duration = audio_clip.duration
            
            # 1. 铺设底图 (视频背景)
            if generated_bg and os.path.exists(generated_bg):
                base_video = ImageClip(generated_bg).set_duration(duration)
            else:
                base_video = ColorClip(size=(1280, 720), color=(10, 20, 60), duration=duration)
            
            # 2. 呼叫 Whisper，只要时间轴数据，不要图片！
            segments = get_subtitle_segments(audio_file_path)
            
            # 3. 终极杀手锏：直接在底图的每一帧像素上强行画字！
            video_with_subs = add_subtitles_to_video(base_video, segments)
            
            # 4. 挂载音频
            final_video = video_with_subs.set_audio(audio_clip)
            
            # 5. 输出成品
            final_video.write_videofile(video_file_path, fps=24, logger=None)
            
            # 释放内存
            audio_clip.close()
            base_video.close()
            final_video.close()
            
            final_video_name = f"{base_filename}.mp4"
            redis_client.set(task_id, f"SUCCESS: http://127.0.0.1:8000/api/videos/{final_video_name}")
            print(f"[{task_id}] ✅ 任务大功告成！带精准字幕的高清视频已出炉！")
            
        except Exception as e:
            redis_client.set(task_id, f"ERROR: 视频渲染失败 - {str(e)}")
    except Exception as e: # <--- 【这就是你刚才不小心删掉的最外层兜底网】
        redis_client.set(task_id, f"ERROR: 系统严重异常 - {str(e)}")
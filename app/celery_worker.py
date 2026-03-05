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

# 1. 初始化 Celery 引擎与 Redis 客户端
# broker: 接收 FastAPI 任务的队列
# backend: 存储任务执行结果的地方
celery_app = Celery(
    'video_worker',
    broker='redis://127.0.0.1:6379/0',
    backend='redis://127.0.0.1:6379/0'
)

# 纯净的 Redis 客户端，用于更新我们自定义的业务状态
redis_client = redis.Redis(host='127.0.0.1', port=6379, db=0, decode_responses=True)

OUTPUT_DIR = "test_videos"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 2. 贴上魔法标签，将普通函数变为可被分布式调度的 Worker 任务
@celery_app.task(name="generate_video_task")
def run_video_generation_pipeline(task_id: str):
    """独立的分布式多模态渲染后厨"""
    # 【核心改造】：不再使用内存字典 TASK_STORE，而是直接把状态写进 Redis
    redis_client.set(task_id, "RUNNING")
    print(f"\n[Worker 节点] 🚀 接收到订单 [{task_id}]，后厨开始运转...")
    
    try:
        db = DatabaseManager()
        llm = LLMService()
        media = MediaService()
        vector_db = VectorDBManager()

        current_time = datetime.now().strftime("%Y%m%d%H%M")
        base_filename = f"{current_time}_{task_id[:4]}"
        
        audio_file_path = os.path.join(OUTPUT_DIR, f"{base_filename}.mp3")
        bg_image_path = os.path.join(OUTPUT_DIR, f"{base_filename}.jpg")
        video_file_path = os.path.join(OUTPUT_DIR, f"{base_filename}.mp4")

        recent_news = db.get_recent_news(limit=5)
        if not recent_news:
            redis_client.set(task_id, "FAILED: 数据库为空")
            return
            
        news_for_ai = [f"- {row[0]}: {row[1]}" for row in recent_news]
        
        news_for_vector = [{"id": str(row[0]), "text": f"标题: {row[0]} 内容: {row[1]}", "metadata": {"source": "daily_fetch"}} for row in recent_news]
        vector_db.add_news_to_vector_db(news_for_vector)

        query_keyword = recent_news[0][0] if recent_news else "AI"
        historical_docs = vector_db.search_related_news(query_text=query_keyword, n_results=3)
        historical_context = "\n".join(historical_docs) if historical_docs else "暂无关联历史。"

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
        
        print(f"[{task_id}] 🎙️ 正在调用 TTS...")
        temp_audio = media.generate_audio(script)
        if not temp_audio or not os.path.exists(temp_audio):
            redis_client.set(task_id, "FAILED: 语音生成失败")
            return
        shutil.move(temp_audio, audio_file_path)

        print(f"[{task_id}] 🎨 正在调用云端 FLUX...")
        generated_bg = media.generate_background_image(image_prompt, save_path=bg_image_path)
        
        print(f"[{task_id}] 🎬 剪辑引擎合成中...")
        from moviepy.editor import ImageClip, AudioFileClip, ColorClip
        
        try:
            audio_clip = AudioFileClip(audio_file_path)
            duration = audio_clip.duration
            
            if generated_bg and os.path.exists(generated_bg):
                video_clip = ImageClip(generated_bg).set_duration(duration)
            else:
                video_clip = ColorClip(size=(1280, 720), color=(10, 20, 60), duration=duration)
                
            final_video = video_clip.set_audio(audio_clip)
            final_video.write_videofile(video_file_path, fps=24, logger=None)
            
            audio_clip.close()
            video_clip.close()
            final_video.close()
            
            final_video_name = f"{base_filename}.mp4"
            # 【核心改造】：成功后将网络链接写回 Redis
            redis_client.set(task_id, f"SUCCESS: http://127.0.0.1:8000/api/videos/{final_video_name}")
            print(f"[{task_id}] ✅ 任务大功告成！")
            
        except Exception as e:
            redis_client.set(task_id, f"ERROR: 视频渲染失败 - {str(e)}")
            
    except Exception as e:
        redis_client.set(task_id, f"ERROR: 系统严重异常 - {str(e)}")
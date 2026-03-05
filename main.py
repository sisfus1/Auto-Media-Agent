import os
import json
import asyncio
import uuid
import shutil
from datetime import datetime
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# 导入我们自己写的服务模块
from app.db.database import DatabaseManager
from app.db.vector_db import VectorDBManager
from app.services.llm import LLMService
from app.services.media import MediaService

app = FastAPI()

# 配置 CORS，允许 Vue3 前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局任务字典，模拟 Redis 状态存储 (V1.0 暂留，未来升级 Celery)
TASK_STORE = {}

# 【新增】在程序启动时，自动在根目录创建一个 test_videos 文件夹
OUTPUT_DIR = "test_videos"
os.makedirs(OUTPUT_DIR, exist_ok=True)

class VideoTaskResponse(BaseModel):
    task_id: str
    status: str

def run_video_generation_pipeline(task_id: str):
    """真正的多模态视频生成后台流水线"""
    TASK_STORE[task_id] = "RUNNING"
    print(f"\n[{task_id}] 🚀 后台任务开始执行...")
    
    try:
        # 1. 初始化各项服务
        db = DatabaseManager()
        llm = LLMService()
        media = MediaService()
        vector_db = VectorDBManager()

        # 【核心改造：生成时间戳文件名及定义统一的输出路径】
        current_time = datetime.now().strftime("%Y%m%d%H%M")
        base_filename = f"{current_time}_{task_id[:4]}"
        
        audio_file_path = os.path.join(OUTPUT_DIR, f"{base_filename}.mp3")
        bg_image_path = os.path.join(OUTPUT_DIR, f"{base_filename}.jpg")
        video_file_path = os.path.join(OUTPUT_DIR, f"{base_filename}.mp4")

        # 2. 获取最新数据 (传统关系型数据库)
        recent_news = db.get_recent_news(limit=5)
        if not recent_news:
            TASK_STORE[task_id] = "FAILED: 数据库为空"
            return
            
        news_for_ai = [f"- {row[0]}: {row[1]}" for row in recent_news]
        
        # 3. 🧠 记忆检索 (RAG 核心逻辑)
        news_for_vector = []
        for row in recent_news:
            news_for_vector.append({
                "id": str(row[0]),
                "text": f"标题: {row[0]} 内容: {row[1]}",
                "metadata": {"source": "daily_fetch"}
            })
        vector_db.add_news_to_vector_db(news_for_vector)

        query_keyword = recent_news[0][0] if recent_news else "AI人工智能最新进展"
        historical_docs = vector_db.search_related_news(query_text=query_keyword, n_results=3)
        historical_context = "\n".join(historical_docs) if historical_docs else "暂无关联历史。"

        # 4. 🤖 调用大模型生成深度报告与【绘画提示词】
        print(f"[{task_id}] 🤖 大模型正在结合历史记忆深度思考...")
        report = asyncio.run(llm.generate_daily_report(news_for_ai, historical_context=historical_context))
        
        if "error" in report:
            TASK_STORE[task_id] = f"FAILED: AI 生成报告失败 - {report['error']}"
            return
        
        script_lines = [f"大家好，今天是{report.get('date', '今天')}。"]
        for item in report.get('top_news', []):
            script_lines.append(item.get('title', ''))
            script_lines.append(item.get('summary', ''))
        script_lines.append(report.get('editor_comment', '感谢收看。'))
        script = "\n".join(script_lines)

        image_prompt = report.get("image_prompt", "A high tech news studio, abstract data flow, 8k resolution, cinematic lighting")
        print(f"[{task_id}] 💡 提取到的画面灵感: {image_prompt}")

        # 5. 🎙️ 生成语音并归档
        print(f"[{task_id}] 🎙️ 正在调用 TTS 生成语音...")
        temp_audio = media.generate_audio(script)
        if not temp_audio or not os.path.exists(temp_audio):
            TASK_STORE[task_id] = "FAILED: 语音生成失败"
            return
            
        # 将根目录生成的音频移动到 test_videos 文件夹并重命名
        shutil.move(temp_audio, audio_file_path)

        # 6. 🎨 生成视觉背景 (FLUX) 直接保存到 test_videos
        print(f"[{task_id}] 🎨 正在调用云端 FLUX 模型生成动态视觉背景...")
        generated_bg = media.generate_background_image(image_prompt, save_path=bg_image_path)
        
        # 7. 🎬 最终视频合成 (MoviePy)
        print(f"[{task_id}] 🎬 剪辑引擎启动：将音频与视觉画面合成...")
        from moviepy.editor import ImageClip, AudioFileClip, ColorClip
        
        try:
            audio_clip = AudioFileClip(audio_file_path)
            duration = audio_clip.duration
            
            if generated_bg and os.path.exists(generated_bg):
                video_clip = ImageClip(generated_bg).set_duration(duration)
            else:
                print(f"[{task_id}] ⚠️ 生图失败，采用深蓝色纯色背景兜底。")
                video_clip = ColorClip(size=(1280, 720), color=(10, 20, 60), duration=duration)
                
            final_video = video_clip.set_audio(audio_clip)
            
            # 视频保存到新的时间戳路径
            final_video.write_videofile(video_file_path, fps=24, logger=None)
            
            audio_clip.close()
            video_clip.close()
            final_video.close()
            
            # 【核心改造：返回前端需要的网络链接，只拼文件名】
            final_video_name = f"{base_filename}.mp4"
            TASK_STORE[task_id] = f"SUCCESS: http://127.0.0.1:8000/api/videos/{final_video_name}"
            print(f"[{task_id}] ✅ 任务大功告成！完美视听成品路径: {os.path.abspath(video_file_path)}")
            
        except Exception as e:
            TASK_STORE[task_id] = f"ERROR: 视频渲染失败 - {str(e)}"
            print(f"[{task_id}] ❌ 视频合成异常: {e}")
            
    except Exception as e:
        TASK_STORE[task_id] = f"ERROR: 系统严重异常 - {str(e)}"
        print(f"[{task_id}] ❌ 流水线崩溃: {e}")

# --- API 路由定义 ---

@app.post("/api/tasks/generate_video", response_model=VideoTaskResponse)
async def create_video_task(background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())[:8]
    TASK_STORE[task_id] = "PENDING"
    background_tasks.add_task(run_video_generation_pipeline, task_id)
    return {"task_id": task_id, "status": "PENDING"}

@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    status = TASK_STORE.get(task_id, "NOT_FOUND")
    return {"task_id": task_id, "status": status}

@app.get("/api/videos/{filename}")
async def get_video(filename: str):
    """前端通过这个接口来获取并播放视频"""
    # 告诉 FastAPI 去 test_videos 文件夹里找视频
    file_path = os.path.join(os.getcwd(), OUTPUT_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="video/mp4")
    return {"error": "视频文件不存在"}
import os
import uuid
import asyncio # 确保有这个
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware # 【新增】导入跨域中间件
from pydantic import BaseModel
import uvicorn
from fastapi.responses import FileResponse
# (确保你之前已经导入了 os)

# 导入你的服务逻辑
from app.db.database import DatabaseManager
from app.services.llm import LLMService
from app.services.media import MediaService
from moviepy.editor import ColorClip

app = FastAPI(title="Auto-Media-Agent API", version="0.4.0")
# 【新增】配置 CORS，允许前端 5173 端口访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # 允许的请求来源
    allow_credentials=True,
    allow_methods=["*"], # 允许所有 HTTP 方法 (GET, POST 等)
    allow_headers=["*"], # 允许所有请求头
)

# --- 1. 定义数据模型 (Pydantic) ---
class VideoTaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

# 模拟一个内存中的任务状态字典（未来会被 Redis + Celery 替代）
TASK_STORE = {}

# --- 2. 核心业务逻辑封装为独立函数 ---
def run_video_generation_pipeline(task_id: str):
    """这是原本 main.py 中的核心逻辑，现在放到后台运行"""
    TASK_STORE[task_id] = "RUNNING"
    print(f"[{task_id}] 🚀 后台任务开始执行...")
    
    try:
        db = DatabaseManager()
        llm = LLMService()
        media = MediaService()

        # 1. 获取数据
        recent_news = db.get_recent_news(limit=5)
        if not recent_news:
            TASK_STORE[task_id] = "FAILED: 数据库为空"
            return
            
        news_for_ai = [f"- {row[0]}: {row[1]}" for row in recent_news]
        
        # 2. AI 分析
        report = asyncio.run(llm.generate_daily_report(news_for_ai))
        if "top_news" not in report:
            TASK_STORE[task_id] = "FAILED: AI 生成报告失败"
            return
            
        # 3. 拼接口播
        script = f"大家好，今天是{report.get('date')}。{report.get('editor_comment')}。"
        for i, item in enumerate(report['top_news']):
            script += f"第{i+1}条：{item['title']}。{item['summary']}。"
        
        # 4. 生成语音与视频
        audio_file = media.generate_audio(script)
        if not audio_file:
            TASK_STORE[task_id] = "FAILED: 语音生成失败"
            return

        bg_image = "background.jpg"
        if not os.path.exists(bg_image):
            ColorClip(size=(1280, 720), color=(10, 20, 60), duration=5).save_frame(bg_image, t=1)

        video_file = media.generate_video(audio_file, bg_image)
        if video_file:
            TASK_STORE[task_id] = f"SUCCESS: {os.path.abspath(video_file)}"
            print(f"[{task_id}] 🎉 视频生成完成！")
        else:
            TASK_STORE[task_id] = "FAILED: 视频合成失败"

    except Exception as e:
        TASK_STORE[task_id] = f"ERROR: {str(e)}"
    finally:
        # 这里应该做一些资源清理，比如 db.close() 等
        pass

# --- 3. API 路由定义 ---
@app.post("/api/tasks/generate_video", response_model=VideoTaskResponse)
async def create_video_task(background_tasks: BackgroundTasks):
    """
    触发视频生成的接口。它会立即返回一个 task_id，而真正的生成过程在后台进行。
    """
    # 生成唯一任务 ID
    task_id = str(uuid.uuid4())
    TASK_STORE[task_id] = "PENDING"
    
    # 将重任务放入 FastAPI 的后台队列中
    background_tasks.add_task(run_video_generation_pipeline, task_id)
    
    return VideoTaskResponse(
        task_id=task_id, 
        status="PENDING", 
        message="视频生成任务已提交后台处理"
    )

@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    """前端轮询查询任务状态的接口"""
    status = TASK_STORE.get(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task_id, "status": status}

@app.get("/api/videos/{filename}")
async def get_video(filename: str):
    """专门为前端提供视频流的接口"""
    # 因为我们的视频直接生成在项目根目录下，所以直接查 filename
    if not os.path.exists(filename):
        raise HTTPException(status_code=404, detail="视频文件未找到或已被删除")
    
    # 返回视频文件，FastAPI 会自动处理视频的拖拽缓冲(流式传输)
    return FileResponse(filename, media_type="video/mp4")

if __name__ == "__main__":
    # 启动命令: python api_main.py (或者 uvicorn api_main:app --reload)
    uvicorn.run(app, host="0.0.0.0", port=8000)
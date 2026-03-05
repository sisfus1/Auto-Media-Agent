import os
import uuid
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import redis

# 导入我们刚刚写好的 Celery 任务
from app.celery_worker import run_video_generation_pipeline

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUT_DIR = "test_videos"

# 连接到 Redis 订单墙
redis_client = redis.Redis(host='127.0.0.1', port=6379, db=0, decode_responses=True)

class VideoTaskResponse(BaseModel):
    task_id: str
    status: str

@app.post("/api/tasks/generate_video", response_model=VideoTaskResponse)
async def create_video_task():
    task_id = str(uuid.uuid4())[:8]
    
    # 1. 在 Redis 里贴上一个新订单状态
    redis_client.set(task_id, "PENDING")
    
    # 2. ⚡️ 将任务异步抛给 Celery 后厨！(.delay 是 Celery 的灵魂指令)
    run_video_generation_pipeline.delay(task_id)
    
    # 3. 毫秒级返回给前端，FastAPI 绝不阻塞！
    return {"task_id": task_id, "status": "PENDING"}

@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    # 前端轮询时，直接去 Redis 墙上查看最新状态
    status = redis_client.get(task_id)
    if not status:
        status = "NOT_FOUND"
    return {"task_id": task_id, "status": status}

@app.get("/api/videos/{filename}")
async def get_video(filename: str):
    file_path = os.path.join(os.getcwd(), OUTPUT_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="video/mp4")
    return {"error": "视频文件不存在"}
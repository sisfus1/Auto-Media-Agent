<template>
  <div class="container">
    <h1>🚀 Auto-Media-Agent 控制台</h1>
    <p class="subtitle">一键全自动抓取新闻、AI 生成文案并合成视频</p>

    <div class="card">
      <button 
        @click="startPipeline" 
        :disabled="status === 'RUNNING'"
        :class="{ 'btn-running': status === 'RUNNING' }"
      >
        {{ status === 'RUNNING' ? '视频生成中...' : '🎬 一键生成今日视频' }}
      </button>

      <div class="status-box" v-if="status !== 'IDLE'">
        <h3>系统状态:</h3>
        <p class="message">{{ message }}</p>
        
        <div class="progress-bar" v-if="status === 'RUNNING'">
          <div class="progress-inner"></div>
        </div>

        <div class="result" v-if="status === 'SUCCESS'">
          <video :src="videoUrl" controls autoplay class="video-player"></video>
          <p class="tip">📁 本地源文件：<code>{{ videoPath }}</code></p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const status = ref('IDLE') 
const message = ref('等待指令...')
const videoPath = ref('')
const videoUrl = ref('') // 新增：用于绑定的视频播放地址
let pollingInterval = null

const startPipeline = async () => {
  status.value = 'RUNNING'
  message.value = '正在向后台发送任务...'
  videoPath.value = ''
  videoUrl.value = ''
  
  try {
    const response = await axios.post('http://127.0.0.1:8000/api/tasks/generate_video')
    const taskId = response.data.task_id
    message.value = '任务已进入后台队列，正在执行 AI 抓取与分析...'
    
    pollingInterval = setInterval(() => {
      checkProgress(taskId)
    }, 2000)
    
  } catch (error) {
    status.value = 'ERROR'
    message.value = '❌ 请求失败，请检查后端服务是否启动。'
    console.error(error)
  }
}

const checkProgress = async (taskId) => {
  try {
    const response = await axios.get(`http://127.0.0.1:8000/api/tasks/${taskId}`)
    const currentStatus = response.data.status
    
    if (currentStatus.startsWith('SUCCESS')) {
      clearInterval(pollingInterval)
      status.value = 'SUCCESS'
      message.value = '🎉 视频渲染完毕，准备播放！'
      
      // 1. 获取绝对路径展示给用户看
      const rawPath = currentStatus.replace('SUCCESS: ', '')
      videoPath.value = rawPath
      
      // 2. 提取文件名，拼接成我们刚才写的后端 API 播放地址
      // 这里用正则兼容了 Windows的 \ 和 Mac/Linux的 /
      const filename = rawPath.split(/[\\/]/).pop() 
      videoUrl.value = `http://127.0.0.1:8000/api/videos/${filename}`
      
    } else if (currentStatus.startsWith('FAILED') || currentStatus.startsWith('ERROR')) {
      clearInterval(pollingInterval)
      status.value = 'ERROR'
      message.value = '❌ 任务出错: ' + currentStatus
    } else {
      message.value = `🤖 系统运作中... 当前状态: [${currentStatus}]`
    }
  } catch (error) {
    console.error("轮询状态时发生错误", error)
  }
}
</script>

<style scoped>
.container { max-width: 800px; margin: 40px auto; text-align: center; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; }
.subtitle { color: #666; margin-bottom: 30px; }
.card { background: #f8f9fa; border-radius: 12px; padding: 40px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
button { background: #007bff; color: white; border: none; padding: 15px 30px; font-size: 18px; border-radius: 8px; cursor: pointer; transition: background 0.3s; font-weight: bold; }
button:hover:not(:disabled) { background: #0056b3; }
.btn-running { background: #6c757d; cursor: not-allowed; }
.status-box { margin-top: 30px; text-align: left; padding: 20px; background: white; border-radius: 8px; }
.message { font-size: 16px; font-weight: bold; color: #d63384; }
.progress-bar { width: 100%; height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden; margin-top: 15px; }
.progress-inner { width: 50%; height: 100%; background: #28a745; animation: loading 2s infinite ease-in-out; }
@keyframes loading { 0% { transform: translateX(-100%); } 100% { transform: translateX(200%); } }
code { background: #e9ecef; padding: 5px 10px; border-radius: 4px; display: block; margin: 10px 0; word-break: break-all; }
.tip { font-size: 12px; color: #888; }

/* 新增的播放器样式 */
.video-player {
  width: 100%;
  max-width: 700px;
  border-radius: 8px;
  margin-top: 20px;
  box-shadow: 0 8px 16px rgba(0,0,0,0.2);
  background: #000;
}
</style>
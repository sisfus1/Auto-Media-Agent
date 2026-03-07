<template>
  <div class="min-h-screen bg-[#050505] text-gray-200 font-sans relative overflow-x-hidden flex flex-col items-center py-12 px-4 sm:px-6">
    
    <canvas ref="canvasRef" class="fixed top-0 left-0 w-full h-full z-0 opacity-50 pointer-events-auto"></canvas>

    <div class="z-10 w-full max-w-3xl p-8 sm:p-12 rounded-[2rem] backdrop-blur-2xl bg-white/[0.03] border border-white/10 shadow-[0_0_80px_rgba(0,0,0,0.8)] flex flex-col gap-10">
      
      <div class="flex flex-col items-center text-center gap-2 group cursor-default">
        <h1 class="text-4xl md:text-5xl font-extrabold tracking-[0.2em] text-transparent bg-clip-text bg-gradient-to-r from-gray-100 to-gray-500 transition-transform duration-700 group-hover:scale-[1.02]">
          AUTO-MEDIA-AGENT
        </h1>
        <p class="text-[10px] md:text-xs tracking-[0.3em] text-gray-500 uppercase mt-2">
          Autonomous Rendering Engine
        </p>
      </div>

      <div class="flex flex-col gap-3 relative group">
        <label class="text-xs tracking-[0.15em] text-gray-400 uppercase flex items-center gap-2">
          <svg class="w-4 h-4 text-gray-500 transition-colors group-hover:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"></path></svg>
          Engine Directive (Topic / Keywords)
        </label>
        <input 
          v-model="customTopic" 
          type="text" 
          placeholder="e.g., Focus strictly on Apple's latest AI models..." 
          class="w-full bg-black/40 border border-gray-800 rounded-xl px-5 py-4 text-sm tracking-wide text-white placeholder-gray-600 focus:outline-none focus:border-gray-400 focus:ring-1 focus:ring-gray-400 transition-all duration-300 hover:bg-black/60"
        />
      </div>

      <div class="flex justify-center mt-2">
        <button 
          @click="generateVideo" 
          :disabled="loading"
          class="relative group overflow-hidden px-12 py-4 rounded-full bg-white/5 border border-gray-600 transition-all duration-500 hover:border-gray-200 hover:bg-white/10 hover:shadow-[0_0_40px_rgba(255,255,255,0.1)] hover:-translate-y-1 disabled:opacity-40 disabled:hover:-translate-y-0 disabled:cursor-not-allowed active:scale-95"
        >
          <div class="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:animate-[shimmer_1.5s_infinite]"></div>
          <span class="relative text-xs md:text-sm tracking-[0.15em] uppercase font-bold text-gray-200 flex items-center gap-3">
            <svg v-if="loading" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ loading ? 'Processing Sequence...' : 'Initialize Generation' }}
          </span>
        </button>
      </div>

      <div v-if="videoUrl || loading" class="animate-fade-in-up rounded-2xl overflow-hidden border border-gray-800 bg-black/80 shadow-2xl relative aspect-video flex items-center justify-center group">
        
        <div v-if="loading" class="absolute inset-0 flex flex-col items-center justify-center bg-black/60 backdrop-blur-md z-10 text-gray-400 gap-5">
          <div class="w-10 h-10 border-4 border-gray-800 border-t-gray-300 rounded-full animate-spin"></div>
          <span class="text-xs tracking-[0.2em] uppercase animate-pulse">Rendering Multimodal Stream...</span>
        </div>
        
        <video 
          v-if="videoUrl"
          :src="videoUrl" 
          controls 
          autoplay
          class="w-full h-full object-cover outline-none transition-transform duration-1000 group-hover:scale-[1.01]"
        ></video>
      </div>

      <div class="mt-4 border-t border-gray-800/60 pt-8" v-if="history.length > 0">
        <h3 class="text-[10px] tracking-[0.2em] text-gray-500 uppercase mb-5 flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
          Asset Archives
        </h3>
        
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div 
            v-for="(item, index) in history" 
            :key="index"
            @click="playHistory(item)"
            class="group relative h-20 bg-gray-900 border border-gray-800 rounded-xl overflow-hidden cursor-pointer hover:border-gray-400 transition-all duration-300 hover:shadow-[0_0_15px_rgba(255,255,255,0.05)]"
          >
            <div class="absolute inset-0 bg-gradient-to-br from-black to-gray-800 opacity-90 group-hover:opacity-40 transition-opacity"></div>
            <div class="absolute inset-0 flex flex-col items-center justify-center p-2 text-center">
              <svg class="w-6 h-6 text-gray-500 group-hover:text-white group-hover:scale-125 transition-all mb-1 duration-300" fill="currentColor" viewBox="0 0 20 20"><path d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"></path></svg>
              <span class="text-[9px] text-gray-500 group-hover:text-gray-300 font-mono tracking-widest">{{ item.date }}</span>
            </div>
          </div>
        </div>
      </div>
      
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

// --- 状态管理 ---
const taskId = ref(null)
const customTopic = ref('')
const loading = ref(false)
const videoUrl = ref('')
const checkInterval = ref(null)
const history = ref([]) // 历史资产库数据

// 页面加载时从 LocalStorage 读取历史资产
onMounted(() => {
  const savedHistory = localStorage.getItem('ama_video_history')
  if (savedHistory) {
    history.value = JSON.parse(savedHistory)
  }
})

// --- 核心业务逻辑 ---
const generateVideo = async () => {
  loading.value = true
  videoUrl.value = ''
  
  try {
    // 提示：如果要后端接收 customTopic，可以在这发送 body。当前先保持简单的 POST
    const res = await fetch('http://localhost:8000/api/tasks/generate_video', {
      method: 'POST'
    })
    
    if (!res.ok) throw new Error(`Network response was ${res.status}`)
    
    const data = await res.json()
    taskId.value = data.task_id
    
    checkInterval.value = setInterval(checkStatus, 2000)
  } catch (error) {
    console.error("Fetch Error:", error)
    loading.value = false
    alert("System Error: Unable to reach backend engine.")
  }
}

const checkStatus = async () => {
  if (!taskId.value) return
  
  try {
    const res = await fetch(`http://localhost:8000/api/tasks/${taskId.value}`)
    const data = await res.json()
    
    if (data.status.startsWith('SUCCESS')) {
      clearInterval(checkInterval.value)
      loading.value = false
      const url = data.status.split(': ')[1]
      videoUrl.value = url
      
      // 保存至历史资产库
      saveToHistory(url)
    } else if (data.status.startsWith('FAILED') || data.status.startsWith('ERROR')) {
      clearInterval(checkInterval.value)
      loading.value = false
      alert(`Render Failed: ${data.status}`)
    }
  } catch (error) {
    console.error("Polling Error:", error)
    clearInterval(checkInterval.value)
    loading.value = false
  }
}

// 保存至本地资产库
const saveToHistory = (url) => {
  const now = new Date()
  const dateStr = `${now.getMonth()+1}/${now.getDate()} ${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}`
  
  // 插入到数组最前面
  history.value.unshift({ url, date: dateStr })
  
  // 只保留最近的 8 个视频，防止页面过长
  if (history.value.length > 8) {
    history.value = history.value.slice(0, 8)
  }
  
  localStorage.setItem('ama_video_history', JSON.stringify(history.value))
}

// 播放历史记录
const playHistory = (item) => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
  videoUrl.value = item.url
}

// --- 高级 Canvas 粒子引力场引擎 (防遮挡改良版) ---
const canvasRef = ref(null)
let animationFrameId = null

onMounted(() => {
  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')
  let width, height
  let particles = []
  
  const mouse = { x: null, y: null, radius: 180 }

  const resize = () => {
    width = canvas.width = window.innerWidth
    height = canvas.height = window.innerHeight
    initParticles()
  }

  window.addEventListener('resize', resize)
  window.addEventListener('mousemove', (e) => {
    mouse.x = e.x
    mouse.y = e.y
  })
  window.addEventListener('mouseout', () => {
    mouse.x = null
    mouse.y = null
  })

  class Particle {
    constructor() {
      this.x = Math.random() * width
      this.y = Math.random() * height
      this.vx = (Math.random() - 0.5) * 0.5
      this.vy = (Math.random() - 0.5) * 0.5
      this.size = Math.random() * 1.5 + 0.5
      this.baseColor = 'rgba(255, 255, 255, 0.4)'
    }
    draw() {
      ctx.beginPath()
      ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2)
      ctx.fillStyle = this.baseColor
      ctx.fill()
    }
    update() {
      if (this.x > width || this.x < 0) this.vx = -this.vx
      if (this.y > height || this.y < 0) this.vy = -this.vy
      this.x += this.vx
      this.y += this.vy

      if (mouse.x != null && mouse.y != null) {
        let dx = mouse.x - this.x
        let dy = mouse.y - this.y
        let distance = Math.sqrt(dx * dx + dy * dy)
        if (distance < mouse.radius) {
          const forceDirectionX = dx / distance
          const forceDirectionY = dy / distance
          const force = (mouse.radius - distance) / mouse.radius
          this.x -= forceDirectionX * force * 2
          this.y -= forceDirectionY * force * 2
        }
      }
      this.draw()
    }
  }

  const initParticles = () => {
    particles = []
    const numberOfParticles = (width * height) / 12000
    for (let i = 0; i < numberOfParticles; i++) {
      particles.push(new Particle())
    }
  }

  const animate = () => {
    ctx.clearRect(0, 0, width, height)
    for (let i = 0; i < particles.length; i++) {
      particles[i].update()
      for (let j = i; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x
        const dy = particles[i].y - particles[j].y
        const distance = Math.sqrt(dx * dx + dy * dy)
        if (distance < 120) {
          ctx.beginPath()
          ctx.strokeStyle = `rgba(255, 255, 255, ${0.08 - distance/1500})`
          ctx.lineWidth = 0.5
          ctx.moveTo(particles[i].x, particles[i].y)
          ctx.lineTo(particles[j].x, particles[j].y)
          ctx.stroke()
        }
      }
    }
    animationFrameId = requestAnimationFrame(animate)
  }

  resize()
  animate()
})

onUnmounted(() => {
  cancelAnimationFrame(animationFrameId)
})
</script>

<style>
/* 极简扫光动画 */
@keyframes shimmer {
  100% { transform: translateX(100%); }
}
/* 优雅滑入动画 */
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(15px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in-up {
  animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
/* 隐藏浏览器原生滚动条，保持极客感 */
::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-track {
  background: #050505; 
}
::-webkit-scrollbar-thumb {
  background: #333; 
  border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
  background: #555; 
}
</style>
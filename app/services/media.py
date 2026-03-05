import asyncio
import edge_tts
from moviepy.editor import AudioFileClip, ImageClip
import time
import requests
import os

class MediaService:
    def __init__(self):
        # 语音角色：zh-CN-YunxiNeural (男声，适合新闻)
        # 可选：zh-CN-XiaoxiaoNeural (女声)
        self.voice = "zh-CN-YunxiNeural"
        timestamp = int(time.time())
        self.output_audio = f"temp_audio_{timestamp}.mp3"
        self.output_video = f"final_daily_news_{timestamp}.mp4"

    async def _text_to_speech(self, text, output_file):
        """(内部异步方法) 调用 Edge-TTS 生成语音"""
        # 注意：这个方法必须保留，generate_audio 会调用它
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(output_file)

    def generate_background_image(self, prompt: str, save_path: str = "background.jpg") -> str:
        """调用云端大模型生成背景图"""
        print(f"🎨 视觉引擎启动！正在根据提示词生成高清插画: {prompt}")
        
        # 使用硅基流动的免费高速 FLUX 模型
        url = "https://api.siliconflow.cn/v1/images/generations"
        api_key = os.getenv("SILICONFLOW_API_KEY")
        
        if not api_key:
            print("⚠️ 警告：未找到 SILICONFLOW_API_KEY，跳过生图。")
            return None
            
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 1024x576 正好是 16:9 的宽屏视频比例
        payload = {
            "model": "black-forest-labs/FLUX.1-schnell",
            "prompt": prompt,
            "image_size": "1024x576" 
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status() # 如果报错直接抛出异常
            
            # 从返回结果中提取图片的下载链接
            image_url = response.json()["data"][0]["url"]
            
            # 将图片下载到本地
            img_data = requests.get(image_url).content
            with open(save_path, 'wb') as handler:
                handler.write(img_data)
                
            print(f"✅ AI 视觉背景图生成完毕！已保存至: {save_path}")
            return save_path
            
        except Exception as e:
            print(f"❌ 生图失败: {e}")
            return None

    def generate_audio(self, text: str):
        """生成 MP3 音频"""
        print(f"🔊 Media: 正在将文案转为语音 ({len(text)}字)...")
        try:
            # 【核心修改】安全地在同步/多线程环境中运行异步代码
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            if loop.is_running():
                # 如果当前线程已经有运行的循环（例如在 BackgroundTasks 中），使用 run_coroutine_threadsafe
                future = asyncio.run_coroutine_threadsafe(self._text_to_speech(text, self.output_audio), loop)
                future.result() # 等待任务完成
            else:
                # 如果没有循环，创建一个新的并运行
                loop.run_until_complete(self._text_to_speech(text, self.output_audio))
                
            print(f"✅ 音频已生成: {self.output_audio}")
            return self.output_audio
        except Exception as e:
            print(f"❌ 语音生成失败: {e}")
            return None

    def generate_video(self, audio_path: str, background_image: str):
        """合成最终视频 (图片 + 音频)"""
        print("🎬 Media: 正在渲染视频 (MoviePy)...")
        
        try:
            # 1. 加载音频
            audio = AudioFileClip(audio_path)
            
            # 2. 加载背景图，设置时长与音频一致
            video = ImageClip(background_image).set_duration(audio.duration)
            
            # 3. 合并音画
            video = video.set_audio(audio)
            
            # 4. 导出
            video.write_videofile(self.output_video, fps=24, codec="libx264", audio_codec="aac")
            
            print(f"✅ 视频渲染完成！文件: {self.output_video}")
            return self.output_video
            
        except Exception as e:
            print(f"❌ 视频合成失败: {e}")
            return None
import asyncio
import edge_tts
from moviepy.editor import AudioFileClip, ImageClip
import time

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
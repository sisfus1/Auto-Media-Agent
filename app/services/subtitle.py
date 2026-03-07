import numpy as np
from PIL import Image, ImageDraw, ImageFont
from faster_whisper import WhisperModel

# 1. 初始化 Whisper 听写大脑
print("🧠 正在加载 Whisper ASR 听写引擎...")
whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")

def get_subtitle_segments(audio_path: str):
    """
    第一阶段：纯粹的听写，只返回 [开始时间, 结束时间, 文字] 的时间轴字典
    """
    print("🎙️ Whisper 正在逐字解析音频时间轴...")
    segments_generator, _ = whisper_model.transcribe(audio_path, beam_size=5, language="zh")
    
    segments = []
    for segment in segments_generator:
        segments.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text
        })
        print(f"   ✍️ 捕获时间轴: [{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
        
    return segments

def add_subtitles_to_video(base_video_clip, segments):
    """
    第二阶段：极其硬核的像素级暴力渲染！彻底绕开 MoviePy 的图层叠加！
    """
    # 尝试加载中文字体
    try:
        font = ImageFont.truetype("C:\\Windows\\Fonts\\msyh.ttc", 60) # 微软雅黑，字号调大到60
    except IOError:
        try:
            font = ImageFont.truetype("C:\\Windows\\Fonts\\simhei.ttf", 60) # 黑体
        except:
            font = ImageFont.load_default()

    def render_frame(get_frame, t):
        """
        这个核心函数会在视频的每一帧被调用。t 是当前帧的时间(秒)。
        """
        # 1. 获取当前这一秒的背景底图 (纯粹的 RGB 像素矩阵)
        frame_array = get_frame(t)
        
        # 2. 遍历时间轴，看看当前这一秒该不该有字幕
        current_text = ""
        for seg in segments:
            if seg["start"] <= t <= seg["end"]:
                current_text = seg["text"]
                break
        
        # 3. 如果当前时间没有字幕，直接把原图还回去，不浪费算力
        if not current_text:
            return frame_array
            
        # 4. 如果有字幕，把像素矩阵变成画板
        img = Image.fromarray(frame_array)
        draw = ImageDraw.Draw(img)
        
        # 5. 计算文字居中位置 (底部往上一点)
        video_w, video_h = img.size
        x = video_w / 2
        y = video_h - 100
        
        # 6. 用黑笔描边，白笔写字，强行刻录在像素上！
        draw.text((x, y), current_text, font=font, fill="white", stroke_width=4, stroke_fill="black", anchor="ms")
        
        # 7. 把画好字的画板变回像素矩阵，塞回给视频
        return np.array(img)

    # fl() 是 MoviePy 的底层大法：对视频的所有帧应用我们自定义的函数
    return base_video_clip.fl(render_frame)
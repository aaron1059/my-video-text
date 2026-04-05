import os
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageSequenceClip, AudioFileClip

# 从GitHub Secrets读取Server酱SCKEY
SCKEY = os.environ.get("SCKEY")

# -------------------------- 1. 读取my_text.txt中的文字 --------------------------
def get_text():
    with open("my_text.txt", "r", encoding="utf-8") as f:
        return f.read().strip()

# -------------------------- 2. 生成匹配文字的图文视频 --------------------------
def text_to_video(text):
    # 1. 生成竖屏背景图（适配微信朋友圈/视频号 9:16）
    width, height = 1080, 1920
    img = Image.new("RGB", (width, height), color=(20, 20, 40))  # 深色背景
    draw = ImageDraw.Draw(img)

    # 2. 加载中文字体（GitHub Actions自带免费中文字体）
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", 80)
    except:
        font = ImageFont.load_default(size=80)

    # 3. 自动换行排版文字
    lines = []
    words = text.split("\n")
    for line in words:
        while len(line) > 0:
            # 计算每行可容纳的字数
            for i in range(len(line), 0, -1):
                bbox = draw.textbbox((0, 0), line[:i], font=font)
                if bbox[2] - bbox[0] < width - 200:
                    lines.append(line[:i])
                    line = line[i:]
                    break

    # 4. 绘制文字到图片
    y = height // 2 - (len(lines) * 100) // 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        draw.text((x, y), line, font=font, fill=(255, 255, 255))
        y += 100

    # 5. 保存图片
    img_path = "/tmp/text_image.png"
    img.save(img_path)

    # 6. 生成5秒视频 + 免费背景音乐
    # 加载免费BGM（GitHub Actions自带）
    audio = AudioFileClip("/usr/share/sounds/alsa/Noise.wav").subclip(0, 5)
    # 生成视频
    clip = ImageSequenceClip([img_path], fps=24)
    clip = clip.set_audio(audio)
    # 保存视频
    video_path = "/tmp/output_video.mp4"
    clip.write_videofile(video_path, codec="libx264", audio_codec="aac")

    return video_path

# -------------------------- 3. 上传视频到免费图床，获取可访问链接 --------------------------
def upload_to_free_host(video_path):
    # 用免费图床sm.ms上传（完全免费，无需注册）
    url = "https://sm.ms/api/v2/upload"
    files = {"smfile": open(video_path, "rb")}
    response = requests.post(url, files=files)
    result = response.json()
    if result["code"] == "success":
        return result["data"]["url"]
    else:
        # 备用图床
        url = "https://freeimage.host/api/1/upload"
        params = {"key": "6d207e02198a891b966d7f997e135dd8", "action": "upload"}
        files = {"source": open(video_path, "rb")}
        response = requests.post(url, files=files, data=params)
        result = response.json()
        return result["image"]["url"]

# -------------------------- 4. 通过Server酱推送视频链接到微信 --------------------------
def push_wechat(text, video_url):
    today = datetime.now().strftime("%Y-%m-%d")
    content = f"""
✅ 你的文字已自动生成视频！

【文案内容】
{text}

【视频链接】
{video_url}

👉 操作步骤：
1. 点开链接播放
2. 长按视频 → 保存到手机
3. 去微信朋友圈/视频号发布
"""
    resp = requests.post(
        f"https://sctapi.ftqq.com/{SCKEY}.send",
        data={
            "title": f"📽️ AI视频生成完成 {today}",
            "desp": content
        }, timeout=15
    )
    print("推送成功！状态码：", resp.status_code)

if __name__ == "__main__":
    # 全流程执行
    text = get_text()
    print("读取到的文字：", text)
    video_path = text_to_video(text)
    print("视频生成完成：", video_path)
    video_url = upload_to_free_host(video_path)
    print("视频链接：", video_url)
    push_wechat(text, video_url)
    print("✅ 全流程完成！")

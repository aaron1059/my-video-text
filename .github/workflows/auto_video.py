import os
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
# 修正moviepy导入方式，兼容所有版本
from moviepy.editor import ImageSequenceClip
import numpy as np

# 从GitHub Secrets读取Server酱SCKEY
SCKEY = os.environ.get("SCKEY")
if not SCKEY:
    raise Exception("❌ 错误：未配置SCKEY，请在GitHub Secrets中添加SCKEY")

# -------------------------- 1. 读取my_text.txt中的文字 --------------------------
def get_text():
    with open("my_text.txt", "r", encoding="utf-8") as f:
        text = f.read().strip()
    if not text:
        raise Exception("❌ 错误：my_text.txt为空，请输入文字内容")
    return text

# -------------------------- 2. 生成匹配文字的图文视频 --------------------------
def text_to_video(text):
    # 1. 生成竖屏背景图（9:16 适配微信）
    width, height = 1080, 1920
    img = Image.new("RGB", (width, height), color=(20, 20, 40))
    draw = ImageDraw.Draw(img)

    # 2. 加载中文字体（兼容GitHub Actions环境）
    font_paths = [
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    font = None
    for path in font_paths:
        try:
            font = ImageFont.truetype(path, 80)
            break
        except:
            continue
    if not font:
        font = ImageFont.load_default(size=80)

    # 3. 自动换行排版
    lines = []
    words = text.split("\n")
    for line in words:
        while len(line) > 0:
            for i in range(len(line), 0, -1):
                bbox = draw.textbbox((0, 0), line[:i], font=font)
                if bbox[2] - bbox[0] < width - 200:
                    lines.append(line[:i])
                    line = line[i:]
                    break

    # 4. 绘制文字
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

    # 6. 生成5秒无声视频（彻底解决BGM问题）
    clip = ImageSequenceClip([img_path], fps=24, durations=[5])
    video_path = "/tmp/output_video.mp4"
    clip.write_videofile(video_path, codec="libx264", audio_codec="aac", audio=False)

    return video_path

# -------------------------- 3. 上传视频到免费图床 --------------------------
def upload_to_free_host(video_path):
    # 主图床：sm.ms
    url = "https://sm.ms/api/v2/upload"
    try:
        with open(video_path, "rb") as f:
            files = {"smfile": f}
            response = requests.post(url, files=files, timeout=30)
            result = response.json()
        if result["code"] == "success":
            return result["data"]["url"]
    except Exception as e:
        print(f"sm.ms上传失败，尝试备用图床: {e}")
    
    # 备用图床：freeimage.host
    url = "https://freeimage.host/api/1/upload"
    params = {"key": "6d207e02198a891b966d7f997e135dd8", "action": "upload"}
    with open(video_path, "rb") as f:
        files = {"source": f}
        response = requests.post(url, files=files, data=params, timeout=30)
        result = response.json()
    return result["image"]["url"]

# -------------------------- 4. Server酱推送微信 --------------------------
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
    print(f"推送状态码：{resp.status_code}")
    if resp.status_code != 200:
        raise Exception(f"推送失败：{resp.text}")

if __name__ == "__main__":
    try:
        text = get_text()
        print(f"读取文字：{text}")
        video_path = text_to_video(text)
        print(f"视频生成完成：{video_path}")
        video_url = upload_to_free_host(video_path)
        print(f"视频链接：{video_url}")
        push_wechat(text, video_url)
        print("✅ 全流程成功！")
    except Exception as e:
        print(f"❌ 流程失败：{e}")
        raise

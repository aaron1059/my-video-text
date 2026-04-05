import os
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import subprocess

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

# -------------------------- 2. 生成文字图片 + ffmpeg合成视频 --------------------------
def text_to_video(text):
    width, height = 1080, 1920
    img = Image.new("RGB", (width, height), color=(20, 20, 40))
    draw = ImageDraw.Draw(img)

    # 加载中文字体
    font_paths = [
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    font = None
    for path in font_paths:
        try:
            font = ImageFont.truetype(path, 70)
            break
        except:
            continue
    if not font:
        font = ImageFont.load_default(size=70)

    # 自动换行
    lines = []
    for line in text.split("\n"):
        while line:
            for i in range(len(line), 0, -1):
                if draw.textlength(line[:i], font=font) < 900:
                    lines.append(line[:i])
                    line = line[i:]
                    break

    # 居中绘制
    y = height // 2 - len(lines) * 50
    for line in lines:
        text_width = draw.textlength(line, font=font)
        x = (width - text_width) // 2
        draw.text((x, y), line, font=font, fill=(255, 255, 255))
        y += 100

    img_path = "/tmp/frame.png"
    img.save(img_path)

    # 生成5秒视频
    video_path = "/tmp/output.mp4"
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", img_path,
        "-t", "5", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-vf", "scale=1080:1920", "-an", video_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return video_path

# -------------------------- 3. 上传到Catbox（支持视频直链，微信直接播放） --------------------------
def upload_to_catbox(video_path):
    url = "https://catbox.moe/user/api.php"
    files = {"fileToUpload": open(video_path, "rb")}
    data = {"reqtype": "fileupload"}
    response = requests.post(url, files=files, data=data, timeout=30)
    # Catbox直接返回直链，无需解析
    video_url = response.text.strip()
    if video_url.startswith("https://"):
        return video_url
    raise Exception(f"Catbox上传失败：{video_url}")

# -------------------------- 4. Server酱推送微信（直链直接点开播放） --------------------------
def push_wechat(text, video_url):
    today = datetime.now().strftime("%Y-%m-%d")
    content = f"""
✅ 你的文字视频已生成！微信直接点开就能看👇

【文案内容】
{text}

【视频直链】
{video_url}

👉 操作：
1. 直接点上面的链接，微信里直接播放
2. 长按视频 → 保存到手机
3. 发朋友圈/视频号
"""
    resp = requests.post(
        f"https://sctapi.ftqq.com/{SCKEY}.send",
        data={
            "title": f"📽️ 视频生成完成 {today}",
            "desp": content
        }, timeout=15
    )
    print(f"推送状态码：{resp.status_code}")
    if resp.status_code != 200:
        raise Exception(f"推送失败：{resp.text}")

if __name__ == "__main__":
    try:
        text = get_text()
        print(f"✅ 读取文字：{text}")
        video_path = text_to_video(text)
        print(f"✅ 视频生成完成：{video_path}")
        video_url = upload_to_catbox(video_path)
        print(f"✅ 视频直链：{video_url}")
        push_wechat(text, video_url)
        print("✅ 全流程完成！")
    except Exception as e:
        print(f"❌ 流程失败：{e}")
        raise

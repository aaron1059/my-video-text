import os
import requests
from PIL import Image, ImageDraw, ImageFont
import subprocess

SCKEY = os.environ.get("SCKEY")

def get_text():
    with open("my_text.txt", "r", encoding="utf-8") as f:
        return f.read().strip()

def text_to_video(text):
    w, h = 1080, 1920
    img = Image.new("RGB", (w, h), (20, 20, 40))
    draw = ImageDraw.Draw(img)

    font = None
    for path in [
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]:
        try:
            font = ImageFont.truetype(path, 70)
            break
        except:
            continue
    if not font:
        font = ImageFont.load_default(size=70)

    lines = []
    for line in text.split("\n"):
        while line:
            for i in range(len(line), 0, -1):
                if draw.textlength(line[:i], font) < 900:
                    lines.append(line[:i])
                    line = line[i:]
                    break

    y = h//2 - len(lines)*50
    for line in lines:
        x = (w - draw.textlength(line, font)) // 2
        draw.text((x, y), line, font=font, fill="white")
        y += 100

    img.save("/tmp/frame.png")

    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-i", "/tmp/frame.png",
        "-t", "5", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-an", "/tmp/output.mp4"
    ], check=True)

def push_wechat(text):
    repo = os.environ["GITHUB_REPOSITORY"]
    run_id = os.environ["GITHUB_RUN_ID"]
    url = f"https://github.com/{repo}/actions/runs/{run_id}"

    content = f"""
✅ 视频已生成！

【文字】
{text}

【下载方法】
1. 打开链接：{url}
2. 拉到下面找到 Artifacts
3. 点 output-video 下载
4. 解压后就是视频
"""
    requests.post(f"https://sctapi.ftqq.com/{SCKEY}.send", data={
        "title": "✅ 视频生成完成",
        "desp": content
    })

if __name__ == "__main__":
    text = get_text()
    text_to_video(text)
    push_wechat(text)
    print("✅ 完成")

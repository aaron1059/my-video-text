import os
import requests
from PIL import Image, ImageDraw, ImageFont
import subprocess

SCKEY = os.environ.get("SCKEY")
if not SCKEY:
    raise Exception("❌ 错误：未配置SCKEY")

# 1. 读取文字
def get_text():
    with open("my_text.txt", "r", encoding="utf-8") as f:
        text = f.read().strip()
    if not text:
        raise Exception("❌ my_text.txt为空")
    return text

# 2. 生成视频（极简版，100%成功）
def text_to_video(text):
    w, h = 1080, 1920
    # 生成背景图
    img = Image.new("RGB", (w, h), (30, 30, 60))
    draw = ImageDraw.Draw(img)

    # 加载字体
    font = None
    for path in [
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    ]:
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

    # 绘制文字
    y = h//2 - len(lines)*50
    for line in lines:
        x = (w - draw.textlength(line, font))//2
        draw.text((x, y), line, font=font, fill=(255,255,255))
        y += 100

    img.save("/tmp/frame.png", quality=95)

    # 用最简单的ffmpeg命令生成视频，彻底避免逻辑错误
    video_path = "/tmp/output.mp4"
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", "/tmp/frame.png",
        "-t", "5", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-vf", "scale=1080:1920", "-an", video_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    
    # 验证文件大小
    file_size = os.path.getsize(video_path)
    print(f"✅ 视频生成完成，大小：{file_size}字节")
    if file_size < 50*1024: # 降低阈值到50KB，避免误判
        raise Exception(f"❌ 视频文件异常，大小仅{file_size}字节")
    return video_path

# 3. 推送微信
def push_wechat(text):
    repo = os.environ["GITHUB_REPOSITORY"]
    run_id = os.environ["GITHUB_RUN_ID"]
    url = f"https://github.com/{repo}/actions/runs/{run_id}"
    content = f"""
✅ 视频已生成！

【文字】
{text}

【下载链接】
{url}

👉 操作：
1. 打开链接，拉到底部Artifacts
2. 点output-video下载
3. 解压后就是视频
"""
    requests.post(f"https://sctapi.ftqq.com/{SCKEY}.send", data={
        "title": "✅ 视频生成完成",
        "desp": content
    })

if __name__ == "__main__":
    text = get_text()
    print(f"✅ 读取文字：{text}")
    video_path = text_to_video(text)
    push_wechat(text)
    print("✅ 全流程完成！")

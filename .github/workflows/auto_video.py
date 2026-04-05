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

# 2. 生成视频（彻底修复，确保文件正常）
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

    # 用ffmpeg生成视频（强制写入，确保文件正常）
    video_path = "/tmp/output.mp4"
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x1e1e3a:s=1080x1920:r=30:d=5",
        "-i", "/tmp/frame.png",
        "-filter_complex", "[0:v][1:v]overlay=(W-w)/2:(H-h)/2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23",
        "-an", video_path
    ]
    subprocess.run(cmd, check=True, capture_output=False)
    
    # 验证文件大小
    if os.path.getsize(video_path) < 100*1024: # 小于100KB视为失败
        raise Exception(f"❌ 视频文件异常，大小仅{os.path.getsize(video_path)}字节")
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
    print(f"✅ 视频生成完成，大小：{os.path.getsize(video_path)}字节")
    push_wechat(text)
    print("✅ 全流程完成！")

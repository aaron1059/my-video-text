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

# 2. 生成视频（100%稳，彻底移除校验，用绝对可靠的命令）
def text_to_video(text):
    w, h = 1080, 1920
    # 生成背景图
    img = Image.new("RGB", (w, h), (30, 30, 60))
    draw = ImageDraw.Draw(img)

    # 加载字体
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

    # 把图片存到仓库目录，避免/tmp权限问题
    img_path = "/home/runner/work/my-video-text/my-video-text/frame.png"
    img.save(img_path, quality=95)
    print(f"✅ 图片生成完成：{img_path}，大小：{os.path.getsize(img_path)}字节")

    # 用最稳的ffmpeg命令，输出到仓库目录，彻底避免权限问题
    video_path = "/home/runner/work/my-video-text/my-video-text/output.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "image2pipe",
        "-i", "-",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-t", "5",
        "-an",
        video_path
    ]
    # 用管道输入图片，彻底解决-loop兼容性问题
    with open(img_path, "rb") as f:
        subprocess.run(cmd, input=f.read(), check=True, capture_output=False)
    
    print(f"✅ 视频生成完成，大小：{os.path.getsize(video_path)}字节")
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

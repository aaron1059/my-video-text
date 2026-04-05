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
    # 1. 生成9:16竖屏背景图（适配微信）
    width, height = 1080, 1920
    img = Image.new("RGB", (width, height), color=(20, 20, 40))
    draw = ImageDraw.Draw(img)

    # 2. 加载中文字体（兼容所有环境）
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

    # 3. 自动换行排版
    lines = []
    for line in text.split("\n"):
        while line:
            for i in range(len(line), 0, -1):
                if draw.textlength(line[:i], font=font) < 900:
                    lines.append(line[:i])
                    line = line[i:]
                    break

    # 4. 居中绘制文字
    y = height // 2 - len(lines) * 50
    for line in lines:
        text_width = draw.textlength(line, font=font)
        x = (width - text_width) // 2
        draw.text((x, y), line, font=font, fill=(255, 255, 255))
        y += 100

    # 5. 保存图片
    img_path = "/tmp/frame.png"
    img.save(img_path)

    # 6. 用ffmpeg生成5秒无声视频
    video_path = "/tmp/output.mp4"
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", img_path,
        "-t", "5", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-vf", "scale=1080:1920", "-an", video_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return video_path

# -------------------------- 3. Server酱推送微信（直接推GitHub Actions链接） --------------------------
def push_wechat(text):
    today = datetime.now().strftime("%Y-%m-%d")
    # 直接推送当前Actions运行页面，你可以从这里下载视频
    # （GitHub会自动生成artifact下载链接，无需第三方图床）
    run_url = os.environ.get("GITHUB_SERVER_URL") + "/" + os.environ.get("GITHUB_REPOSITORY") + "/actions/runs/" + os.environ.get("GITHUB_RUN_ID")
    
    content = f"""
✅ 你的文字已自动生成视频！

【文案内容】
{text}

【视频下载链接】
{run_url}

👉 操作步骤：
1. 点开链接，进入Actions页面
2. 点击「Artifacts」→「output-video」下载视频
3. 保存到手机，发朋友圈/视频号
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
        print(f"✅ 读取到的文字：{text}")
        video_path = text_to_video(text)
        print(f"✅ 视频生成完成：{video_path}")
        push_wechat(text)
        print("✅ 全流程完成！")
    except Exception as e:
        print(f"❌ 流程失败：{e}")
        raise

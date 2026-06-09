# video_transcribe.py — 视频→文本+截图 蒸馏工具
# 用法: python video_transcribe.py <视频文件>
#        python video_transcribe.py video.mp4
#        python video_transcribe.py "c:/videos/因子拆解.mp4"
# 输出: 同目录下 <视频名>_transcript.md + <视频名>_frames/ 截图

import subprocess, os, sys, json, base64, io, time, urllib.request

API_KEY = os.environ.get("SILICONFLOW_API_KEY", "")
API_URL = "https://api.siliconflow.cn/v1/audio/transcriptions"

if not API_KEY:
    # 尝试从 .claude.json (MCP配置) 读取
    try:
        for cfg_name in [".claude.json", ".claude/settings.json"]:
            cfg_path = os.path.expanduser(f"~/{cfg_name}")
            if os.path.exists(cfg_path):
                with open(cfg_path) as f:
                    s = json.load(f)
                # .claude.json: mcpServers.<name>.env.SILICONFLOW_API_KEY
                for server in s.get("mcpServers", {}).values():
                    if server.get("env", {}).get("SILICONFLOW_API_KEY"):
                        API_KEY = server["env"]["SILICONFLOW_API_KEY"]
                        break
                # settings.json: env.SILICONFLOW_API_KEY
                if not API_KEY:
                    API_KEY = s.get("env", {}).get("SILICONFLOW_API_KEY", "")
                if API_KEY: break
    except: pass
    if not API_KEY:
        print("未找到 SILICONFLOW_API_KEY，请在终端执行:")
        print('  set SILICONFLOW_API_KEY=你的key')
        sys.exit(1)

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def extract_audio(video_path):
    """ffmpeg 提取音频为 16kHz mono wav"""
    wav_path = video_path + ".audio.wav"
    print(f"🎧 提取音频...")
    r = run(f'ffmpeg -y -i "{video_path}" -ar 16000 -ac 1 -vn "{wav_path}" 2>&1')
    if not os.path.exists(wav_path) or os.path.getsize(wav_path) < 1000:
        print(f"  失败: {r.stderr[-200:]}")
        return None
    size_mb = os.path.getsize(wav_path) / 1024 / 1024
    print(f"  完成 ({size_mb:.1f}MB)")
    return wav_path

def split_audio(wav_path, chunk_secs=300):
    """大文件分段 (SiliconFlow 限制 25MB/段, ~5分钟)"""
    size_mb = os.path.getsize(wav_path) / 1024 / 1024
    if size_mb < 20:
        return [wav_path]

    # 获取时长
    r = run(f'ffprobe -v quiet -show_entries format=duration -of csv=p=0 "{wav_path}"')
    try:
        duration = float(r.stdout.strip())
    except:
        duration = size_mb * 60 / 10  # 估算: ~10MB/分钟

    chunks = []
    for start in range(0, int(duration) + 1, chunk_secs):
        chunk_path = wav_path + f".chunk{start}.wav"
        run(f'ffmpeg -y -i "{wav_path}" -ss {start} -t {chunk_secs} -ar 16000 -ac 1 "{chunk_path}" 2>&1')
        if os.path.exists(chunk_path) and os.path.getsize(chunk_path) > 1000:
            chunks.append(chunk_path)
    print(f"  分 {len(chunks)} 段")
    return chunks

def transcribe_chunk(chunk_path):
    """SiliconFlow 语音转文字 (FunAudioLLM/SenseVoiceSmall)"""
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email.mime.text import MIMEText
    from email import encoders

    with open(chunk_path, "rb") as f:
        audio_data = f.read()

    # 用 email.mime 正确构建 multipart
    outer = MIMEMultipart('form-data')
    outer.attach(MIMEText('FunAudioLLM/SenseVoiceSmall', _subtype='plain', _charset='utf-8'))
    outer['model'] = 'ignored'  # won't be used
    # Actually, we need form fields, not headers. Let's do it right.

    boundary = "----FormBoundary" + os.urandom(16).hex()
    body = b''
    # model field
    body += f'--{boundary}\r\n'.encode()
    body += b'Content-Disposition: form-data; name="model"\r\n\r\n'
    body += b'FunAudioLLM/SenseVoiceSmall\r\n'
    # file field
    body += f'--{boundary}\r\n'.encode()
    body += b'Content-Disposition: form-data; name="file"; filename="audio.wav"\r\n'
    body += b'Content-Type: audio/wav\r\n\r\n'
    body += audio_data
    body += b'\r\n'
    body += f'--{boundary}--\r\n'.encode()

    req = urllib.request.Request(API_URL, data=body)
    req.add_header("Authorization", f"Bearer {API_KEY}")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")

    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read())
            return result.get("text", "")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()[:300]
        print(f"  API error ({e.code}): {err_body}")
        return ""
    except Exception as e:
        print(f"  API error: {e}")
        return ""

def transcribe_all(chunks):
    """逐段转录"""
    full_text = []
    for i, chunk in enumerate(chunks):
        print(f"  📝 转录第 {i+1}/{len(chunks)} 段...")
        text = transcribe_chunk(chunk)
        if text:
            full_text.append(text)
        time.sleep(0.5)
    return "\n".join(full_text)

def extract_frames(video_path, output_dir, interval=10):
    """每 interval 秒截一帧"""
    os.makedirs(output_dir, exist_ok=True)
    print(f"📸 截图 (每{interval}秒)...")
    run(f'ffmpeg -y -i "{video_path}" -vf "fps=1/{interval}" -q:v 2 "{output_dir}/frame_%04d.jpg" 2>&1')
    count = len([f for f in os.listdir(output_dir) if f.endswith('.jpg')])
    print(f"  完成: {count} 张")
    return count

def cleanup(paths):
    for p in paths:
        try:
            if os.path.isfile(p): os.remove(p)
        except: pass

def main():
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    VIDEO_DIR = os.path.join(SCRIPT_DIR, "videos")
    os.makedirs(VIDEO_DIR, exist_ok=True)

    # 无参数 → 自动处理 videos/ 下所有视频
    if len(sys.argv) < 2:
        video_exts = ('.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv')
        videos = sorted([f for f in os.listdir(VIDEO_DIR) if f.lower().endswith(video_exts)])
        if not videos:
            print(f"请将视频放入: {VIDEO_DIR}")
            print(f"或: python video_transcribe.py <视频文件>")
            sys.exit(1)
        print(f"📂 发现 {len(videos)} 个视频\n")
        for i, v in enumerate(videos):
            print(f"  [{i+1}/{len(videos)}] {v}")
        print()
        for v in videos:
            process_one(os.path.join(VIDEO_DIR, v))
        print(f"\n✅ 全部完成 ({len(videos)} 个)")
        return

    video_path = sys.argv[1]
    if not os.path.exists(video_path):
        print(f"文件不存在: {video_path}")
        sys.exit(1)
    process_one(video_path)

def process_one(video_path):
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    out_dir = os.path.dirname(video_path) or "."

    print(f"\n{'='*60}")
    print(f"  🎬 {os.path.basename(video_path)}")
    print(f"{'='*60}\n")

    # 1. 音频
    wav = extract_audio(video_path)
    if not wav:
        print("❌ 音频提取失败")
        sys.exit(1)

    # 2. 分段转录
    chunks = split_audio(wav)
    transcript = transcribe_all(chunks)

    if not transcript:
        print("❌ 转录为空")
        cleanup([wav] + chunks)
        sys.exit(1)

    # 3. 截图
    frames_dir = os.path.join(out_dir, f"{base_name}_frames")
    frame_count = extract_frames(video_path, frames_dir)

    # 4. 写入 md
    md_path = os.path.join(out_dir, f"{base_name}_transcript.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# {base_name}\n\n")
        f.write(f"> 转录时间: {time.strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"> 时长片段: {len(chunks)} 段\n")
        f.write(f"> 截图: {frame_count} 张 → `{base_name}_frames/`\n\n")
        f.write("---\n\n")
        f.write(transcript)

    # 5. 清理
    cleanup([wav] + chunks)

    print(f"\n{'='*60}")
    print(f"  ✅ 完成")
    print(f"  文本: {md_path}")
    print(f"  截图: {frames_dir}/ ({frame_count} 张)")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()

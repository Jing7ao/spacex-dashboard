"""
图片→视频 最简单方案
用法: python img2video.py <图片目录> -o out.mp4
"""
import os, sys, subprocess, argparse, glob

def make_video(img_dir, output, fps=1, w=1080, h=1920):
    """
    每张图作为视频的一帧，用 fps 控制速度。
    fps=0.5 → 每张图2秒, fps=1 → 每张图1秒, fps=1/3→3秒
    不需要 filter_complex，不会崩。
    """
    exts = ('.jpg','.jpeg','.png','.webp','.bmp')
    imgs = sorted([f for f in os.listdir(img_dir) if f.lower().endswith(exts)])
    if not imgs:
        print("No images found")
        return

    print(f"{len(imgs)} images -> {len(imgs)/fps:.0f}s video")

    # 第一步：所有图缩放+填充，输出到临时目录
    tmp_dir = img_dir + "_scaled"
    os.makedirs(tmp_dir, exist_ok=True)

    print(f"Step 1/2: Scaling {len(imgs)} images...")
    for i, img in enumerate(imgs):
        src = os.path.join(img_dir, img)
        out_name = f"{i:05d}.png"
        dst = os.path.join(tmp_dir, out_name)
        if os.path.exists(dst):
            continue
        # 缩放+居中填充到目标尺寸
        cmd = [
            "ffmpeg", "-y", "-i", src,
            "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2",
            "-frames:v", "1", dst
        ]
        subprocess.run(cmd, capture_output=True)
        if i % 20 == 0:
            print(f"  {i+1}/{len(imgs)}")

    # 第二步：帧序列 → 视频
    print(f"Step 2/2: Encoding video...")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", os.path.join(tmp_dir, "%05d.png"),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        output
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    # 清理
    for f in os.listdir(tmp_dir):
        os.remove(os.path.join(tmp_dir, f))
    os.rmdir(tmp_dir)

    print(f"Done: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Images to video (simple frame sequence)")
    parser.add_argument("img_dir")
    parser.add_argument("--output", "-o", default="slideshow.mp4")
    parser.add_argument("--fps", type=float, default=0.5, help="Frames per second. 0.5=2s/img, 0.33=3s/img")
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1920)

    args = parser.parse_args()
    make_video(args.img_dir, args.output, args.fps, args.width, args.height)


import asyncio
import shutil
import os

FFMPEG = shutil.which("ffmpeg")

WIDTH = 3840
HEIGHT = 2160
FPS = 30


EFFECTS = {
    "normal": "",
    "cinematic": "eq=contrast=1.15:saturation=1.2:brightness=0.02",
    "romantic": "eq=saturation=1.35:gamma=1.08,colorbalance=rs=0.08:gs=0.02",
    "sad": "eq=saturation=0.55:brightness=-0.04:contrast=1.12",
    "memories": "colorbalance=rs=0.06:bs=-0.04,eq=contrast=1.08:saturation=0.85",
    "attitude": "eq=contrast=1.35:saturation=1.25:brightness=-0.02",
    "gray": "hue=s=0",
    "vintage": "colorbalance=rs=0.12:gs=0.03:bs=-0.10,eq=contrast=1.1:saturation=0.8",
    "blur": "gblur=sigma=2",
    "rgb": "rgbashift=rh=8:bh=-8",
    "glitch": "rgbashift=rh=12:bh=-12",
    "shake": "crop=iw-20:ih-20:x='10+10*sin(t*20)':y='10+10*cos(t*18)',scale=3840:2160",
    "slow": "setpts=2*PTS",
    "fast": "setpts=0.5*PTS",
}


async def run_ffmpeg(args):
    if not FFMPEG:
        raise RuntimeError("FFmpeg is not installed on this server.")

    process = await asyncio.create_subprocess_exec(
        FFMPEG,
        "-y",
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        error = stderr.decode(errors="ignore")
        raise RuntimeError(error[-2500:] or "FFmpeg rendering failed.")

    return True


def video_filter(effect):
    selected = EFFECTS.get(effect, EFFECTS["cinematic"])

    filters = [
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase",
        f"crop={WIDTH}:{HEIGHT}",
        f"fps={FPS}",
    ]

    if selected:
        filters.append(selected)

    return ",".join(filters)


async def render_photo(
    photo,
    output,
    effect="cinematic",
    music=None,
    duration=10,
):
    if not os.path.exists(photo):
        raise FileNotFoundError("Photo file not found.")

    duration = max(5, min(int(duration), 60))

    selected = EFFECTS.get(effect, EFFECTS["cinematic"])

    filters = [
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase",
        f"crop={WIDTH}:{HEIGHT}",
        (
            "zoompan="
            "z='min(zoom+0.0015,1.5)':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            f"d=1:s={WIDTH}x{HEIGHT}:fps={FPS}"
        ),
    ]

    if selected:
        filters.append(selected)

    args = [
        "-loop", "1",
        "-framerate", str(FPS),
        "-i", photo,
    ]

    if music and os.path.exists(music):
        args += [
            "-stream_loop", "-1",
            "-i", music,
        ]

    args += [
        "-vf", ",".join(filters),
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
    ]

    if music and os.path.exists(music):
        args += [
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
        ]
    else:
        args += ["-an"]

    args += [
        "-movflags", "+faststart",
        output,
    ]

    await run_ffmpeg(args)


async def render_video(
    video,
    output,
    effect="cinematic",
    music=None,
    duration=30,
    start_time=0,
):
    if not os.path.exists(video):
        raise FileNotFoundError("Video file not found.")

    duration = max(5, min(int(duration), 60))
    start_time = max(0, int(start_time))

    args = []

    if start_time:
        args += ["-ss", str(start_time)]

    args += ["-i", video]

    if music and os.path.exists(music):
        args += [
            "-stream_loop", "-1",
            "-i", music,
        ]

    args += [
        "-t", str(duration),
        "-vf", video_filter(effect),
        "-map", "0:v:0",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
    ]

    if music and os.path.exists(music):
        args += [
            "-map", "1:a:0",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
        ]
    else:
        args += [
            "-map", "0:a?",
            "-c:a", "aac",
            "-b:a", "192k",
        ]

    args += [
        "-movflags", "+faststart",
        output,
    ]

    await run_ffmpeg(args)

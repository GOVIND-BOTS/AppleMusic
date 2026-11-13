
import asyncio
import os
import shutil

FFMPEG = shutil.which("ffmpeg")

WIDTH = 3840
HEIGHT = 2160
FPS = 30


EFFECTS = {
    "normal": "null",
    "cinematic": "eq=contrast=1.15:saturation=1.25:brightness=0.02",
    "gray": "hue=s=0",
    "vintage": "colorbalance=rs=.08:gs=.02:bs=-.08,eq=contrast=1.12:saturation=.75",
    "blur": "gblur=sigma=12",
    "rgb": "rgbashift=rh=8:bh=-8",
    "glitch": "rgbashift=rh=12:bh=-12,eq=contrast=1.2",
    "shake": "crop=iw-40:ih-40:x=20:y=20,scale=3840:2160",
    "slow": "setpts=2.0*PTS",
    "fast": "setpts=0.5*PTS",
}


async def run_ffmpeg(args):
    if not FFMPEG:
        raise RuntimeError("FFmpeg is not installed.")

    process = await asyncio.create_subprocess_exec(
        FFMPEG,
        "-hide_banner",
        "-loglevel", "error",
        "-y",
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise RuntimeError(
            stderr.decode(errors="replace")[-2500:]
        )


def video_filter(effect):
    selected = EFFECTS.get(effect, EFFECTS["normal"])

    base = (
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={WIDTH}:{HEIGHT},"
        f"fps={FPS}"
    )

    return f"{base},{selected}"


async def render_photo(photo, output, effect="cinematic", music=None):
    if not os.path.exists(photo):
        raise FileNotFoundError("Photo file not found.")

    # Animated Ken Burns style photo video.
    selected = EFFECTS.get(effect, EFFECTS["cinematic"])

    zoom = (
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={WIDTH}:{HEIGHT},"
        f"zoompan=z='min(zoom+0.0015,1.15)':"
        f"x='iw/2-(iw/zoom/2)':"
        f"y='ih/2-(ih/zoom/2)':"
        f"d=180:s={WIDTH}x{HEIGHT}:fps={FPS}"
    )

    if selected != "null":
        zoom += "," + selected

    args = [
        "-loop", "1",
        "-i", photo,
        "-t", "6",
        "-vf", zoom,
        "-an",
    ]

    if music and os.path.exists(music):
        args += [
            "-i", music,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            "-c:a", "aac",
            "-b:a", "192k",
        ]
    else:
        args += ["-an"]

    args += [
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output,
    ]

    await run_ffmpeg(args)
    return output


async def render_video(video, output, effect="cinematic", music=None):
    if not os.path.exists(video):
        raise FileNotFoundError("Video file not found.")

    args = ["-i", video]

    if music and os.path.exists(music):
        args += ["-i", music]

    args += [
        "-map", "0:v:0",
        "-vf", video_filter(effect),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
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
        args += ["-map", "0:a?", "-c:a", "aac", "-b:a", "192k"]

    args += [
        "-movflags", "+faststart",
        output,
    ]

    await run_ffmpeg(args)
    return output

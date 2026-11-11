"""ScreenScene: turn a screenshot and narration beats into a narrated MP4.

Pipeline: one ElevenLabs text-to-speech call per beat, measure each clip,
size each camera move to its spoken beat, render with Manim, mux with ffmpeg.
"""

import base64
import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_VOICE_ID = "Xb7hH8MSUJpSbSDYk0k2"  # "Alice", a premade voice
MODEL_ID = "eleven_turbo_v2_5"
MAX_BEATS = 8
MAX_CHARS_PER_BEAT = 500
TAIL_SECONDS = 0.6
OUTPUT_DIR = Path.home() / "screenscene_output"
QUALITY_FLAGS = {"draft": "-ql", "standard": "-qm"}

SCREENSCENE_RENDER_SCHEMA = {
    "name": "screenscene_render",
    "description": (
        "Turn a screenshot into a short narrated explainer video. Use when "
        "the user gives an image (diagram, dashboard, UI, code) and asks for "
        "an animated, voiced walkthrough. First look at the image and decide "
        "3 to 6 beats. Each beat has narration text (one or two short "
        "sentences) and a region of the image to zoom into, as fractions "
        "[x0, y0, x1, y1] with the origin at the top left. Use "
        "[0, 0, 1, 1] for a whole-image beat. Returns the path of the MP4."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "image_path": {
                "type": "string",
                "description": "Path to the screenshot file (png or jpg)",
            },
            "beats": {
                "type": "array",
                "description": "Ordered beats of the walkthrough (1 to 8)",
                "items": {
                    "type": "object",
                    "properties": {
                        "narration": {
                            "type": "string",
                            "description": "What the narrator says in this beat",
                        },
                        "region": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Focus box [x0, y0, x1, y1], each 0 to 1",
                        },
                    },
                    "required": ["narration"],
                },
            },
            "voice_id": {
                "type": "string",
                "description": "Optional ElevenLabs voice id the account can use",
            },
            "quality": {
                "type": "string",
                "description": "draft (480p15, fastest) or standard (720p30, default)",
            },
        },
        "required": ["image_path", "beats"],
    },
}

SCENE_TEMPLATE = '''
from manim import *
import json

class Walk(MovingCameraScene):
    def construct(self):
        spec = json.load(open({spec_path!r}))
        img = ImageMobject({image_path!r})
        img.set(height=7.0)
        W, H = img.width, img.height
        self.add(img)
        frame = self.camera.frame
        frame.move_to(ORIGIN).set(width=max(W * 1.1, H * 1.1 * 16 / 9))
        prev = None
        for beat in spec["beats"]:
            x0, y0, x1, y1 = beat["region"]
            cx = ((x0 + x1) / 2 - 0.5) * W
            cy = (0.5 - (y0 + y1) / 2) * H
            rw, rh = (x1 - x0) * W, (y1 - y0) * H
            width = max(rw, rh * 16 / 9) * 1.15
            d = beat["duration"]
            move = min(1.2, 0.4 * d)
            anims = [frame.animate.move_to([cx, cy, 0]).set(width=width)]
            if prev is not None:
                anims.append(FadeOut(prev))
                prev = None
            self.play(*anims, run_time=move, rate_func=smooth)
            used = move
            if (x1 - x0) < 0.95 or (y1 - y0) < 0.95:
                rect = Rectangle(width=rw, height=rh, stroke_color=YELLOW,
                                 stroke_width=5, fill_opacity=0).move_to([cx, cy, 0])
                self.play(Create(rect), run_time=0.4)
                used += 0.4
                prev = rect
            self.wait(max(d - used, 0.01))
        self.wait({tail})
'''


class RenderError(Exception):
    pass


def _tool(env_name, command):
    path = os.environ.get(env_name) or shutil.which(command)
    if not path:
        raise RenderError(
            f"'{command}' was not found. Install it and put it on PATH "
            f"(or set {env_name} to its full path)."
        )
    return path


def _clean_region(region):
    if not isinstance(region, (list, tuple)) or len(region) != 4:
        return [0.0, 0.0, 1.0, 1.0]
    try:
        x0, y0, x1, y1 = [min(max(float(v), 0.0), 1.0) for v in region]
    except (TypeError, ValueError):
        return [0.0, 0.0, 1.0, 1.0]
    if x1 - x0 < 0.05 or y1 - y0 < 0.05:
        return [0.0, 0.0, 1.0, 1.0]
    return [x0, y0, x1, y1]


def _narrate(text, out_path, key, voice_id):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"
    body = json.dumps({"text": text, "model_id": MODEL_ID}).encode()
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"xi-api-key": key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:300]
        raise RenderError(f"ElevenLabs returned HTTP {e.code}: {detail}")
    except (urllib.error.URLError, TimeoutError) as e:
        raise RenderError(f"Could not reach ElevenLabs: {e}")
    out_path.write_bytes(base64.b64decode(data["audio_base64"]))


def _duration(ffprobe, path):
    out = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True, timeout=30,
    ).stdout.strip()
    return float(out)


def _render(args):
    from agent.secret_scope import get_secret

    key = (get_secret("ELEVENLABS_API_KEY") or "").strip()
    if not key:
        raise RenderError("ELEVENLABS_API_KEY is not set for this plugin.")

    image = Path(str(args.get("image_path", ""))).expanduser().resolve()
    if not image.is_file():
        raise RenderError(f"Image not found: {image}")

    beats_in = args.get("beats") or []
    if not isinstance(beats_in, list) or not 1 <= len(beats_in) <= MAX_BEATS:
        raise RenderError(f"Provide between 1 and {MAX_BEATS} beats.")
    beats = []
    for i, b in enumerate(beats_in):
        text = str((b or {}).get("narration", "")).strip()
        if not text:
            raise RenderError(f"Beat {i + 1} has no narration text.")
        if len(text) > MAX_CHARS_PER_BEAT:
            raise RenderError(
                f"Beat {i + 1} narration is over {MAX_CHARS_PER_BEAT} characters."
            )
        beats.append({"narration": text, "region": _clean_region(b.get("region"))})

    voice_id = str(args.get("voice_id") or DEFAULT_VOICE_ID).strip()
    flag = QUALITY_FLAGS.get(str(args.get("quality") or "standard"), "-qm")

    manim = _tool("SCREENSCENE_MANIM", "manim")
    ffmpeg = _tool("SCREENSCENE_FFMPEG", "ffmpeg")
    ffprobe = _tool("SCREENSCENE_FFPROBE", "ffprobe")

    work = Path(tempfile.mkdtemp(prefix="screenscene_"))
    try:
        clips = []
        for i, beat in enumerate(beats):
            mp3 = work / f"beat{i}.mp3"
            _narrate(beat["narration"], mp3, key, voice_id)
            beat["duration"] = _duration(ffprobe, mp3)
            clips.append(mp3)

        listfile = work / "list.txt"
        listfile.write_text("".join(f"file '{c}'\n" for c in clips))
        audio = work / "audio.m4a"
        subprocess.run(
            [ffmpeg, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
             "-i", str(listfile), "-c:a", "aac", str(audio)],
            check=True, timeout=120,
        )

        spec = work / "spec.json"
        spec.write_text(json.dumps({"beats": beats}))
        scene = work / "scene.py"
        scene.write_text(SCENE_TEMPLATE.format(
            spec_path=str(spec), image_path=str(image), tail=TAIL_SECONDS))
        proc = subprocess.run(
            [manim, flag, "--media_dir", str(work / "media"),
             "-o", "walk", str(scene), "Walk"],
            capture_output=True, text=True, timeout=600,
        )
        if proc.returncode != 0:
            raise RenderError("Manim failed: " + proc.stderr[-600:])
        video = next((work / "media").rglob("walk.mp4"), None)
        if video is None:
            raise RenderError("Manim finished but no video file was found.")

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        final = OUTPUT_DIR / f"screenscene_{time.strftime('%Y%m%d_%H%M%S')}.mp4"
        subprocess.run(
            [ffmpeg, "-y", "-loglevel", "error", "-i", str(video),
             "-i", str(audio), "-c:v", "copy", "-c:a", "aac",
             "-shortest", str(final)],
            check=True, timeout=120,
        )
        return {
            "status": "ok",
            "video_path": str(final),
            "duration_seconds": round(_duration(ffprobe, final), 2),
            "beats": len(beats),
        }
    finally:
        shutil.rmtree(work, ignore_errors=True)


def screenscene_render(args: dict, **kwargs) -> str:
    """Tool handler. Always returns a JSON string and never raises."""
    try:
        return json.dumps(_render(args or {}))
    except RenderError as e:
        return json.dumps({"error": str(e)})
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "A rendering step timed out."})
    except subprocess.CalledProcessError as e:
        return json.dumps({"error": f"Command failed: {e.cmd[0]} (exit {e.returncode})"})
    except Exception as e:
        return json.dumps({"error": f"screenscene_render failed: {e}"})


def register(ctx):
    ctx.register_tool(
        name="screenscene_render",
        toolset="screenscene",
        schema=SCREENSCENE_RENDER_SCHEMA,
        handler=screenscene_render,
    )
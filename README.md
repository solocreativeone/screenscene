# ScreenScene

ScreenScene is a Hermes Agent plugin that turns a screenshot and a short list of narration beats into a narrated explainer video. For each beat it zooms the camera to a region of your screenshot, draws a highlight rectangle around it, and plays an ElevenLabs voiceover. Every camera move is sized to the length of its spoken beat, so the visuals and the voice stay in step.

## How it works

1. Hermes looks at the screenshot and chooses 3 to 6 beats. Each beat has a short narration and a focus region.
2. The plugin sends each beat's text to ElevenLabs and measures the length of the returned audio.
3. Manim renders a camera path over your real screenshot, with each move timed to its beat.
4. ffmpeg combines the video and the narration into one MP4.

## Tool

`screenscene_render`

| Parameter | Required | Description |
|---|---|---|
| `image_path` | yes | Path to a PNG or JPG screenshot |
| `beats` | yes | 1 to 8 beats. Each has `narration` (up to 500 characters) and an optional `region` as `[x0, y0, x1, y1]`, fractions of the image from the top left. Use `[0, 0, 1, 1]` for a whole-image beat |
| `voice_id` | no | An ElevenLabs voice your account can use. Default is a premade voice |
| `quality` | no | `standard` (720p30, default) or `draft` (480p15, faster) |

It returns the path of the finished video, its length in seconds, and the number of beats. Videos are saved in `~/screenscene_output/`.

Example prompt: "Use screenscene_render on ~/shots/dashboard.png. Make 4 beats: an overview, then three zooms on the most important areas. Keep each narration short."

## Requirements

* Manim Community Edition (`manim`) on your PATH, or set `SCREENSCENE_MANIM` to its full path
* `ffmpeg` and `ffprobe` on your PATH (or set `SCREENSCENE_FFMPEG` and `SCREENSCENE_FFPROBE`)
* An ElevenLabs API key with Text to Speech access, stored as `ELEVENLABS_API_KEY`. Free accounts can use their own premade voices but not library voices through the API

## Limitations

* Choosing regions needs a model that can look at images. If your model cannot, give the regions yourself in the prompt.
* A four beat video takes about one minute to render at the default quality.
* Region accuracy depends on how well the model locates parts of the image. Highlight boxes are only as precise as the coordinates provided.
* Narration uses ElevenLabs credits, about one call per beat.

## Disclosures

* Network calls: HTTPS requests to the ElevenLabs API (`api.elevenlabs.io`) for text to speech. The narration text of each beat is sent. The API key is read through Hermes secret handling and is never written to files or logs by this plugin.
* Subprocesses: runs `manim`, `ffmpeg` and `ffprobe` with fixed arguments and timeouts. No shell is used.
* Files: reads the screenshot path you give it. Writes temporary files to a private temp folder (deleted after each run) and the final MP4 to `~/screenscene_output/`.
* Background processes: none. Rendering runs as a bounded step during the tool call.
* Telemetry: none.

## Installation

```bash
hermes plugins install solocreativeone/screenscene
hermes plugins enable screenscene
```

Then make sure `ELEVENLABS_API_KEY` is set for Hermes. To check a local copy:

```bash
hermes plugins doctor .
```

## License

MIT License. See [LICENSE](LICENSE) for details.

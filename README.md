# ScreenScene

ScreenScene is a Hermes Agent plugin that is being built to generate narrated explainer videos from UI screenshots and structured narration beats. It will animate focus regions with Manim, synthesize voiceover with ElevenLabs, and combine the result into an MP4 video with ffmpeg.

> **Status: early release (v0.1.x).** The `screenscene_render` tool is registered but is a placeholder that returns "not implemented yet". Rendering, narration and muxing arrive in v0.2.0. The behaviors listed under Disclosures describe the planned implementation and are not active in this version.

## Overview

ScreenScene provides one tool, `screenscene_render`. Given a screenshot and a sequence of beats (narration text plus a focus region of the image), the finished plugin will render a synchronized video. The narration audio acts as the master clock: each animation is sized to the measured length of its spoken beat.

## Tools

* `screenscene_render`: Renders an explainer video from a screenshot and narration beats. Placeholder in v0.1.x.

## Requirements (planned for v0.2.0)

* Manim Community Edition (`manim`) installed and on your PATH
* `ffmpeg` installed and on your PATH
* An ElevenLabs API key, supplied through Hermes's configured secret handling

None of these are used by v0.1.x.

## Disclosures

In accordance with Hermes plugin catalog requirements, the following behaviors are disclosed. They describe the planned implementation and take effect only when the renderer ships.

* Network calls: Will make outbound HTTPS requests to the ElevenLabs API for text-to-speech. The narration script text is sent to ElevenLabs, using the user's own API key.
* Subprocesses: Will run `manim` CLI commands to render animations and `ffmpeg` CLI commands to combine video and audio.
* Files written: Will write temporary voiceover audio, intermediate render files, and the final MP4 to disk.
* Background processes: None. Rendering runs as a bounded, synchronous step during tool execution.
* Current behavior (v0.1.x): No network calls, no subprocesses and no files are written.

## Installation

Until the plugin is listed in the Hermes catalog, install it from its repository:

```bash
hermes plugins install solocreativeone/screenscene
hermes plugins enable screenscene
```

To check a local copy:

```bash
hermes plugins doctor .
```

## License

MIT License. See [LICENSE](LICENSE) for details.
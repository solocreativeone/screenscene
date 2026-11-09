# ScreenScene

ScreenScene is a Hermes Agent plugin that generates narrated explainer videos from UI screenshots and structured narration beats. It animates focus regions with Manim, synthesizes voiceover with ElevenLabs, and multiplexes the result into an MP4 video with ffmpeg.

## Overview

ScreenScene provides the `screenscene_render` tool. Given a screenshot and a sequence of narration beats (narration text plus bounding box focus coordinates), the plugin renders a synchronized video presentation.

## Tools

* `screenscene_render`: Renders an explainer video from input screenshots and narration beats.

## Disclosures

In accordance with Hermes plugin catalog requirements, the following behaviors are disclosed:

* Network Calls: Makes outbound HTTPS requests to the ElevenLabs API for text-to-speech audio synthesis. Narration script text is transmitted to ElevenLabs.
* Subprocesses: Executes `manim` CLI commands to render animations and `ffmpeg` CLI commands to mux video and audio tracks.
* Files Written: Writes temporary voiceover audio files, intermediate Manim scene frames, and final output MP4 video files to disk.
* Background Processes: None. All rendering and multiplexing tasks execute as bounded, synchronous operations during tool execution.

## Installation

To test ScreenScene locally with Hermes Agent:

```bash
hermes plugins doctor .
```

To enable the plugin in your Hermes environment:

```bash
hermes plugins enable screenscene
```

## License

MIT License. See [LICENSE](LICENSE) for details.

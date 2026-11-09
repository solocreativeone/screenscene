"""ScreenScene: turn a screenshot into a narrated explainer video (skeleton)."""

import json

SCREENSCENE_RENDER_SCHEMA = {
    "name": "screenscene_render",
    "description": (
        "Turn a screenshot into a short narrated explainer video. "
        "Use when the user gives an image (diagram, dashboard, UI, code) "
        "and asks for an animated, voiced walkthrough. Takes the image path "
        "and a list of beats; each beat has narration text and the region "
        "of the image to focus on. Not implemented yet in this version."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "image_path": {
                "type": "string",
                "description": "Path to the screenshot file",
            },
            "beats": {
                "type": "array",
                "description": "Ordered beats of the walkthrough",
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
                            "description": "Focus box as [x0, y0, x1, y1], values 0 to 1",
                        },
                    },
                    "required": ["narration"],
                },
            },
        },
        "required": ["image_path", "beats"],
    },
}


def screenscene_render(args: dict, **kwargs) -> str:
    """Placeholder handler. Always returns a JSON string."""
    try:
        if not args.get("image_path"):
            return json.dumps({"error": "image_path is required"})
        return json.dumps({"status": "not implemented yet"})
    except Exception as e:
        return json.dumps({"error": f"screenscene_render failed: {e}"})


def register(ctx):
    ctx.register_tool(
        name="screenscene_render",
        toolset="screenscene",
        schema=SCREENSCENE_RENDER_SCHEMA,
        handler=screenscene_render,
    )

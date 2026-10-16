# HotAPI MCP Server

Full coverage of every HotAPI model and feature (image, video, chat, face-swap, tasks, uploads, usage).

## Deploy on mcphosting.io

1. Connect this GitHub repo in [mcphosting.io](https://www.mcphosting.io).
2. Set the environment variable `HOTAPI_KEY=hk_live_...` in the project settings.
3. The entry point is `server.py` (FastMCP Streamable HTTP transport — supported natively).

## Local test

```bash
pip install -r requirements.txt
export HOTAPI_KEY=hk_live_...
python server.py
```

## Key tools

- `list_models` / `get_usage`
- `create_task(model, input_data)` — universal entry point for every endpoint
- `get_task` / `list_tasks` / `cancel_task` / `delete_task_result`
- `chat_completion`
- `generate_image` / `edit_image` / `generate_video` (convenience wrappers)

All media generation is async. Use `create_task` (or a convenience tool) then poll with `get_task` until status is `succeeded`, `failed`, or `cancelled`.

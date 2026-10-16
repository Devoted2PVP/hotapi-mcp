"""
HotAPI MCP Server — full coverage of all models & features.
Host on mcphosting.io (FastMCP + Streamable HTTP).
Set HOTAPI_KEY in the environment.
"""

import os
from typing import Any, Optional, Dict, List
from fastmcp import FastMCP
import httpx

HOTAPI_BASE = "https://api.hotapi.ai/v1"
API_KEY = os.environ.get("HOTAPI_KEY")
if not API_KEY:
    raise RuntimeError("HOTAPI_KEY environment variable is required")

mcp = FastMCP("HotAPI")

async def _request(method: str, path: str, **kwargs) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    headers.update(kwargs.pop("headers", {}))
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.request(method, f"{HOTAPI_BASE}{path}", headers=headers, **kwargs)
        resp.raise_for_status()
        return resp.json() if resp.content else {}

@mcp.tool()
async def list_models() -> Dict[str, Any]:
    """List all available HotAPI models with pricing and capabilities."""
    return await _request("GET", "/models")

@mcp.tool()
async def get_usage() -> Dict[str, Any]:
    """Get current credit usage / balance information."""
    return await _request("GET", "/usage")

@mcp.tool()
async def create_task(
    model: str,
    input_data: Dict[str, Any],
    idempotency_key: Optional[str] = None,
    webhook: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create an async generation task on any HotAPI model.
    Prefer this for full coverage of every image/video/face-swap endpoint.
    
    Examples of model values:
    - z-image-spicy
    - seedream-5.0-lite-spicy/text-to-image
    - seedream-5.0-pro-spicy/image-edit
    - face-swap-spicy
    - wan-2.7-spicy
    - seedance-2.5-spicy/text-to-video
    - berry-1.0-spicy/reference-to-video
    - w3.0-pro-spicy/image-to-video
    ... and every other model listed by list_models()
    """
    headers = {}
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    params = {}
    if webhook:
        params["webhook"] = webhook
    return await _request(
        "POST",
        f"/{model.lstrip('/')}",
        json=input_data,
        headers=headers,
        params=params,
    )

@mcp.tool()
async def get_task(task_id: str) -> Dict[str, Any]:
    """Retrieve the full status and result of a task."""
    return await _request("GET", f"/tasks/{task_id}")

@mcp.tool()
async def list_tasks(
    limit: int = 20,
    status: Optional[str] = None,
    cursor: Optional[str] = None,
    fields: str = "summary",
) -> Dict[str, Any]:
    """List recent tasks. status: pending|queued|processing|succeeded|failed|cancelled|expired|active"""
    params = {"limit": limit, "fields": fields}
    if status:
        params["status"] = status
    if cursor:
        params["cursor"] = cursor
    return await _request("GET", "/tasks", params=params)

@mcp.tool()
async def cancel_task(task_id: str) -> Dict[str, Any]:
    """Cancel a queued or running task (refund only if not yet started)."""
    return await _request("DELETE", f"/tasks/{task_id}")

@mcp.tool()
async def delete_task_result(task_id: str) -> Dict[str, Any]:
    """Delete the result assets of a completed task."""
    return await _request("DELETE", f"/tasks/{task_id}/result")

@mcp.tool()
async def chat_completion(
    model: str,
    messages: List[Dict[str, Any]],
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    tools: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    OpenAI-compatible chat completion.
    Models: qwen3.8-27b-spicy, silly-1.0, etc.
    """
    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        body["max_tokens"] = max_tokens
    if tools:
        body["tools"] = tools
    return await _request("POST", "/chat/completions", json=body)

@mcp.tool()
async def upload_image(image_url: str) -> Dict[str, Any]:
    """
    Helper for image URLs. Pass public HTTPS URLs directly to image-edit / face-swap / reference tools.
    For true local file upload, use HotAPI's /v1/uploads multipart endpoint separately.
    """
    return {"url": image_url, "note": "Pass public HTTPS URLs directly to generation tools."}

@mcp.tool()
async def generate_image(
    prompt: str,
    model: str = "seedream-5.0-lite-spicy/text-to-image",
    size: str = "2K",
    aspect_ratio: Optional[str] = None,
    idempotency_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Quick text-to-image. Default is Seedream Lite. Other options: z-image-spicy, seedream-5.0-pro-spicy/text-to-image, etc."""
    body = {"prompt": prompt, "size": size}
    if aspect_ratio:
        body["aspect_ratio"] = aspect_ratio
    return await create_task(model, body, idempotency_key)

@mcp.tool()
async def edit_image(
    prompt: str,
    image_urls: List[str],
    model: str = "seedream-5.0-lite-spicy/image-edit",
    size: str = "2K",
) -> Dict[str, Any]:
    """Edit or blend images. image_urls: 1 for edit, 2-14 for blend."""
    body = {"prompt": prompt, "image": image_urls if len(image_urls) > 1 else image_urls[0], "size": size}
    return await create_task(model, body)

@mcp.tool()
async def generate_video(
    prompt: str,
    model: str = "seedance-2.5-spicy/text-to-video",
    duration: Optional[int] = None,
    image_url: Optional[str] = None,
    reference_image_urls: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Flexible video generation. Supports text, image, and reference modes depending on the model."""
    body: Dict[str, Any] = {"prompt": prompt}
    if duration:
        body["duration"] = duration
    if image_url:
        body["image_url"] = image_url
    if reference_image_urls:
        body["reference_image_urls"] = reference_image_urls
    return await create_task(model, body)

if __name__ == "__main__":
    mcp.run(transport="streamable-http")

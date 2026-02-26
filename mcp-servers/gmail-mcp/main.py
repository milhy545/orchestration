"""
FastAPI HTTP wrapper for the Gmail MCP server.

Exposes the MCP tool operations as REST endpoints compatible with
the orchestration stack (zen_coordinator).
"""

import logging
import os
import sys
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator

# Configure path so email_client imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from email_client.handlers import handle_call_tool  # noqa: E402
from email_client.config import EMAIL_CONFIG  # noqa: E402

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = FastAPI(
    title="Gmail MCP API",
    description="Gmail email operations – search, send, forward, labels, and more.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)
Instrumentator().instrument(app).expose(app)


# --------------- Models ---------------

class ToolRequest(BaseModel):
    """Generic MCP tool invocation request."""
    arguments: Dict[str, Any] = {}


class ToolResponse(BaseModel):
    tool: str
    result: Any


# --------------- Health ---------------

@app.get("/health")
async def health():
    configured = bool(EMAIL_CONFIG.get("email")) and bool(EMAIL_CONFIG.get("password"))
    return {"status": "ok", "configured": configured}


# --------------- Generic tool call ---------------

async def _call_tool(name: str, arguments: dict) -> dict:
    """Call an MCP tool and return the text content."""
    try:
        results = await handle_call_tool(name, arguments)
        texts = [r.text for r in results if hasattr(r, "text")]
        return {"tool": name, "result": texts[0] if len(texts) == 1 else texts}
    except Exception as e:
        log.error("Tool %s failed: %s", name, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tool/{tool_name}", response_model=ToolResponse)
async def call_tool(tool_name: str, req: ToolRequest):
    """Invoke any registered MCP tool by name."""
    return await _call_tool(tool_name, req.arguments)


# --------------- Convenience endpoints ---------------

class SearchRequest(BaseModel):
    keyword: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    raw_query: Optional[str] = None
    folder: str = "inbox"
    limit: int = 20


@app.post("/gmail/search")
async def search_emails(req: SearchRequest):
    args = {k: v for k, v in req.dict().items() if v is not None}
    return await _call_tool("search-emails", args)


class SendRequest(BaseModel):
    to: List[str]
    subject: str
    content: str
    cc: List[str] = []


@app.post("/gmail/send")
async def send_email(req: SendRequest):
    return await _call_tool("send-email", req.dict())


class ForwardRequest(BaseModel):
    email_id: str
    to: List[str]
    subject_prefix: str = "Fwd: "
    additional_message: str = ""
    cc: List[str] = []


@app.post("/gmail/forward")
async def forward_email(req: ForwardRequest):
    return await _call_tool("forward-email", req.dict())


@app.get("/gmail/email/{email_id}")
async def get_email_content(email_id: str):
    return await _call_tool("get-email-content", {"email_id": email_id})


@app.post("/gmail/count")
async def count_daily_emails(start_date: str, end_date: str):
    return await _call_tool("count-daily-emails", {"start_date": start_date, "end_date": end_date})


@app.get("/gmail/labels")
async def list_labels():
    return await _call_tool("list-labels", {})


class LabelRequest(BaseModel):
    label_name: str


@app.post("/gmail/labels")
async def create_label(req: LabelRequest):
    return await _call_tool("create-label", req.dict())


class ApplyLabelRequest(BaseModel):
    email_id: str
    label_name: str


@app.post("/gmail/labels/apply")
async def apply_label(req: ApplyLabelRequest):
    return await _call_tool("apply-label", req.dict())


class MoveRequest(BaseModel):
    email_id: str
    destination_label: str


@app.post("/gmail/move")
async def move_email(req: MoveRequest):
    return await _call_tool("move-email", req.dict())

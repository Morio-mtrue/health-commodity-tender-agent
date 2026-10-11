from __future__ import annotations

import asyncio
from datetime import timedelta
import json
import os
import shutil
import sys
import uuid
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from orchestrator.store import now


def error_detail(error):
    children=getattr(error,"exceptions",None)
    if children:
        return "; ".join(dict.fromkeys(error_detail(child) for child in children))
    return f"{type(error).__name__}: {error}"


async def invoke(parameters, tool, arguments):
    async with stdio_client(parameters) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            timeout = 660 if tool == "compile_evaluation_plan" and arguments.get("model") else 180
            result = await session.call_tool(tool, arguments, read_timeout_seconds=timedelta(seconds=timeout))
            if result.isError:
                raise ValueError("; ".join(c.text for c in result.content if hasattr(c, "text")))
            if result.structuredContent is not None:
                return result.structuredContent
            return json.loads(next(c.text for c in result.content if hasattr(c,"text")))


async def procurement(store, tool, arguments):
    parameters = StdioServerParameters(command=sys.executable, args=["-m", "mcp_server.server"],
        cwd=str(Path.cwd()), env={**os.environ, "TENDER_CASE_ROOT": str(store.root)})
    try:
        timeout = 660 if tool == "compile_evaluation_plan" and arguments.get("model") else 180
        return await asyncio.wait_for(invoke(parameters, tool, arguments), timeout=timeout)
    except Exception as error:
        detail=error_detail(error)
        store.event("mcp_transport:"+tool, arguments.get("case_id"), arguments, {"error": detail}, "ERROR")
        raise ValueError(detail) from error


async def borrowed_manifest_read(store, case_id):
    script = Path("node_modules/@modelcontextprotocol/server-filesystem/dist/index.js").resolve()
    node = shutil.which("node")
    manifest = store.case_path(case_id, "manifest-v1.json")
    args = {"path": str(manifest)}
    call_id, started = uuid.uuid4().hex, now()
    store.event("filesystem.read_text_file", case_id, args, None, "STARTED", call_id=call_id, started_at=started)
    try:
        if not node or not script.exists():
            raise ValueError("Borrowed Filesystem MCP is not installed; run npm ci")
        params = StdioServerParameters(command=node, args=[str(script), str(store.case_path(case_id))])
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                result = await asyncio.wait_for(session.call_tool("read_text_file", args), timeout=30)
                if result.isError:
                    raise ValueError("Borrowed Filesystem MCP rejected the case manifest")
                contents = "\n".join(c.text for c in result.content if hasattr(c,"text"))
                if json.loads(contents)["id"] != case_id:
                    raise ValueError("Borrowed manifest content mismatch")
                output = {"status": "SUCCESS", "manifest": json.loads(contents)}
        store.event("filesystem.read_text_file", case_id, args, output, "SUCCESS", call_id=call_id, started_at=started)
        return {"status": "SUCCESS", "tool": "filesystem.read_text_file"}
    except Exception as error:
        output = {"status": "UNRESOLVED", "reason": str(error)}
        store.event("filesystem.read_text_file", case_id, args, output, "ERROR", call_id=call_id, started_at=started)
        return output

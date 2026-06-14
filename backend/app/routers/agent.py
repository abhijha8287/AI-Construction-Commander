import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.agents.rca_agent import get_agent, extract_final_answer

router = APIRouter(prefix="/api/agent", tags=["agent"])


class QueryRequest(BaseModel):
    query: str


@router.post("/investigate")
async def investigate(request: QueryRequest):
    """
    Stream the root cause analysis agent reasoning steps via SSE.
    Each on_tool_end event yields a step. Final on_chain_end yields the answer.
    """
    agent = get_agent()

    async def event_stream():
        step = 0
        try:
            async for event in agent.astream_events(
                {"messages": [("user", request.query)]},
                version="v2",
            ):
                event_type = event.get("event", "")
                event_name = event.get("name", "")

                if event_type == "on_tool_start":
                    tool_input = event.get("data", {}).get("input", {})
                    step += 1
                    payload = json.dumps({
                        "step": step,
                        "type": "tool_start",
                        "tool": event_name,
                        "input": tool_input,
                        "done": False,
                    })
                    yield f"data: {payload}\n\n"

                elif event_type == "on_tool_end":
                    tool_output = event.get("data", {}).get("output", "")
                    output_data = tool_output
                    if hasattr(tool_output, "content"):
                        try:
                            output_data = json.loads(tool_output.content)
                        except Exception:
                            output_data = str(tool_output.content)

                    payload = json.dumps({
                        "step": step,
                        "type": "tool_end",
                        "tool": event_name,
                        "result": output_data,
                        "done": False,
                    }, default=str)
                    yield f"data: {payload}\n\n"

                elif event_type == "on_chain_end" and event_name == "LangGraph":
                    output = event.get("data", {}).get("output", {})
                    final = extract_final_answer(output)
                    payload = json.dumps({
                        "step": step + 1,
                        "type": "final",
                        "done": True,
                        "answer": final,
                    }, default=str)
                    yield f"data: {payload}\n\n"

        except Exception as e:
            error_payload = json.dumps({
                "step": step,
                "type": "error",
                "done": True,
                "error": str(e),
            })
            yield f"data: {error_payload}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/query")
async def simple_query(request: QueryRequest):
    """Non-streaming version for testing."""
    agent = get_agent()
    result = await agent.ainvoke({"messages": [("user", request.query)]})
    return extract_final_answer(result)

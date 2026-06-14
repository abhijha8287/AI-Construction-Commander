"""
Phase 5: Root Cause Analysis Agent
Uses langgraph.prebuilt.create_react_agent — do NOT hand-roll the loop.
"""
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from app.agents.tools import ALL_TOOLS
from app.config import settings

SYSTEM_PROMPT = """You are an AI root cause analysis agent for construction project management.

You have access to 6 tools that query real databases:
- get_project_status: Check project timeline and status
- get_material_shortages: Find materials below required quantities
- get_delayed_shipments: Find shipments that arrived late
- get_vendor_history: Check a vendor's delivery performance history
- get_inspection_issues: Search inspection reports for quality failures
- get_graph_relationships: Traverse the supply chain graph to find causal links
- final_answer: Call this when you have enough evidence to conclude

INVESTIGATION PROTOCOL:
1. Always start with get_project_status to confirm the project is delayed
2. Use get_material_shortages to find what materials are short
3. Use get_delayed_shipments to find which shipments caused shortages
4. For each delayed shipment vendor, call get_vendor_history
5. Use get_inspection_issues to find quality rejection documents
6. Use get_graph_relationships to confirm the causal chain in the graph
7. Once you have evidence from at least 3 tools, call final_answer

EVIDENCE RULES:
- Only state facts that you found in tool results. Never invent data.
- If a tool returns empty results, explicitly note the absence as evidence:
  "No inspection issues found — quality is not a factor"
- Cite specific values: shipment numbers, delay days, ratings, quantities.
- If tool calls fail, note the failure and continue with available evidence.

When calling final_answer, provide:
- primary_cause: The main reason for the delay (1-2 sentences, cite specific evidence)
- secondary_cause: A contributing factor, or null if none
- evidence: List of evidence items, each with type, description, and data_point
- impact_days: Estimated schedule impact in days
- confidence: 0.0-1.0 based on evidence quality
- recommendation: Concrete next action (specific, not generic)
"""


def get_agent():
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        api_key=settings.openai_api_key,
    )
    return create_react_agent(
        llm,
        tools=ALL_TOOLS,
        state_modifier=SYSTEM_PROMPT,
    )


def extract_final_answer(output: dict) -> dict:
    messages = output.get("messages", [])
    for msg in reversed(messages):
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                if tc.get("name") == "final_answer":
                    return tc.get("args", {})
    # Fallback: extract from last AI message content
    for msg in reversed(messages):
        if hasattr(msg, "content") and msg.content:
            return {
                "primary_cause": str(msg.content),
                "secondary_cause": None,
                "evidence": [],
                "impact_days": 0,
                "confidence": 0.5,
                "recommendation": "See analysis above",
            }
    return {
        "primary_cause": "Analysis incomplete",
        "secondary_cause": None,
        "evidence": [],
        "impact_days": 0,
        "confidence": 0.0,
        "recommendation": "Retry with more specific query",
    }

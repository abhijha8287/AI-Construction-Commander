"""
Phase 4: Tool Validation Gate
Run each tool in isolation and assert expected values.
All 6 must print PASS before LangGraph is written.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.agents.tools import (
    get_project_status, get_material_shortages, get_delayed_shipments,
    get_vendor_history, get_inspection_issues, get_graph_relationships,
)


async def run_validations():
    print("Phase 4: Tool Validation Gate\n")
    passed = 0
    failed = 0

    # Tool 1
    print("Tool 1: get_project_status('Tower A')")
    try:
        result = await get_project_status.ainvoke({"project_name": "Tower A"})
        assert result.get("status") == "delayed", f"status={result.get('status')}"
        assert result.get("planned_end_date") == "2026-07-15", f"planned_end_date={result.get('planned_end_date')}"
        print(f"  status:           {result['status']}  ✓")
        print(f"  planned_end_date: {result['planned_end_date']}  ✓")
        print("  Tool 1 PASS\n")
        passed += 1
    except Exception as e:
        print(f"  Tool 1 FAIL: {e}\n")
        failed += 1

    # Tool 2
    print("Tool 2: get_material_shortages('Tower A')")
    try:
        result = await get_material_shortages.ainvoke({"project_name": "Tower A"})
        assert any(m["name"] == "Rebar" for m in result), f"Rebar not found in {result}"
        rebar = next(m for m in result if m["name"] == "Rebar")
        assert rebar["actual_quantity"] == 320.0, f"actual_quantity={rebar['actual_quantity']}"
        assert rebar["planned_quantity"] == 500.0, f"planned_quantity={rebar['planned_quantity']}"
        print(f"  Rebar actual:     {rebar['actual_quantity']} of {rebar['planned_quantity']}  ✓")
        print(f"  Shortage:         {rebar['shortage']}  ✓")
        print("  Tool 2 PASS\n")
        passed += 1
    except Exception as e:
        print(f"  Tool 2 FAIL: {e}\n")
        failed += 1

    # Tool 3
    print("Tool 3: get_delayed_shipments('Tower A')")
    try:
        result = await get_delayed_shipments.ainvoke({"project_name": "Tower A"})
        assert any(s["shipment_number"] == "S-102" for s in result), f"S-102 not found in {result}"
        s102 = next(s for s in result if s["shipment_number"] == "S-102")
        assert s102["delay_days"] == 9, f"delay_days={s102['delay_days']}"
        assert s102["vendor_name"] == "ABC Steel", f"vendor={s102['vendor_name']}"
        print(f"  S-102 delay_days: {s102['delay_days']}  ✓")
        print(f"  S-102 vendor:     {s102['vendor_name']}  ✓")
        print("  Tool 3 PASS\n")
        passed += 1
    except Exception as e:
        print(f"  Tool 3 FAIL: {e}\n")
        failed += 1

    # Tool 4
    print("Tool 4: get_vendor_history('ABC Steel')")
    try:
        result = await get_vendor_history.ainvoke({"vendor_name": "ABC Steel"})
        assert result.get("rating") == 2.7, f"rating={result.get('rating')}"
        assert result.get("on_time_rate", 1) < 0.5, f"on_time_rate={result.get('on_time_rate')}"
        assert result.get("total_shipments", 0) >= 4, f"total_shipments={result.get('total_shipments')}"
        print(f"  rating:           {result['rating']}  ✓")
        print(f"  on_time_rate:     {result['on_time_rate']}  ✓")
        print(f"  total_shipments:  {result['total_shipments']}  ✓")
        print(f"  avg_delay_days:   {result['avg_delay_days']}  ✓")
        print("  Tool 4 PASS\n")
        passed += 1
    except Exception as e:
        print(f"  Tool 4 FAIL: {e}\n")
        failed += 1

    # Tool 5
    print("Tool 5: get_inspection_issues('Tower A')")
    try:
        result = await get_inspection_issues.ainvoke({"project_name": "Tower A"})
        assert len(result) > 0, "No inspection issues found"
        assert any(issue.get("status") == "FAILED" for issue in result), f"No FAILED status in {result}"
        assert any("yield strength" in issue.get("content", "").lower() for issue in result), "yield strength not in content"
        top = result[0]
        print(f"  Found:            {top['title']}  ✓")
        print(f"  Status:           {top['status']}  ✓")
        print(f"  Score:            {top['score']}  ✓")
        print("  Tool 5 PASS\n")
        passed += 1
    except Exception as e:
        print(f"  Tool 5 FAIL: {e}\n")
        failed += 1

    # Tool 6
    print("Tool 6: get_graph_relationships('Tower A')")
    try:
        result = await get_graph_relationships.ainvoke({"project_name": "Tower A"})
        assert result.get("vendor") == "ABC Steel", f"vendor={result.get('vendor')}"
        assert result.get("shipment") == "S-102", f"shipment={result.get('shipment')}"
        assert result.get("material") == "Rebar", f"material={result.get('material')}"
        assert result.get("delay_days") == 9, f"delay_days={result.get('delay_days')}"
        print(f"  Vendor:           {result['vendor']}  ✓")
        print(f"  Shipment:         {result['shipment']}  ✓")
        print(f"  Material:         {result['material']}  ✓")
        print(f"  Delay days:       {result['delay_days']}  ✓")
        print("  Tool 6 PASS\n")
        passed += 1
    except Exception as e:
        print(f"  Tool 6 FAIL: {e}\n")
        failed += 1

    print("─" * 50)
    print(f"Results: {passed}/6 PASS, {failed}/6 FAIL")
    if failed == 0:
        print("\nPhase 4 COMPLETE ✓ — all 6 tools pass. LangGraph agent is now safe to build.")
    else:
        print("\nPhase 4 FAILED ✗ — fix failing tools before building the agent.")
        print("Failing tools produce hallucinating agents. Do not proceed.")


if __name__ == "__main__":
    asyncio.run(run_validations())

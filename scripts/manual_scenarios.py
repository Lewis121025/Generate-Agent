"""Manual end-to-end walkthroughs for Creative and General modes.

This script uses FastAPI's TestClient to exercise two realistic tasks:
1. Creative Mode: generate and ship a 30-second SecureSphere promo.
2. General Mode: research 2025 North America EV subsidy policies.

The script explicitly clears external infra env vars so everything runs fully in-memory
for local testing (no Postgres/Redis/Weaviate required).
"""

from __future__ import annotations

import os
from pprint import pprint

from fastapi.testclient import TestClient

# Force local-only mode before importing the FastAPI app when requested
manual_mode = os.environ.get("MANUAL_SCENARIOS_MODE", "real").lower()
if manual_mode in {"local", "mock"}:
    overrides = {
        "DATABASE_URL": "",
        "REDIS_URL": "",
        "VECTOR_DB_TYPE": "none",
        "S3_ENDPOINT_URL": "",
        "LLM_PROVIDER_MODE": "mock",
        "VIDEO_PROVIDER": "mock",
        "TTS_PROVIDER": "mock",
        "SEARCH_PROVIDER": "mock",
        "SCRAPE_PROVIDER": "mock",
    }
    for key, value in overrides.items():
        os.environ[key] = value

from lewis_ai_system.main import app


def run_creative_case(client: TestClient) -> dict:
    """Drive the creative workflow from brief to distribution."""

    create_payload = {
        "tenant_id": "enterprise-demo",
        "title": "SecureSphere Cloud Threat Demo",
        "brief": "30秒宣传片，突出跨区域云威胁检测与自动响应编排。",
        "duration_seconds": 30,
        "style": "cinematic-tech",
        "budget_limit_usd": 120.0,
    }
    resp = client.post("/creative/projects", json=create_payload)
    resp.raise_for_status()
    project = resp.json()["project"]
    project_id = project["id"]
    print(f"[Creative] Created project {project_id} in state {project['state']}")

    resp = client.post(f"/creative/projects/{project_id}/approve-script")
    resp.raise_for_status()
    project = resp.json()["project"]
    print(f"[Creative] Script approved, new state: {project['state']}")

    max_steps = 12
    history: list[str] = [project["state"]]
    while project["state"] != "completed" and max_steps > 0:
        if project["state"] == "preview_ready":
            resp = client.post(f"/creative/projects/{project_id}/approve-preview")
            resp.raise_for_status()
            project = resp.json()["project"]
            history.append(project["state"])
            print(f"[Creative] preview approved -> {project['state']}")
        else:
            resp = client.post(f"/creative/projects/{project_id}/advance")
            resp.raise_for_status()
            project = resp.json()["project"]
            history.append(project["state"])
            print(f"[Creative] advanced -> {project['state']}")
        max_steps -= 1

    if project["state"] != "completed":
        raise RuntimeError("Creative project failed to reach COMPLETED state")

    summary = {
        "project_id": project_id,
        "state_history": history,
        "shot_count": len(project["shots"]),
        "render_manifest": project["render_manifest"],
        "distribution_log": project["distribution_log"],
    }
    print("[Creative] Final summary:")
    pprint(summary)
    return summary


def run_general_case(client: TestClient) -> dict:
    """Run an investigative general-mode session with live tools."""

    create_payload = {
        "tenant_id": "enterprise-demo",
        "goal": "研究2025年北美电动车补贴政策，输出FAQ和引用",
        "max_iterations": 4,
        "budget_limit_usd": 4.0,
    }
    resp = client.post("/general/sessions", json=create_payload)
    resp.raise_for_status()
    session = resp.json()["session"]
    session_id = session["id"]
    print(f"[General] Created session {session_id} (iteration {session['iteration']})")

    max_steps = session["max_iterations"]
    while session["state"] == "active" and max_steps > 0:
        resp = client.post(f"/general/sessions/{session_id}/iterate")
        resp.raise_for_status()
        session = resp.json()["session"]
        print(
            f"[General] iteration={session['iteration']} state={session['state']} spent=${session['spent_usd']:.2f}"
        )
        max_steps -= 1

    final_session = client.get(f"/general/sessions/{session_id}").json()["session"]

    summary = {
        "session_id": session_id,
        "state": final_session["state"],
        "iterations": final_session["iteration"],
        "spent_usd": final_session["spent_usd"],
        "tool_calls": [
            {"tool": call["tool"], "decision_path": call["decision_path"]}
            for call in final_session["tool_calls"]
        ],
        "messages": final_session["messages"],
    }
    print("[General] Final summary:")
    pprint(summary)
    return summary


if __name__ == "__main__":
    with TestClient(app) as client:
        creative_summary = run_creative_case(client)
        general_summary = run_general_case(client)

    print("\nDone. Creative & General walkthroughs complete.")
    print("Creative recap:")
    pprint(creative_summary)
    print("General recap:")
    pprint(general_summary)

"""API source: pull users/posts/comments from JSONPlaceholder as engagement inputs.

Lands under data/raw/api/ and builds data/marts/engagement_events.csv for enrichment.
Offline fallback: reuse prior landing if network fails.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from src.integrations.http_client import get_json

ROOT = Path(__file__).resolve().parents[2]


def _load_cfg() -> dict[str, Any]:
    path = ROOT / "config" / "pipeline.yaml"
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _source_cfg() -> dict[str, Any]:
    cfg = _load_cfg().get("api_source", {})
    base = os.getenv("API_SOURCE_BASE_URL", cfg.get("base_url", "https://jsonplaceholder.typicode.com"))
    return {
        "base_url": base.rstrip("/"),
        "users_path": cfg.get("users_path", "/users"),
        "posts_path": cfg.get("posts_path", "/posts"),
        "comments_path": cfg.get("comments_path", "/comments"),
        "timeout": float(os.getenv("API_HTTP_TIMEOUT", cfg.get("timeout", 20))),
        "retries": int(os.getenv("API_HTTP_RETRIES", cfg.get("retries", 3))),
    }


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def build_engagement_events(users: list, posts: list, comments: list) -> pd.DataFrame:
    """Flatten posts + comments into an engagement_events mart grain."""
    user_name = {u["id"]: u.get("name") or u.get("username") for u in users}
    user_email = {u["id"]: u.get("email") for u in users}
    rows: list[dict[str, Any]] = []
    for p in posts:
        rows.append(
            {
                "event_id": f"post-{p['id']}",
                "event_type": "post",
                "user_id": p.get("userId"),
                "user_name": user_name.get(p.get("userId")),
                "user_email": user_email.get(p.get("userId")),
                "parent_id": None,
                "title": p.get("title"),
                "body": (p.get("body") or "")[:500],
            }
        )
    post_user = {p["id"]: p.get("userId") for p in posts}
    for c in comments:
        pid = c.get("postId")
        rows.append(
            {
                "event_id": f"comment-{c['id']}",
                "event_type": "comment",
                "user_id": post_user.get(pid),
                "user_name": c.get("name"),
                "user_email": c.get("email"),
                "parent_id": f"post-{pid}" if pid is not None else None,
                "title": None,
                "body": (c.get("body") or "")[:500],
            }
        )
    df = pd.DataFrame(rows)
    df["_ingest_ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    df["_source_system"] = "jsonplaceholder"
    return df


def fetch_engagement(*, use_network: bool = True) -> dict[str, Any]:
    scfg = _source_cfg()
    raw_api = ROOT / "data" / "raw" / "api"
    marts = ROOT / "data" / "marts"
    raw_api.mkdir(parents=True, exist_ok=True)
    marts.mkdir(parents=True, exist_ok=True)

    try:
        if not use_network:
            raise ConnectionError("network disabled")
        users = get_json(f"{scfg['base_url']}{scfg['users_path']}", timeout=scfg["timeout"], retries=scfg["retries"])
        posts = get_json(f"{scfg['base_url']}{scfg['posts_path']}", timeout=scfg["timeout"], retries=scfg["retries"])
        comments = get_json(
            f"{scfg['base_url']}{scfg['comments_path']}", timeout=scfg["timeout"], retries=scfg["retries"]
        )
        _write_json(raw_api / "users.json", users)
        _write_json(raw_api / "posts.json", posts)
        _write_json(raw_api / "comments.json", comments)
        events = build_engagement_events(users, posts, comments)
        events.to_csv(marts / "engagement_events.csv", index=False)
        events.to_parquet(marts / "engagement_events.parquet", index=False)
        # Also land raw CSVs for inspection
        pd.DataFrame(users).to_csv(raw_api / "users.csv", index=False)
        pd.DataFrame(posts).to_csv(raw_api / "posts.csv", index=False)
        pd.DataFrame(comments).to_csv(raw_api / "comments.csv", index=False)
        result = {
            "source": "jsonplaceholder",
            "users": len(users),
            "posts": len(posts),
            "comments": len(comments),
            "engagement_events": len(events),
            "mart": str(marts / "engagement_events.csv"),
        }
        (raw_api / "manifest.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"[api_source] engagement_events: {len(events)} rows")
        return result
    except Exception as exc:
        existing = marts / "engagement_events.csv"
        if existing.exists():
            print(f"[api_source] network failed ({exc}); reusing {existing}")
            return {
                "source": "jsonplaceholder",
                "fallback": True,
                "error": str(exc),
                "engagement_events": len(pd.read_csv(existing)),
                "mart": str(existing),
            }
        raise RuntimeError(f"API source failed and no fallback at {existing}: {exc}") from exc


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Pull engagement data from JSONPlaceholder")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args(argv)
    print(json.dumps(fetch_engagement(use_network=not args.offline), indent=2))


if __name__ == "__main__":
    main()

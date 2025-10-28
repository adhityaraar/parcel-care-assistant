import os, asyncio
import datetime
from google.adk.sessions import DatabaseSessionService
from google.adk.memory import VertexAiMemoryBankService

from dotenv import load_dotenv
load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION   = os.getenv("LOCATION")

ADK_DB_URL = os.getenv("ADK_DB_URL")
AGENT_ENGINE_ID = os.getenv("AGENT_ENGINE_ID")  # can be bare ID or full path

APP  = os.getenv("APP_NAME", "cymbal_agent")
USER = os.getenv("ADK_UI_USER_ID", "user")

AGENT_ENGINE_ID = AGENT_ENGINE_ID.split("/")[-1]
MAX_SESSIONS=10

session_service = DatabaseSessionService(db_url=ADK_DB_URL, pool_pre_ping=True, pool_recycle=1800)
memory_service  = VertexAiMemoryBankService(project=PROJECT_ID, location=LOCATION, agent_engine_id=AGENT_ENGINE_ID)

def _extract_sessions(raw):
    if raw is None: return []
    s = getattr(raw, "sessions", None)
    if s is not None: return list(s)
    if isinstance(raw, dict): return list(raw.get("sessions", []))
    if isinstance(raw, (list, tuple)): return list(raw)
    return []

def _get_session_id(item):
    if isinstance(item, dict):
        return item.get("session_id") or item.get("id")
    return getattr(item, "session_id", None) or getattr(item, "id", None)

def _get_ts(item):
    keys = ["updated_at", "updated_time", "created_at", "created_time", "start_time"]
    for k in keys:
        v = item.get(k) if isinstance(item, dict) else getattr(item, k, None)
        if isinstance(v, (int, float)): return float(v)
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00")).timestamp()
            except Exception:
                pass
    return 0.0

async def main():
    print(f"[info] project={PROJECT_ID} location={LOCATION} app={APP} user={USER}")
    raw = await session_service.list_sessions(app_name=APP, user_id=USER)
    sessions = _extract_sessions(raw)
    print(f"[info] fetched {len(sessions)} sessions from DB")

    sessions_sorted = sorted(sessions, key=_get_ts, reverse=True)[:MAX_SESSIONS]

    saved = 0
    for s in sessions_sorted:
        sid = _get_session_id(s)
        if not sid: continue

        full = await session_service.get_session(app_name=APP, user_id=USER, session_id=sid)
        print(f"[debug] ingesting session: {sid}")

        # 🔎 show a couple last user messages to confirm content
        events = getattr(full, "events", []) or []
        for e in events[-3:]:
            role = getattr(e, "role", None) or (e.get("role") if isinstance(e, dict) else None)
            text = getattr(e, "text", None) or (e.get("text") if isinstance(e, dict) else None)
            if text:
                print(f"    {role or ''}: {text[:120]}")

        # 📝 call MB and print what it created
        resp = await memory_service.add_session_to_memory(full)
        try:
            md = resp.model_dump() if hasattr(resp, "model_dump") else None
        except Exception:
            md = None
        if md:
            created = md.get("generated_memories") or md.get("memories") or []
            print(f"    → generated_memories: {len(created)}")
            for i, m in enumerate(created, 1):
                # best-effort fields
                text = m.get("text") or m.get("content") or str(m)
                print(f"      {i}. {text[:160]}")
        else:
            print("    → (response received; could not model_dump, but call succeeded)")
        saved += 1

    print(f"[done] processed {saved} session(s)")

if __name__ == "__main__":
    asyncio.run(main())
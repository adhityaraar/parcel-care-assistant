import os, sys, asyncio
from google.adk.sessions import DatabaseSessionService
from google.adk.memory import VertexAiMemoryBankService

from dotenv import load_dotenv
load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION   = os.getenv("LOCATION")

APP  = os.getenv("APP_NAME", "cymbal_agent")
USER = os.getenv("ADK_UI_USER_ID", "user")

ADK_DB_URL = os.getenv("ADK_DB_URL")
AGENT_ENGINE_ID = os.getenv("AGENT_ENGINE_ID")  # can be bare ID or full path
ENGINE_ID = AGENT_ENGINE_ID.split("/")[-1]

SID = os.environ.get("SESSION_ID") or (sys.argv[1] if len(sys.argv) > 1 else None)
if not SID:
    print("Usage: python scripts/ingest_one.py <SESSION_ID>  (or export SESSION_ID=...)")
    raise SystemExit(2)

session_service = DatabaseSessionService(db_url=ADK_DB_URL, pool_pre_ping=True, pool_recycle=1800)
memory_service  = VertexAiMemoryBankService(project=PROJECT_ID, location=LOCATION, agent_engine_id=ENGINE_ID)

async def main():
    sess = await session_service.get_session(app_name=APP, user_id=USER, session_id=SID)
    if sess is None:
        print(f"[error] session not found in DB for app={APP} user={USER} id={SID}")
        print("        Run: python scripts/list_sessions.py  (copy a valid ID)")
        raise SystemExit(1)

    # optional: peek last turns
    events = getattr(sess, "events", []) or []
    for e in events[-3:]:
        role = getattr(e, "role", None) or (e.get("role") if isinstance(e, dict) else None)
        text = getattr(e, "text", None) or (e.get("text") if isinstance(e, dict) else None)
        if text:
            print(f"  {role or ''}: {text[:160]}")

    await memory_service.add_session_to_memory(sess)
    print(f"[done] saved to Memory Bank: {SID}")

if __name__ == "__main__":
    asyncio.run(main())
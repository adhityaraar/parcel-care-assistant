import os, asyncio
from google.adk.sessions import DatabaseSessionService

from dotenv import load_dotenv
load_dotenv()

APP  = os.getenv("APP_NAME", "cymbal_agent")
USER = os.getenv("ADK_UI_USER_ID", "user")
ADK_DB_URL = os.getenv("ADK_DB_URL")

svc = DatabaseSessionService(db_url=ADK_DB_URL, pool_pre_ping=True, pool_recycle=1800)

def _extract(raw):
    if raw is None: return []
    s = getattr(raw, "sessions", None)
    if s is not None: return list(s)
    if isinstance(raw, dict): return list(raw.get("sessions", []))
    if isinstance(raw, (list, tuple)): return list(raw)
    return []

async def main():
    raw = await svc.list_sessions(app_name=APP, user_id=USER)
    sessions = _extract(raw)
    print(f"found {len(sessions)} sessions for app={APP} user={USER}")
    for i, s in enumerate(sessions, 1):
        sid = getattr(s, "session_id", None) or getattr(s, "id", None) or s.get("session_id") or s.get("id")
        ts  = getattr(s, "last_update_time", None) or s.get("last_update_time") if isinstance(s, dict) else None
        print(f"{i:>2}. {sid}  updated={ts}")

if __name__ == "__main__":
    asyncio.run(main())

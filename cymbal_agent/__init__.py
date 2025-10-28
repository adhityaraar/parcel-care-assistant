import os, atexit
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from .agent import root_agent

from google.adk.memory import VertexAiMemoryBankService

from dotenv import load_dotenv
load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION   = os.getenv("LOCATION")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
ADK_DB_URL = os.getenv("ADK_DB_URL")

def _session_service_from_url(url: str) -> DatabaseSessionService:
    return DatabaseSessionService(
        db_url=url,
        pool_pre_ping=True,
        pool_recycle=1800,
        # echo=True,  # uncomment to see SQL in logs
    )

def _session_service_via_connector() -> DatabaseSessionService:
    # Cloud SQL Python Connector — no IP allowlist needed (for local dev/scripts)
    from google.cloud.sql.connector import Connector, IPTypes
    connector = Connector()
    atexit.register(connector.close)

    inst_conn_name = f"{PROJECT_ID}:{LOCATION}:{os.getenv('CLOUDSQL_INSTANCE','cymbaldb')}"
    def getconn():
        return connector.connect(
            inst_conn_name, "pymysql",
            user=DB_USER,
            password=DB_PASSWORD,
            db=DB_NAME,
            ip_type=IPTypes.PUBLIC,  # PRIVATE if you have VPC
        )

    return DatabaseSessionService(
        db_url="mysql+pymysql://",   # ignored when creator= is provided
        creator=getconn,
        pool_pre_ping=True,
        pool_recycle=1800,
    )

# --- Sessions (short-term) ---
session_service = (
    _session_service_from_url(ADK_DB_URL)
    if ADK_DB_URL else
    _session_service_via_connector()
)

# --- Memory Bank (long-term) ---
from google.adk.memory import VertexAiMemoryBankService

memory_service = None
raw_engine = os.getenv("AGENT_ENGINE_ID")

if raw_engine:
    engine_id_bare = raw_engine.split("/")[-1]          # ALWAYS bare ID
    memory_service = VertexAiMemoryBankService(
        project=PROJECT_ID,
        location=LOCATION or "us-central1",
        agent_engine_id=engine_id_bare,
    )
    print(f"[ADK] Memory Bank ENABLED (engine_id={engine_id_bare})")
else:
    print("[ADK] Memory Bank DISABLED: AGENT_ENGINE_ID not set")

runner_kwargs = dict(agent=root_agent, app_name="cymbal_agent", session_service=session_service)
if memory_service:
    runner_kwargs["memory_service"] = memory_service

runner = Runner(**runner_kwargs)
__all__ = ["runner"]
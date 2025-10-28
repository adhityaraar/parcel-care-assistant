# scripts/search_memory.py
import os, asyncio
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

# mb = VertexAiMemoryBankService(
#     project=PROJECT_ID,
#     location=LOCATION,
#     agent_engine_id=ENGINE_ID,
# )

# QUERIES = [
#     "VisionAI",
#     "favorite project",
#     "favorite",
#     "My favorite project is",
#     "project VisionAI",
#     "preferences",
# ]

# async def run_query(q):
#     # Some builds support top_k
#     try:
#         res = await mb.search_memory(app_name=APP, user_id=USER, query=q, top_k=20)
#     except TypeError:
#         res = await mb.search_memory(app_name=APP, user_id=USER, query=q)

#     memories = getattr(res, "memories", []) or []
#     print(f"\n=== Query: {q!r} → {len(memories)} hit(s)")
#     for i, m in enumerate(memories, 1):
#         text = getattr(m, "text", None) or getattr(m, "content", None) or str(m)
#         score = getattr(m, "score", None) or getattr(m, "relevance_score", None)
#         print(f"{i:>2}. {text}")
#         if score is not None:
#             print(f"    score: {score}")

# async def main():
#     for q in QUERIES:
#         await run_query(q)

# if __name__ == "__main__":
#     asyncio.run(main())

mb = VertexAiMemoryBankService(
    project=PROJECT_ID, location=LOCATION, agent_engine_id=ENGINE_ID
)

async def main():
    res = await mb.search_memory(app_name=APP, user_id=USER, query="VisionAI")
    memories = getattr(res, "memories", []) or []
    if not memories:
        print("(no hits)")
    for i, m in enumerate(memories, 1):
        text = getattr(m, "text", None) or getattr(m, "content", None) or str(m)
        print(f"{i}. {text}")

if __name__ == "__main__":
    asyncio.run(main())
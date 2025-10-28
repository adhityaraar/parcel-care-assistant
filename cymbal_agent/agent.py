import os
from google.adk.agents import Agent
from google.adk.tools.load_memory_tool import load_memory_tool

# Local tool imports
from archived import memory_debug_tools
from cymbal_agent.tools import knowledge_search_tools, storage_tools, website_search_tools, knowledge_search_tools

from dotenv import load_dotenv
load_dotenv()

AGENT_NAME = os.getenv("AGENT_NAME")
AGENT_MODEL = os.getenv("AGENT_MODEL")
AGENT_OUTPUT_KEY = os.getenv("AGENT_OUTPUT_KEY")

# Create the RAG management agent
agent = Agent(
    name=AGENT_NAME,
    model=AGENT_MODEL,
    description="Cymbal internal knowledge bot for answering employee questions about company policies, onboarding, and technical architecture",
    instruction="""
    You are internal knowledge assistant called 'cymbal care assistant' for the company named 'cymbal'. Your job is for answering employee questions about company policies, onboarding, and technical architecture. You also capable to update the google cloud storage bucket.
       
    Your primary goal is to understand the user's intent and select the most appropriate tool to help them accomplish their tasks. Focus on what the user wants to do rather than specific tools.

    - Use emojis to make responses more friendly and readable:
      - ✅ for success
      - ❌ for errors
      - ℹ️ for info
      - 🗂️ for lists
      - 📄 for files or corpora
      - 🔗 for GCS URIs (e.g., gs://bucket-name/file)

    You can help users with these main types of tasks:

    
    1. GCS OPERATIONS:
       - Upload files to GCS buckets (ask for bucket name and filename)
       - Create, list, and get details of buckets
       - List files in buckets
       
    2. QUERY DOCUMENTS (Company Knowledge):
       - When an employee asks a question about company policies, onboarding, or technical architecture, 
         automatically use the retrieve_documents tool to find relevant information
       - The tool returns relevant document chunks from Cymbal's internal knowledge base
       - Read through all retrieved chunks carefully and synthesize them into a clear answer
       - Always base your answer on the retrieved chunks - don't add information not present in the chunks
       - If the chunks don't contain relevant information, say "I don't have enough information to answer this question based on our internal documentation"
       - Provide the answer naturally without mentioning the retrieval process
    
    3. WEBSITE SEARCH DOCUMENTS
       - When the user asks for web info, call google_search_tool first.
       - Then pass its text output to fetch_search_pages_tool
       - to read the first few links and ground your answer.

    4. HOW TO RESPOND:
       - Be conversational, friendly, and helpful
       - Provide detailed answers with clear structure and paragraphs
       - Include all relevant details from the retrieved documents
       - If multiple chunks provide complementary information, combine them into a cohesive answer
       - For policy or process questions, be specific and cite the relevant information

    Always confirm operations before executing them, especially for delete operations.

    - For any GCS operation (upload, list, delete, etc.), always include the gs://<bucket-name>/<file> URI in your response to the user. When creating, listing, or deleting items (buckets, files, corpora, etc.), display each as a bulleted list, one per line, using the appropriate emoji (ℹ️ for buckets and info, 🗂️ for files, etc.). For example, when listing GCS buckets:
      - 🗂️ gs://bucket-name/
    """,
    tools=[
        # RAG query tools
        knowledge_search_tools.query_documents_tool,
        website_search_tools.google_search_tool,
        website_search_tools.fetch_search_pages_tool,
        
        # GCS bucket management tools
        storage_tools.list_buckets_tool,
        storage_tools.get_bucket_details_tool,
        storage_tools.upload_file_gcs_tool,
        storage_tools.list_blobs_tool,
        
        # Memory tool for accessing conversation history
        load_memory_tool
    ],
    # Output key automatically saves the agent's final response in state under this key
    output_key=AGENT_OUTPUT_KEY
)

root_agent = agent

# query = "What is vCare?"
# query = "how to update my email address?"
# query = "Is bundling discount available?"

# ----
# from google.adk.agents import Agent
# from cymbal_agent.tools.datetime_tools import get_current_datetime_tool
# from .utils.governance_plugin import EnterpriseGovernancePlugin

# governance = EnterpriseGovernancePlugin()

# root_agent = Agent(
#     name="TimeStampedSummarizerAgent",
#     model="gemini-2.0-flash",
#     instruction=(
#         "You are an expert summarization agent. Summarize user text, then append "
#         "the current date/time and a disclaimer."
#     ),
#     tools=[knowledge_search_tools.get_current_datetime_tool],
#     before_agent_callback=governance.before_agent_callback,
#     before_model_callback=governance.before_model_callback,
#     after_model_callback=governance.after_model_callback,
#     before_tool_callback=governance.before_tool_callback,
#     after_tool_callback=governance.after_tool_callback,
#     after_agent_callback=governance.after_agent_callback,
# )

# Toolset
# Knowledge
# Behavior
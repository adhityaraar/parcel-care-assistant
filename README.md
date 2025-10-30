# ADK-Based Agentic Assistant with Vertex AI

An **Agentic AI system** built using **Google’s Agent Development Kit (ADK)**.


This assistant acts as a **Supervisor Agent** that receives user requests (text or voice) via **ADK Web UI**, plans multi-step reasoning with full context (prompt, history, tools, memory), executes the required actions, and returns a safe, grounded response.

---

<div align="center">
  <img width="640" height="480" alt="Agent Workflow" src="https://github.com/user-attachments/assets/3f1b26bf-9cd0-49df-b504-aa60e885a4db" />
</div>

---

## Overview

This solution integrates **ADK**, **Vertex AI**, **Cloud SQL**, and **Cloud Run** to enable a fully managed conversational and reasoning agent.  
The ADK Web interface provides a simple UI for chatting or speaking with the agent.  
Each interaction runs through:

1. **Planning & Context Building** – Incorporates prompt, history, memory, tools, and knowledge.
2. **Tool Invocation** – Executes APIs, database lookups, or web/document retrieval.
3. **Guardrails** – Ensures safety, policy compliance, and logging.
4. **Memory Update** – Stores or retrieves short-term (Cloud SQL) and long-term (Memory Bank) context.
5. **Response Aggregation** – Returns final answers to the user with traceability.

---

## Environment Requirements

- Python **3.11+**
- Virtual environment (`conda` / `venv`)
- All credentials and configuration should be defined in `.env`
- Google Cloud SDK ([install guide](https://cloud.google.com/sdk/docs/install))
- Access to:
  - Vertex AI API  
  - Cloud Storage  
  - Cloud SQL  
  - Custom APIs Search

### 1. Installation

```bash
# Create and activate environment
conda create -n adk-agent python=3.11 -y
conda activate adk-agent

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Google Cloud

```bash
# Set your project and region
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
CLOUD_SQL_INSTANCE=cymbal-assistant:us-central1:cymbaldb
DB_USER=cymbal_user
DB_PASSWORD=your_password
DB_NAME=cymbal_session

# Enable required services
gcloud services enable aiplatform.googleapis.com     --project=${GOOGLE_CLOUD_PROJECT}
gcloud services enable storage.googleapis.com     --project=${GOOGLE_CLOUD_PROJECT}
gcloud services enable sqladmin.googleapis.com     --project=${GOOGLE_CLOUD_PROJECT}

# Assign IAM roles
gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT}     --member="user:YOUR_EMAIL@domain.com"     --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT}     --member="user:YOUR_EMAIL@domain.com"     --role="roles/storage.objectAdmin"

# Authentication options
# Option 1 (Recommended for development)
gcloud auth application-default login

# Option 2 (For CI/CD or production)
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

---

## How the Agent Works

<div align="center">
<img width="640" height="480" alt="image" src="https://github.com/user-attachments/assets/4d855404-9d6f-42a2-9d14-f043f3e44d33" />
</div>

1. **User → ADK Web:**  
   Users interact through the built-in ADK web chat interface.
2. **Supervisor Agent:**  
   Coordinates actions between the model and tools.
3. **Model Agent:**  
   Calls Gemini/Gemma models to reason and respond.
4. **Tools Layer:**  
   - 🌐 Website Search  
   - 📄 Document Retrieval  
   - ☁️ Storage Operations (upload, list, detail)
   - 💡 Knowledge Update
5. **Memory:**  
   - **Short-term:** Cloud SQL (session data)  
   - **Long-term:** Vertex AI Memory Bank
6. **Governance:**  
   Logs traces, runs guardrails, and tracks evaluation metrics.

---

## Deploying to Google Cloud Run

### 1. Load your environment
```bash
export AGENT_PATH="./cymbal_agent"
export SERVICE_NAME="cymbal-assistant-service"
export APP_NAME="cymbal_agent"
export GOOGLE_GENAI_USE_VERTEXAI=True

source cymbal_agent/.env
```

### 2. Deploy with ADK CLI
```bash
adk deploy cloud_run --project=$GOOGLE_CLOUD_PROJECT --region=$GOOGLE_CLOUD_LOCATION --service_name=$SERVICE_NAME --app_name=$APP_NAME --with_ui $AGENT_PATH
```

After deployment, ADK will output a **public Cloud Run URL** where the chat UI (ADK Web) is accessible.

Test your Agent:
```bash
Example Question:
- What is SED and when is it required for exports?
- Can used household items or personal effects be shipped to Singapore?
- What is SED and when is it required for exports?
```
---

## 🧭 Summary

| Component | Purpose |
|------------|----------|
| **ADK Agent** | Core orchestration logic |
| **Vertex AI** | Model hosting (Gemini/Gemma) & evaluation |
| **Cloud SQL** | Session memory persistence |
| **Cloud Storage** | Document and file handling |
| **Cloud Run** | Hosting & scaling |
| **Guardrails** | Safety, logging, and policy checks |

---

**Author:** [@adhityaraar](mailto:ardiansyah.raar@gmail.com)  
**License:** Apache 2.0
**Made with ❤️ using Google ADK + Vertex AI**
# Overview

<div align="center">
<img width="640" height="480" alt="image" src="https://github.com/user-attachments/assets/3f1b26bf-9cd0-49df-b504-aa60e885a4db" />
</div>

An ADK-based assistant act as Supervisor Agent receives the user request both chat or voice in simple UI -- ADK Web, builds with full context (prompt, history, knowledge, tools, memory), plans a few steps, calls tools (APIs/search/tasks), runs guardrails for safety & logging, aggregates the results, optionally updates memory, and returns the final answer.


## Quickstart: Environment preparation
- Python 3.11+
- Google Cloud project with Vertex AI API enabled
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
- Access to Vertex AI, Cloud Storage, custom API, Cloud SQL


## Installation

```bash
# Set your project and region
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"

# Enable required Google Cloud services
gcloud services enable aiplatform.googleapis.com \
    --project=${GOOGLE_CLOUD_PROJECT}
gcloud services enable storage.googleapis.com \
    --project=${GOOGLE_CLOUD_PROJECT}

# Assign IAM roles to your user or service account
gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
    --member="user:YOUR_EMAIL@domain.com" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
    --member="user:YOUR_EMAIL@domain.com" \
    --role="roles/storage.objectAdmin"

# Authentication
# Option 1: Recommended for local development
gcloud auth application-default login

# Option 2: For CI/CD or production (service account key)
# Download your service account key and set the path
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"

# Enable sqladmin
gcloud services enable sqladmin.googleapis.com

```


## At glance of How the Agentic AI working

<div align="center">
<img width="640" height="480" alt="image" src="https://github.com/user-attachments/assets/4d855404-9d6f-42a2-9d14-f043f3e44d33" />
</div>

Users interact through ADK Web with an ADK Agent that hands off to a Model Agent (wrapped by guardrails). The Model Agent orchestrates three families of tools: (1) Website search (website/fetch), (2) Document search (retrieve & upsert), and (3) Storage ops (list/detail/upload). If a previous session exists, context is restored from Cloud SQL. Guardrails capture traces and policy checks; Governance evaluation records metrics. Outputs are combined and sent back to the user.




## Set up the environment
put the credentials and variables inside the .env


### Quickstart: Host ADK Agents in Google CloudRun

```bash
export AGENT_PATH="./cymbal_agent"
export SERVICE_NAME="cymbal-assistant-service"
export APP_NAME="cymbal_agent"
export GOOGLE_GENAI_USE_VERTEXAI=True

source cymbal_agent/.env

```

```bash
adk deploy cloud_run \
    --project=$GOOGLE_CLOUD_PROJECT \
    --region=$GOOGLE_CLOUD_LOCATION \
    --service_name=$SERVICE_NAME \
    --app_name=$APP_NAME \
    --with_ui \
    $AGENT_PATH
```

### Central Governance Engine 


### Deployment
python deployment.py

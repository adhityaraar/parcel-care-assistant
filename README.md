# Cymbal Care Assistant
An End-to-End Generative AI Solution for Contextual Knowledge Assistance on Vertex AI

## At Glance Agentic AI with Google ADK at Glance
<div align="center">
<img width="640" height="480" alt="image" src="https://github.com/user-attachments/assets/3f1b26bf-9cd0-49df-b504-aa60e885a4db" />
</div>

Hello

## At Glance Agentic AI workflow
<div align="center">
<img width="640" height="480" alt="image" src="https://github.com/user-attachments/assets/4d855404-9d6f-42a2-9d14-f043f3e44d33" />
</div>

Hello

## Prerequisites

- Python 3.11+
- Google Cloud project with Vertex AI API enabled
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
- Access to Vertex AI, Cloud Storage, custom API, Cloud SQL

## Installation

```bash
# Configure your Google Cloud project
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"

# Enable required Google Cloud services
gcloud services enable aiplatform.googleapis.com --project=${GOOGLE_CLOUD_PROJECT}
gcloud services enable storage.googleapis.com --project=${GOOGLE_CLOUD_PROJECT}

# Set up IAM permissions
gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
    --member="user:YOUR_EMAIL@domain.com" \
    --role="roles/aiplatform.user"
gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
    --member="user:YOUR_EMAIL@domain.com" \
    --role="roles/storage.objectAdmin"

# Set up Gemini API key
# Get your API key from Google AI Studio: https://ai.google.dev/
export GOOGLE_API_KEY=your_gemini_api_key_here

# Set up authentication credentials
# Option 1: Use gcloud application-default credentials (recommended for development)
gcloud auth application-default login

# Option 2: Use a service account key (for production or CI/CD environments)
# Download your service account key from GCP Console and set the environment variable
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json
```

## Set up the environment
put the credentials and variables inside the .env

###
xxxx

### Deploy ADK Agents onto Google Cloud Run

<!-- Set your Google Cloud Project ID -->
export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"

<!-- Set your desired Google Cloud Location -->
export GOOGLE_CLOUD_LOCATION="us-central1"

<!-- Set the path to your agent code directory -->
export AGENT_PATH="./cymbal_agent"

<!-- Set a name for your Cloud Run service (optional) -->
export SERVICE_NAME="cymbal-assistant-service"

# Set an application name for the ADK API server (optional)
# Defaults to the agent directory name if not set
export APP_NAME="cymbal_agent"

# Ensure Vertex AI backend is used if needed by your model config
export GOOGLE_GENAI_USE_VERTEXAI=True

source cymbal_agent/.env
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

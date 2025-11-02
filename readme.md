# Opsimate AI Agent

Conversational agent that plans and executes Opsimate API actions from natural language using Groq LLMs. Runs a simple Flask UI where you type a request, the agent creates a JSON plan, and then executes the steps against your Opsimate backend.

## Features

- **Natural language → actions** via Groq `llama-3.1-8b-instant`.
- **Planned, multi-step execution** with visible step-by-step results.
- **Built-in tools** aligning with Opsimate APIs:
  - `create_user(email, fullName, password, role)`
  - `get_all_users()`
  - `change_role(email, newRole)`
  - `create_secret(displayName, secretType, secret_file)`
  - `create_cluster(name, providerType, secretId)`

## Prerequisites

- Python 3.9+
- A Groq API Key (free): https://console.groq.com/home
- Opsimate backend URL and an API token with sufficient permissions

## Setup

1. Create and activate a virtualenv
   - macOS/Linux:
     - `python3 -m venv .venv`
     - `source .venv/bin/activate`
   - Windows (PowerShell):
     - `python -m venv .venv`
     - `.venv\Scripts\Activate.ps1`

2. Install dependencies
   - `pip install -r requirements.txt`

3. Configure environment
   - Copy `.env-example` to `.env` and fill values, or create `.env` with:
     - `GROQ_API_KEY=your_groq_key`
     - `OPSIMATE_TOKEN=your_opsimate_api_token`
     - `OPSIMATE_URL=http://localhost:3001/api/v1`  
       The app accepts either the base URL (e.g., `/api/v1`) or the users URL (e.g., `/api/v1/users`). It will route correctly for `/secrets` and `/providers` endpoints.

## Run

- `python app.py`
- Open http://localhost:5000

## Try these prompts

- Create a new editor user with email raghav@opsimate.com, full name Raghav Singh, and password Raghav@12345.
- Show me all users in the system.
- Change the role of raghav@opsimate.com to viewer.
- Create a secret called SecKaran with kubeconfig file.
- Create a cluster called KaranNegi1 with the secret SecKaran.
- Change the role of user with email idan@opsimate.com to editor and also show me all the users with their roles.
- Create a kubeconfig secret named SecKaran from /Users/karannegi/Karan-One/kubeconfig and then create a K8S provider named KaranNegi1 using that secret.

## How it works (high level)

- The UI posts your text to `/`.
- The agent asks Groq to produce a JSON plan like:
  ```json
  { "steps": [
    {"function": "create_secret", "arguments": {"displayName":"SecKaran","secretType":"kubeconfig","secret_file":"/abs/path"}},
    {"function": "create_cluster", "arguments": {"name":"KaranNegi1","providerType":"K8S","secretId":"{{last_secret_id}}"}}
  ]}
  ```
- The server executes each tool in order, showing results in the UI.

## Troubleshooting

- 401/403 responses: check `OPSIMATE_TOKEN` and permissions.
- 404/Bad route: verify `OPSIMATE_URL` points to your Opsimate API. The app automatically maps `/users` → base for `/secrets` and `/providers`.
- File paths for kubeconfig must be absolute and readable by the app process.
- Console logs: check terminal output for "DEBUG RESULTS" lines.

## Notes

- Secrets endpoint expects either a file path or raw kubeconfig string in `secret_file`.
- `create_cluster` requires a valid `providerType` (e.g., `K8S`) and an integer `secretId`. The app will substitute `{{last_secret_id}}` automatically after a successful secret creation.


import os
import json
import requests
from flask import Flask, render_template, request, jsonify
from groq import Groq
from dotenv import load_dotenv

# =======================
# ENV + SETUP
# =======================
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPSIMATE_TOKEN = os.getenv("OPSIMATE_TOKEN")
OPSIMATE_URL = os.getenv("OPSIMATE_URL")  # e.g. http://localhost:3001/api/v1

app = Flask(__name__)
client = Groq(api_key=GROQ_API_KEY)


def create_user(email, fullName, password, role):
    headers = {"Authorization": f"Bearer {OPSIMATE_TOKEN}", "Content-Type": "application/json"}
    payload = {"email": email, "fullName": fullName, "password": password, "role": role}
    try:
        res = requests.post(OPSIMATE_URL, headers=headers, json=payload)
        data = res.json()
        if res.ok and data.get("success", False):
            user = data["data"]
            return {"ok": True, "message": f"✅ User '{user['fullName']}' created successfully with role '{user['role']}'.", "data": user}
        else:
            return {"ok": False, "message": f"⚠️ Failed to create user: {json.dumps(data, indent=2)}", "data": data}
    except Exception as e:
        return {"ok": False, "message": f"❌ Error: {str(e)}"}

def get_all_users():
    headers = {"Authorization": f"Bearer {OPSIMATE_TOKEN}", "Content-Type": "application/json"}
    try:
        res = requests.get(OPSIMATE_URL, headers=headers)
        data = res.json()

        if res.ok and data.get("success", False):
            users = data["data"]
            formatted = "\n".join([f"- {u['fullName']} ({u['email']}) — {u['role']}" for u in users])
            return {"ok": True, "message": f"📋 All Users:\n{formatted}", "data": users}
        else:
            return {"ok": False, "message": f"⚠️ Failed to fetch users: {json.dumps(data, indent=2)}"}
    except Exception as e:
        return {"ok": False, "message": f"❌ Error fetching users: {str(e)}"}


def change_role(email, newRole):
    headers = {"Authorization": f"Bearer {OPSIMATE_TOKEN}", "Content-Type": "application/json"}
    payload = {"email": email, "newRole": newRole}
    try:
        res = requests.patch(f"{OPSIMATE_URL}/role", headers=headers, json=payload)
        data = res.json()
        if res.ok and data.get("success", False):
            return {"ok": True, "message": f"🔄 {data.get('message', 'User role updated successfully')} for '{email}' to '{newRole}'.", "data": data}
        else:
            return {"ok": False, "message": f"⚠️ Failed to change role: {json.dumps(data, indent=2)}", "data": data}
    except Exception as e:
        return {"ok": False, "message": f"❌ Error updating role: {str(e)}"}


def create_secret(displayName, secretType, secret_file=None, **_kwargs):
    """
    Create a secret in Opsimate. secret_file may be:
      - None / empty => send empty content
      - a local file path string (absolute path) => read and upload as multipart file
      - a raw string (kubeconfig contents) => upload as a text file
    Returns dict: {"ok": bool, "message": str, "data": parsed_response}
    """
    headers = {"Authorization": f"Bearer {OPSIMATE_TOKEN}"}
    try:
        if isinstance(secret_file, str) and os.path.exists(secret_file):
            # file path provided
            with open(secret_file, "rb") as f:
                files = {"secret_file": (os.path.basename(secret_file), f)}
                data = {"displayName": displayName, "secretType": secretType}
                r = requests.post(f"{OPSIMATE_URL.replace('/users','')}/secrets" if "/users" in OPSIMATE_URL else f"{OPSIMATE_URL}/secrets",
                                  headers=headers, data=data, files=files)
        else:
            # either raw string content or None; send as JSON with content field
            payload = {"displayName": displayName, "secretType": secretType, "secret_file": secret_file or ""}
            headers_json = headers.copy()
            headers_json.update({"Content-Type": "application/json"})
            r = requests.post(f"{OPSIMATE_URL.replace('/users','')}/secrets" if "/users" in OPSIMATE_URL else f"{OPSIMATE_URL}/secrets",
                              headers=headers_json, json=payload)

        try:
            resp_json = r.json()
        except Exception:
            resp_json = {"success": False, "raw": r.text}

        if r.ok and resp_json.get("success", False):
            # attempt to extract created secret id(s)
            secret_id = None
            try:
                # common paths: resp_json['data']['secrets'][0]['id'] or resp_json['data']['id']
                if isinstance(resp_json.get("data"), dict) and resp_json["data"].get("secrets"):
                    secret_id = resp_json["data"]["secrets"][0].get("id")
                elif isinstance(resp_json.get("data"), dict) and resp_json["data"].get("id"):
                    secret_id = resp_json["data"].get("id")
            except Exception:
                secret_id = None

            return {"ok": True, "message": f"🔐 Secret '{displayName}' created.", "data": resp_json, "secret_id": secret_id}
        else:
            return {"ok": False, "message": f"⚠️ Failed to create secret: {json.dumps(resp_json, indent=2)}", "data": resp_json}
    except Exception as e:
        return {"ok": False, "message": f"❌ Error creating secret: {str(e)}"}

def create_cluster(name, providerType, secretId, **_kwargs):
    headers = {"Authorization": f"Bearer {OPSIMATE_TOKEN}", "Content-Type": "application/json"}
    payload = {"name": name, "providerType": providerType, "secretId": int(secretId)}
    try:
        r = requests.post(f"{OPSIMATE_URL.replace('/users','')}/providers" if "/users" in OPSIMATE_URL else f"{OPSIMATE_URL}/providers",
                          headers=headers, json=payload)
        try:
            resp_json = r.json()
        except Exception:
            resp_json = {"success": False, "raw": r.text}
        if r.ok and resp_json.get("success", False):
            return {"ok": True, "message": f"☸️ Cluster '{name}' created using Secret ID {secretId}.", "data": resp_json}
        else:
            return {"ok": False, "message": f"⚠️ Failed to create cluster: {json.dumps(resp_json, indent=2)}", "data": resp_json}
    except Exception as e:
        return {"ok": False, "message": f"❌ Error creating cluster: {str(e)}"}

# =======================
# TOOL REGISTRY
# =======================
TOOLS = {
    "create_user": create_user,
    "get_all_users": get_all_users,
    "change_role": change_role,
    "create_secret": create_secret,
    "create_cluster": create_cluster
}

# =======================
# AGENT PROMPT (planner)
# =======================
SYSTEM_PROMPT = """
You are an AI Ops Agent that can perform multi-step actions using these tools.
Respond ONLY in JSON:

{ "steps": [
    {"function": "<function_name>", "arguments": {...}},
    ...
  ]
}

Supported functions and their arguments:
- create_user(email, fullName, password, role)
- get_all_users()
- change_role(email, newRole)
- create_secret(displayName, secretType, secret_file)   # secret_file may be a local absolute path or raw string
- create_cluster(name, providerType, secretId)           # secretId can be an integer or "{{last_secret_id}}"

If you cannot map the request to these functions, return {"steps":[{"function":"none"}]}
"""

# =======================
# PLAN + EXECUTION (with path detection & substitution)
# =======================
def plan_and_execute(user_text):
    # 1) Ask LLM for plan
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ],
        temperature=0.0,
    )

    content = response.choices[0].message.content.strip()

    # parse JSON safely
    try:
        parsed = json.loads(content)
        steps = parsed.get("steps", [])
    except Exception as e:
        return [{"error": f"⚠️ Could not parse LLM output as JSON: {str(e)}", "raw": content}]

    results = []
    context = {}  # will hold last_secret_id etc.

    for idx, step in enumerate(steps, start=1):
        fn = step.get("function")
        args = step.get("arguments", {}) or {}
        results.append({"step": idx, "action": fn, "args": args, "result": None})

        if fn not in TOOLS:
            results[-1]["result"] = {"ok": False, "message": f"Unknown function '{fn}'"}
            continue

        # --- Substitute placeholders like "{{last_secret_id}}" with actual values ---
        for k, v in list(args.items()):
            # If value is placeholder like "{{last_secret_id}}"
            if isinstance(v, str) and v.startswith("{{") and v.endswith("}}"):
                key = v.strip("{} ")
                if key in context:
                    args[k] = context[key]
            # If arg is a local path (string starting with '/' and exists), keep as-is;
            # our create_secret will detect path and open file.
            if isinstance(v, str) and v.startswith("/") and os.path.exists(v):
                # preserve path string; create_secret will open it
                args[k] = v

        # Execute the function
        try:
            outcome = TOOLS[fn](**args)
        except TypeError as e:
            outcome = {"ok": False, "message": f"TypeError calling {fn}: {e}"}
        except Exception as e:
            outcome = {"ok": False, "message": f"Exception calling {fn}: {e}"}

        results[-1]["result"] = outcome

        # If create_secret succeeded and returned secret_id, store it
        if fn == "create_secret" and isinstance(outcome, dict) and outcome.get("ok"):
            sid = outcome.get("secret_id") or (outcome.get("data", {}).get("data", {}).get("secrets", [{}])[0].get("id") if isinstance(outcome.get("data"), dict) else None)
            # fallback: try to dig in various shapes
            if not sid:
                # try common places inside outcome['data']
                d = outcome.get("data")
                if isinstance(d, dict):
                    # case: d = {"secrets":[{"id":...}]}
                    if d.get("secrets") and isinstance(d["secrets"], list) and d["secrets"]:
                        sid = d["secrets"][0].get("id")
                    # case: d = {"data": {"secrets":[...]}}
                    if d.get("data") and isinstance(d["data"], dict) and d["data"].get("secrets"):
                        sid = d["data"]["secrets"][0].get("id")
            if sid:
                context["last_secret_id"] = sid

    return {"steps": results, "context": context}


# =======================
# FLASK ROUTES
# =======================
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        text = request.form.get("user_input")
        results = plan_and_execute(text)

        # 🧩 If model returns wrapped dict
        if isinstance(results, dict) and "steps" in results:
            steps = results["steps"]
        elif isinstance(results, list):
            steps = results
        else:
            steps = [{"step": 0, "action": "unknown", "result": str(results)}]

        print("DEBUG RESULTS:", json.dumps(steps, indent=2))  # ✅ real-time debug
        return jsonify(steps)
    return render_template("index.html")


if __name__ == "__main__":
    print("🚀 Opsimate Multi-Agent running at: http://127.0.0.1:5000")
    app.run(debug=True)

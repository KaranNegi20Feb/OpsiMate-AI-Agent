import os
import json
import requests
from flask import Flask, render_template, request, jsonify
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPSIMATE_TOKEN = os.getenv("OPSIMATE_TOKEN")
OPSIMATE_URL = os.getenv("OPSIMATE_URL")  # http://localhost:3001/api/v1/users

# Flask app setup
app = Flask(__name__)
client = Groq(api_key=GROQ_API_KEY)


# === TOOL 1: Create user ===
def create_user(email, fullName, password, role):
    """Create a new user via the Opsimate API."""
    headers = {
        "Authorization": f"Bearer {OPSIMATE_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "email": email,
        "fullName": fullName,
        "password": password,
        "role": role
    }

    try:
        res = requests.post(OPSIMATE_URL, headers=headers, json=payload)
        data = res.json()

        if res.ok and data.get("success", False):
            user = data["data"]
            return f"✅ User '{user['fullName']}' created successfully with role '{user['role']}'."
        else:
            return f"⚠️ Failed to create user: {json.dumps(data, indent=2)}"
    except Exception as e:
        return f"❌ Error: {str(e)}"


# === TOOL 2: Get all users ===
def get_all_users():
    """Fetch all users from the Opsimate API."""
    headers = {
        "Authorization": f"Bearer {OPSIMATE_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        res = requests.get(OPSIMATE_URL, headers=headers)
        data = res.json()

        if res.ok and data.get("success", False):
            users = data["data"]
            formatted = "\n".join([f"- {u['fullName']} ({u['email']}) — {u['role']}" for u in users])
            return f"📋 All Users:\n{formatted}"
        else:
            return f"⚠️ Failed to fetch users: {json.dumps(data, indent=2)}"
    except Exception as e:
        return f"❌ Error fetching users: {str(e)}"


# === TOOL 3: Change user role ===
def change_role(email, newRole):
    """Change the role of a user using the Opsimate API."""
    headers = {
        "Authorization": f"Bearer {OPSIMATE_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {"email": email, "newRole": newRole}  # ✅ key fixed!

    try:
        res = requests.patch(f"{OPSIMATE_URL}/role", headers=headers, json=payload)
        data = res.json()

        if res.ok and data.get("success", False):
            return f"🔄 {data.get('message', 'User role updated successfully')} for '{email}' to '{newRole}'."
        else:
            return f"⚠️ Failed to change role: {json.dumps(data, indent=2)}"
    except Exception as e:
        return f"❌ Error updating role: {str(e)}"



# === TOOL REGISTRY ===
TOOLS = {
    "create_user": create_user,
    "get_all_users": get_all_users,
    "change_role": change_role,
}


# === SYSTEM PROMPT ===
SYSTEM_PROMPT = """
You are an AI Agent that manages Opsimate users via an API.
Always respond ONLY in JSON format as:
{"function": "<function_name>", "arguments": {...}}

Available functions:
1. create_user(email, fullName, password, role)
2. get_all_users()
3. change_role(email, newRole)

If unsure, return {"function": "none"}.
"""


# === CALL MODEL ===
def call_ai_agent(prompt):
    """Send user command to Groq model and interpret JSON response."""
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",  # ✅ fast and supported
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
    )

    content = response.choices[0].message.content.strip()

    try:
        data = json.loads(content)
        fn_name = data.get("function")
        args = data.get("arguments", {})

        if fn_name in TOOLS:
            result = TOOLS[fn_name](**args)
            return result
        else:
            return "🤖 I’m not sure what to do."
    except json.JSONDecodeError:
        return f"⚠️ Model output not JSON: {content}"
    except Exception as e:
        return f"❌ Error executing function: {str(e)}"


# === FLASK ROUTES ===
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_input = request.form.get("user_input")
        result = call_ai_agent(user_input)
        return jsonify({"response": result})
    return render_template("index.html")


if __name__ == "__main__":
    print("🚀 Opsimate AI Agent running at: http://127.0.0.1:5000")
    app.run(debug=True)

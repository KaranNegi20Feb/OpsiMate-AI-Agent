### GET A GROQ API KEY, IT'S FREE.
Goto: https://console.groq.com/home
Click on the API keys tab.
Click on the + button to create a new API key.
Name it OpsimateAI
Copy the API key.
create a .env file and put it in the .env file from the .env-example file.

### Steps to run the app:

create a venv: `python3 -m venv path/to/venv`
activate the venv: `source path/to/venv/bin/activate`
install the requirements.txt file by `pip install -r requirements.txt`
run the app.py file by `python app.py`
open http://localhost:5000 in your browser.

### Some basic things the agent can perform:
Create a new editor user with email raghav@opsimate.com , full name Raghav Singh, and password Raghav@12345.
Show me all users in the system.
Change the role of raghav@opsimate.com to viewer.
Create a secret called SecKaran with kubeconfig file.
Create a cluster called KaranNegi1 with the secret SecKaran.
Change the role of user with email idan@opsimate.com to editor and also show me all the users with their roles
Create a kubeconfig secret named SecKaran from /Users/karannegi/Karan-One/kubeconfig and then create a K8S provider named KaranNegi1 using that secret.




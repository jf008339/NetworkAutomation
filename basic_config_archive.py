import requests
import base64
import json
import urllib3
import getpass
import time

urllib3.disable_warnings()

# DNA Center Connection Details
username = "devnetuser"
password = "Cisco123!"  # This is unsecure - use environment variables or getpass library instead
url = "https://sandboxdnac.cisco.com"
use_ssl_verification = False  # Always set to 'True' in production environments

# ------------------ Connect to DNA Center ------------------

# Generate Base64 login string
auth_string = f"{username}:{password}"
auth_string = auth_string.encode("ascii")
auth_string = base64.b64encode(auth_string)
auth_string = str(auth_string, "utf-8")
auth_string = f"Basic {auth_string}"

# Get Authentication Token from DNA Center API
headers = {"Authorization": auth_string}
response = requests.post(
    f"{url}/dna/system/api/v1/auth/token", headers=headers, verify=use_ssl_verification
)
response_data = json.loads(response.text)
authToken = response_data["Token"]

# ------------------ Config-Archive Task ------------------

# Get the list of devices' uuid
headers = {"x-auth-token": authToken}
response = requests.get(
    f"{url}/dna/intent/api/v1/network-device",
    headers=headers,
    verify=use_ssl_verification,
)
response_data = json.loads(response.text)

devices_uiids = [device["id"] for device in response_data["response"]]
# print(devices_uiids)

# Trigger a Config-Archive Task
headers = {
    "x-auth-token": authToken,
    "Content-Type": "application/json",
    "Accept": "application/json",
}
payload = {"deviceId": devices_uiids, "password": "Cisco123!"}

response_data = requests.post(
    f"{url}/dna/intent/api/v1/network-device-archive/cleartext",
    headers=headers,
    data=json.dumps(payload),
)

task_id = json.loads(response_data.text)["response"]["taskId"]
# print(task_id)

# Wait for the Task to be completed and collect the file URL
attempts = 5
wait_time = 10

for _ in range(attempts):
    time.sleep(wait_time)

    headers = {"x-auth-token": authToken}
    response = requests.get(
        f"{url}/dna/intent/api/v1/task/{task_id}",
        headers=headers,
        verify=use_ssl_verification,
    )

    task_data = response.json()["response"]
    #print(task_data)

    if task_data["isError"]:
        reason = task_data.get("failureReason", task_data["progress"])
        raise ValueError(f"Async task error: {reason}")

    if "endTime" in task_data:
        file_url = task_data["additionalStatusURL"]
        break

# ------------------ Importing Config-Archive ------------------
print(file_url)
headers = {"x-auth-token": authToken}

file_stream = requests.get(f"{url}{file_url}", headers=headers, stream=True)

with open('config-archive.zip', 'wb') as local_file:
    for data in file_stream:
        local_file.write(data)

print('🥳 Done')

import requests
import json

# The URL of your API Gateway endpoint
url = "https://telemetry.englobe-pdf-flow.brandongorman.me/telemetry"

# Sample data to send
data = {
    "device": "DeviceIdentifier123",
    "data": 100, 
    "info": "Additional information (optional)"
}

# Convert the data to JSON
json_data = json.dumps(data)

# Headers, set 'Content-Type' to 'application/json'
headers = {
    "Content-Type": "application/json"
}

# Sending the POST request
response = requests.post(url, data=json_data, headers=headers)

# Printing the response
print("Status Code:", response.status_code)
print("Response Body:", response.text)
print(response)

# The URL of your API Gateway endpoint
url = "https://telemetry.englobe-pdf-flow.brandongorman.me/test"

# Sending the GET request
response = requests.get(url)

# Printing the response
print("Status Code:", response.status_code)
print("Response Body:", response.text)

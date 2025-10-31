import json, requests

code = input("Paste your authorization code here:\n").strip()

with open("credentials.json") as f:
    creds = json.load(f)["installed"]

data = {
    "code": code,
    "client_id": creds["client_id"],
    "client_secret": creds["client_secret"],
    "redirect_uri": creds["redirect_uris"][0],
    "grant_type": "authorization_code",
}

r = requests.post("https://oauth2.googleapis.com/token", data=data)
if r.status_code == 200:
    token_data = r.json()
    with open("token.json", "w") as f:
        json.dump(token_data, f, indent=2)
    print("\n✅ token.json created successfully!\n")
else:
    print("\n❌ Failed to exchange code.\n", r.text)

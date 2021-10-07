
from google.cloud import secretmanager_v1
from pathlib import Path

client = secretmanager_v1.SecretManagerServiceClient()

# Access the secret version.
name = "projects/gebwai-1608107987653/secrets/dotenv-thanakan-prod/versions/1"
response = client.access_secret_version(request={"name": name})


payload = response.payload.data.decode("UTF-8")

out_file = Path('.env')

with out_file.open('w') as f:
    f.write(payload)

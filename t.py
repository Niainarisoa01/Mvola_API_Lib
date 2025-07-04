from datetime import datetime, timezone

# Date de la requête au format requis
request_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

print(request_date)
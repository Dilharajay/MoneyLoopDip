import json

# Load Pipfile.lock
with open("Pipfile.lock") as f:
    lock_data = json.load(f)

# Process default (production) packages
with open("requirements.txt", "w") as req_file:
    for pkg, info in lock_data["default"].items():
        version = info.get("version", "")
        line = f"{pkg}{version}"
        req_file.write(line + "\n")

# Optional: generate dev-requirements.txt
with open("dev-requirements.txt", "w") as dev_file:
    for pkg, info in lock_data.get("develop", {}).items():
        version = info.get("version", "")
        line = f"{pkg}{version}"
        dev_file.write(line + "\n")

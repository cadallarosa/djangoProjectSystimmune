import requests
import sseclient

TRAVERSAL_START_URL = "http://django.systimmune.net:3000/api/traverse/start"
TRAVERSAL_PROGRESS_URL = "http://django.systimmune.net:3000/api/traverse/progress"

def start_traversal():
    print("🚀 Starting OPC UA traversal...")
    try:
        requests.get(TRAVERSAL_START_URL, stream=True)
    except Exception as e:
        print(f"❌ Failed to start traversal: {e}")
        return False
    return True

def monitor_progress():
    print("📡 Monitoring traversal progress...")
    try:
        response = requests.get(TRAVERSAL_PROGRESS_URL, stream=True)
        client = sseclient.SSEClient(response)

        for event in client.events():
            if not event.data.strip():
                continue

            try:
                data = eval(event.data) if isinstance(event.data, str) else event.data
                print(f"🔄 Status: {data['stats']['status']} | Folders: {data['stats']['completedFolders']}/{data['stats']['totalFolders']} | Vars: {data['stats']['variablesFound']}")
                if data.get("complete"):
                    print("✅ Traversal complete.")
                    return True
            except Exception as err:
                print("⚠️ Error parsing SSE event:", err)

    except Exception as e:
        print(f"❌ Error during SSE monitoring: {e}")
    return False

def main():
    if start_traversal():
        completed = monitor_progress()
        if completed:
            print("📦 Running transfer_OPCUA_to_db()")
            transfer_OPCUA_to_DB()
        else:
            print("❌ Traversal failed to complete.")
    else:
        print("❌ Could not start traversal.")

if __name__ == "__main__":
    main()

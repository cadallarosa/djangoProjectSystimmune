from celery import shared_task
import requests

@shared_task
def trigger_import_task():
    try:
        res = requests.post("http://django.systimmune.net:3000/api/traverse/start", timeout=20)
        if res.status_code == 200:
            return "✅ Import triggered successfully."
        return f"⚠️ Server responded with: {res.status_code} - {res.text}"
    except Exception as e:
        return f"❌ Error triggering import: {e}"


from celery import shared_task
import datetime

@shared_task
def test_scheduled_print():
    print(f"🕒 Test task ran at {datetime.datetime.now()}")


@shared_task
def trigger_auto_traversal():
    try:
        response = requests.post("http://localhost:3000/api/traverse/start-auto", timeout=300)  # 5 min timeout
        response.raise_for_status()
        return {
            "status": "success",
            "message": response.json()
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": str(e)
        }

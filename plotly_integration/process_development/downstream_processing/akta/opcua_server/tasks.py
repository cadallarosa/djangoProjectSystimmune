# tasks.py
# Location: plotly_integration/process_development/downstream_processing/akta/opcua_server/tasks.py

from celery import shared_task
import requests
import time
import datetime
from django.conf import settings

# Configuration
NODEJS_SERVER = "http://localhost:3000"
CHECK_INTERVAL = 30  # Check every 30 seconds
MAX_WAIT_TIME = 3600  # Maximum 1 hour wait for traversal


@shared_task(name='plotly_integration.run_complete_pipeline')
def run_complete_import_pipeline():
    """
    Run the complete import pipeline:
    1. Start OPC UA traversal
    2. Wait for traversal to complete
    3. Run historical data import
    """
    results = {
        "start_time": datetime.datetime.now().isoformat(),
        "traversal": {},
        "import": {},
        "status": "started"
    }

    # Step 1 & 2: Traversal
    try:
        # Start the traversal
        print("🚀 Starting OPC UA traversal...")
        start_response = requests.post(
            f"{NODEJS_SERVER}/api/traverse/start-optimized",
            timeout=30
        )
        start_response.raise_for_status()

        if not start_response.json().get('success'):
            raise Exception("Failed to start traversal")

        results["traversal"]["started_at"] = datetime.datetime.now().isoformat()
        print("✅ Traversal started successfully")

        # Wait for traversal to complete
        print("⏳ Waiting for traversal to complete...")
        elapsed = 0
        last_processed = 0

        while elapsed < MAX_WAIT_TIME:
            time.sleep(CHECK_INTERVAL)
            elapsed += CHECK_INTERVAL

            try:
                status_response = requests.get(
                    f"{NODEJS_SERVER}/api/traverse/stats",
                    timeout=10
                )
                status_response.raise_for_status()
                stats = status_response.json()

                is_active = stats.get('active', False)
                processed = stats.get('processedFolders', 0)
                total = stats.get('totalFolders', 0)
                errors = stats.get('errors', 0)
                inserted = stats.get('insertedRecords', 0)

                # Check if manually stopped
                if stats.get('manuallyStopped', False):
                    print("⚠️ Traversal was manually stopped")
                    results["traversal"]["manually_stopped"] = True
                    results["status"] = "stopped"
                    return results

                # Log progress
                if processed != last_processed:
                    print(f"📊 Progress: {processed}/{total} folders, {inserted} records inserted, {errors} errors")
                    last_processed = processed

                if not is_active:
                    # Traversal completed!
                    results["traversal"]["completed_at"] = datetime.datetime.now().isoformat()
                    results["traversal"]["stats"] = stats
                    results["traversal"]["duration_seconds"] = elapsed
                    print(f"✅ Traversal completed! Processed {processed} folders, inserted {inserted} records")
                    break

            except Exception as e:
                print(f"⚠️ Error checking status: {e}")

        else:
            # Timeout reached
            results["error"] = f"Traversal did not complete within {MAX_WAIT_TIME} seconds"
            results["status"] = "timeout"
            return results

    except Exception as e:
        # Traversal failed
        print(f"❌ Traversal failed: {e}")
        results["traversal"]["error"] = str(e)
        results["status"] = "traversal_failed"
        return results

    # Step 3: Run the Python import
    print("\n🔄 Starting historical data import...")
    results["import"]["started_at"] = datetime.datetime.now().isoformat()

    try:
        # Import and run the function directly
        from plotly_integration.process_development.downstream_processing.akta.opcua_server.read_historical_data import \
            process_opcua_node_ids

        start_time = "2013-01-01T00:00:00"
        end_time = datetime.datetime.now().isoformat()

        # Run the import
        process_opcua_node_ids(start_time, end_time)

        results["import"]["completed_at"] = datetime.datetime.now().isoformat()
        results["import"]["status"] = "success"
        results["status"] = "completed"
        print("✅ Historical data import completed successfully")

    except Exception as e:
        results["import"]["error"] = str(e)
        results["import"]["status"] = "failed"
        results["status"] = "import_failed"
        print(f"❌ Import failed: {e}")

    results["completed_at"] = datetime.datetime.now().isoformat()

    # Log final summary
    duration = (datetime.datetime.fromisoformat(results["completed_at"]) -
                datetime.datetime.fromisoformat(results["start_time"])).total_seconds()
    print(f"\n{'=' * 60}")
    print(f"Pipeline completed in {duration:.1f} seconds")
    print(f"Status: {results['status']}")
    print(f"{'=' * 60}")

    return results


@shared_task(name='plotly_integration.run_import_only')
def run_import_only():
    """
    Run only the Python import script.
    Use this when you already have traversal data and just want to import unprocessed records.
    """
    try:
        print("🚀 Starting OPC UA historical data import...")

        from plotly_integration.process_development.downstream_processing.akta.opcua_server.read_historical_data import \
            process_opcua_node_ids
        from plotly_integration.models import AktaNodeIds

        # Check how many need import
        unimported_count = AktaNodeIds.objects.filter(imported=False).count()
        print(f"📊 Found {unimported_count} unimported records")

        if unimported_count == 0:
            return {
                "status": "success",
                "message": "No unimported records found",
                "timestamp": datetime.datetime.now().isoformat()
            }

        start_time = "2013-01-01T00:00:00"
        end_time = datetime.datetime.now().isoformat()

        # Run the import
        process_opcua_node_ids(start_time, end_time)

        # Check results
        still_unimported = AktaNodeIds.objects.filter(imported=False).count()
        imported_count = unimported_count - still_unimported

        return {
            "status": "success",
            "message": f"Imported {imported_count} records successfully",
            "processed": imported_count,
            "remaining": still_unimported,
            "timestamp": datetime.datetime.now().isoformat()
        }

    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()

        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.datetime.now().isoformat()
        }


@shared_task(name='plotly_integration.run_traversal_only')
def run_traversal_only():
    """
    Run only the traversal part.
    Use this to discover new OPC UA nodes without importing historical data.
    """
    try:
        print("🚀 Starting OPC UA traversal...")

        response = requests.post(
            f"{NODEJS_SERVER}/api/traverse/start-optimized",
            timeout=30
        )
        response.raise_for_status()

        if response.json().get('success'):
            print("✅ Traversal started successfully")
            return {
                "status": "started",
                "response": response.json(),
                "timestamp": datetime.datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "error": "Failed to start traversal",
                "response": response.json(),
                "timestamp": datetime.datetime.now().isoformat()
            }

    except Exception as e:
        print(f"❌ Failed to start traversal: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.datetime.now().isoformat()
        }


@shared_task(name='plotly_integration.check_traversal_status')
def check_traversal_status():
    """Check current traversal status"""
    try:
        response = requests.get(
            f"{NODEJS_SERVER}/api/traverse/stats",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e), "timestamp": datetime.datetime.now().isoformat()}


@shared_task(name='plotly_integration.stop_traversal')
def stop_traversal():
    """Stop the currently running traversal"""
    try:
        response = requests.post(
            f"{NODEJS_SERVER}/api/traverse/stop",
            timeout=10
        )
        response.raise_for_status()
        print("🛑 Traversal stop requested")
        return {"status": "stopped", "timestamp": datetime.datetime.now().isoformat()}
    except Exception as e:
        return {"error": str(e), "timestamp": datetime.datetime.now().isoformat()}


@shared_task(name='plotly_integration.check_import_status')
def check_import_status():
    """
    Check how many records need import.
    Useful for monitoring and deciding when to run imports.
    """
    from plotly_integration.models import AktaNodeIds, AktaResult

    total_nodes = AktaNodeIds.objects.count()
    imported_nodes = AktaNodeIds.objects.filter(imported=True).count()
    unimported_nodes = AktaNodeIds.objects.filter(imported=False).count()
    total_results = AktaResult.objects.count()

    percentage = round((imported_nodes / total_nodes * 100), 2) if total_nodes > 0 else 0

    status_msg = f"📊 Import Status: {imported_nodes}/{total_nodes} imported ({percentage}%)"
    if unimported_nodes > 0:
        status_msg += f" - {unimported_nodes} remaining"

    print(status_msg)

    return {
        "total_nodes": total_nodes,
        "imported": imported_nodes,
        "unimported": unimported_nodes,
        "percentage": percentage,
        "total_results": total_results,
        "status_message": status_msg,
        "timestamp": datetime.datetime.now().isoformat()
    }


@shared_task(name='plotly_integration.cleanup_old_results')
def cleanup_old_results(days_to_keep=30):
    """
    Optional task to clean up old task results from django_celery_results.
    Schedule this weekly to keep the database clean.
    """
    try:
        from django_celery_results.models import TaskResult
        from django.utils import timezone
        from datetime import timedelta

        cutoff_date = timezone.now() - timedelta(days=days_to_keep)

        # Count before deletion
        old_results = TaskResult.objects.filter(date_created__lt=cutoff_date)
        count = old_results.count()

        # Delete old results
        old_results.delete()

        print(f"🧹 Cleaned up {count} task results older than {days_to_keep} days")

        return {
            "status": "success",
            "deleted_count": count,
            "cutoff_date": cutoff_date.isoformat(),
            "timestamp": datetime.datetime.now().isoformat()
        }

    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.datetime.now().isoformat()
        }


@shared_task(name='plotly_integration.health_check')
def health_check():
    """
    Simple health check task to verify Celery is working.
    Can be scheduled every hour to ensure the system is running.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "message": "Celery worker is running"
    }
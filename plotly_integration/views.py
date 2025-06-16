# views.py
from django.http import JsonResponse
from datetime import datetime
import traceback
# from plotly_integration.process_development.downstream_processing.akta.opcua_server.read_historical_data import process_opcua_node_ids
#
# def trigger_opc_import(request):
#     try:
#         start_time = "2013-01-01T00:00:00"
#         end_time = datetime.now().isoformat()
#         process_opcua_node_ids(start_time, end_time)
#         return JsonResponse({"success": True, "message": "✅ OPC import completed."})
#     except Exception as e:
#         return JsonResponse({
#             "success": False,
#             "error": str(e),
#             "trace": traceback.format_exc()
#         }, status=500)

import os
from opcua import Client, ua
from datetime import datetime, timedelta

PKI_DIR = r"C:\Users\cdallarosa\DataAlchemy\PythonProject1\pki"
CLIENT_CERT = os.path.join(PKI_DIR, "own/certs/OWN.cer")
CLIENT_KEY = os.path.join(PKI_DIR, "own/private/uaexpert_privatekey.pem")
SERVER_CERT = os.path.join(PKI_DIR, "trusted/certs/HDAServer [84CD0A9C66CC7AA72575C3DBBDCFF83B0F84BCC1].der")
SERVER_URL = "opc.tcp://opcsrv:60434/OPC/HistoricalAccessServer"

def get_opc_client():
    client = Client(SERVER_URL)
    client.application_uri = "urn:SI-CF8MJX3:UnifiedAutomation:UaExpert"
    client.set_security_string(f"Basic256Sha256,SignAndEncrypt,{CLIENT_CERT},{CLIENT_KEY},{SERVER_CERT}")
    client.set_user("OPCuser")
    client.set_password("OPCuser_710l")
    client.session_timeout = 30000
    client.uaclient.timeout = 30000
    return client

def browse_node(node):
    try:
        return node.get_children()
    except:
        return []

def read_historical_data(node, days=7):
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)
    history = node.read_raw_history(starttime=start_time, endtime=end_time)
    return [(entry.SourceTimestamp, entry.Value.Value) for entry in history if entry.Value.Value is not None]

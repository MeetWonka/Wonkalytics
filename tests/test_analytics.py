# test_analytics.py
from wonkalytics.analytics import _write_to_azure_sql
from datetime import datetime

def test_write_to_azure_sql():
    log_item = {
        'username': 'logging_test', 
        'action': 'test_log', 
        'timestamp': datetime.now(),
        'tenant_id': 'test_tenant_id',
        'email': 'logtestmail@wonka.com'
    }
    assert _write_to_azure_sql(log_item) == True  # Returns true if no errors


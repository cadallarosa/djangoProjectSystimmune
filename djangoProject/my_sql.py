from django.db import connections

def reset_mysql_connection():
    """
    Force-close all MySQL connections to prevent stale connections.
    This helps fix 'Lost connection to server' errors.
    """
    for conn in connections.all():
        try:
            conn.close_if_unusable_or_obsolete()
        except Exception as e:
            print(f"⚠️ Database connection reset failed: {e}")

# Reset database connection at startup
reset_mysql_connection()


from src.database.database_manager import get_db_manager

def dump_settings():
    db = get_db_manager()
    try:
        # Check if table exists first or just try to query
        settings = db.execute_query("SELECT setting_key, setting_value FROM system_settings")
        for s in settings:
            print(f"{s[0]}: {s[1]}")
    except Exception as e:
        print(f"Error querying system_settings: {e}")
        try:
            # Fallback to general table list if that failed
            tables = db.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
            print(f"Available tables: {tables}")
        except:
            print("Could not even list tables.")

if __name__ == "__main__":
    dump_settings()

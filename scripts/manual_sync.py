import os
import sys
import toml

# Add root directory to path
sys.path.append(os.getcwd())

def load_secrets():
    try:
        data = toml.load(".streamlit/secrets.toml")
        
        # Flatten and set env vars
        # Handle simple key-values
        for key, value in data.items():
            if isinstance(value, str):
                os.environ[key] = value
                print(f"Loaded {key}")
            elif isinstance(value, dict):
                 # Not deep flattening for now, just main keys if needed
                 pass
                 
    except Exception as e:
        print(f"Error loading secrets: {e}")
        sys.exit(1)

def main():
    print("🔄 Loading configuration...")
    load_secrets()
    
    print("🔄 Importing Sync Manager...")
    try:
        from src.utils.cloud_sync_manager import CloudSyncManager
    except ImportError as e:
        print(f"Import Error: {e}")
        sys.exit(1)
        
    manager = CloudSyncManager()
    
    print("🚀 Starting Manual Sync...")
    print(f"Local DB Path expected at: {manager.local_db_path}")
    
    success, message = manager.run_full_sync()
    
    if success:
        print("\n✅ SUCCESS!")
        print(message)
    else:
        print("\n❌ FAILED")
        print(message)

if __name__ == "__main__":
    main()

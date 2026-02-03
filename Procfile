# Heroku Procfile
# Defines process types for Heroku deployment

# Web process - marketing dashboard
web: streamlit run dashboard.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true

# Client dashboard process
client: streamlit run client_dashboard.py --server.port=8503 --server.address=0.0.0.0 --server.headless=true

# Background worker for order synchronization
worker: python -m src.workers.order_sync_worker --mode continuous

# Optional: One-off migration process
# release: python scripts/migrate.py

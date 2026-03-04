import sqlite3
import pandas as pd
conn = sqlite3.connect('database/client_data.db')
df = pd.read_sql_query("SELECT * FROM onboarding_status WHERE client_email = 'admin@refundly.ai'", conn)
print(df)

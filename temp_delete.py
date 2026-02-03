import sqlite3

email = 'rouxel.s2@chu-nice.fr'
print(f'Force deleting ALL data for: {email}\n')

# Delete from credentials.db (might be multiple rows)
conn = sqlite3.connect('database/credentials.db')
cursor = conn.cursor()

# First check what we have
cursor.execute('SELECT id, platform, store_name FROM credentials WHERE client_id = ?', (email,))
rows = cursor.fetchall()
print(f'Found {len(rows)} credentials entries:')
for row in rows:
    print(f'  - ID: {row[0]}, Platform: {row[1]}, Store: {row[2]}')

# Delete all
cursor.execute('DELETE FROM credentials WHERE client_id = ?', (email,))
deleted = cursor.rowcount
conn.commit()
conn.close()

print(f'\n✅ Deleted {deleted} rows from credentials.db')

# Final verification
conn = sqlite3.connect('database/credentials.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM credentials WHERE client_id = ?', (email,))
count = cursor.fetchone()[0]
conn.close()

print(f'✅ Final check: {count} rows remaining (should be 0)')

if count == 0:
    print(f'\n🎉 Account {email} completely deleted!')
else:
    print(f'\n⚠️  Still {count} rows remaining!')

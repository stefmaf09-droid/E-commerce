import psycopg2
import bcrypt

def get_password_hash(password: str) -> str:
    """Hash a password for storing."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

try:
    conn = psycopg2.connect('postgresql://neondb_owner:npg_fJ5tC4sdDjcx@ep-little-pond-al8y4ngw-pooler.c-3.eu-central-1.aws.neon.tech/neondb?sslmode=require')
    cur = conn.cursor()
    
    email = 'stephenrouxel22@orange.fr'
    fake_hash = get_password_hash('password123')
    
    cur.execute("SELECT * FROM credentials WHERE email=%s", (email,))
    exists = cur.fetchone()
    
    if exists:
        cur.execute("UPDATE credentials SET password_hash=%s WHERE email=%s", (fake_hash, email))
        print("Updated existing user")
    else:
        cur.execute("INSERT INTO credentials (email, password_hash, role) VALUES (%s, %s, %s)", (email, fake_hash, 'client'))
        print("Inserted new user")
        
    conn.commit()
    print('✅ Production DB credentials updated successfully')
except Exception as e:
    print(f"Error: {e}")

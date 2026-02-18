import unittest
import os
import sqlite3
from src.auth.password_manager import PasswordManager, set_client_password, get_user_role, set_user_role, verify_client_password

class TestAuthRoles(unittest.TestCase):
    def setUp(self):
        self.test_db = "tests/test_passwords.db"
        self.manager = PasswordManager(db_path=self.test_db)
        
    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
            
    def test_default_role(self):
        email = "user@example.com"
        password = "password123"
        
        # Create new user using the INSTANCE attached to test DB
        self.manager.set_client_password(email, password)
        
        # Check default role
        role = self.manager.get_user_role(email)
        self.assertEqual(role, 'client')
        
    def test_set_role_explicitly(self):
        email = "admin@example.com"
        password = "adminpass"
        
        # Create user with explicit role using INSTANCE
        self.manager.set_client_password(email, password, role='admin')
        
        role = self.manager.get_user_role(email)
        self.assertEqual(role, 'admin')
        
    def test_update_password_preserves_role(self):
        email = "admin2@example.com"
        
        # 1. Create admin user
        self.manager.set_client_password(email, "pass1", role='admin')
        self.assertEqual(self.manager.get_user_role(email), 'admin')
        
        # 2. Update password without specifying role
        self.manager.set_client_password(email, "pass2")
        
        # 3. Verify password changed and role preserved
        self.assertTrue(self.manager.verify_client_password(email, "pass2"))
        self.assertEqual(self.manager.get_user_role(email), 'admin')
        
    def test_change_role(self):
        email = "user2@example.com"
        self.manager.set_client_password(email, "pass", role='client')
        
        # Promote to admin
        success = self.manager.set_user_role(email, 'admin')
        self.assertTrue(success)
        self.assertEqual(self.manager.get_user_role(email), 'admin')
        
        # Demote to client
        self.manager.set_user_role(email, 'client')
        self.assertEqual(self.manager.get_user_role(email), 'client')

if __name__ == '__main__':
    unittest.main()


import sys
import os

# Add src to path
sys.path.append(os.getcwd())

from src.auth.password_manager import set_user_role, get_user_role

email = "stephenrouxel22@orange.fr"
print(f"Current role for {email}: {get_user_role(email)}")

print(f"Promoting {email} to admin...")
success = set_user_role(email, "admin")

if success:
    print(f"SUCCESS: Role updated to {get_user_role(email)}")
else:
    print("FAILURE: Could not update role. User might not exist.")

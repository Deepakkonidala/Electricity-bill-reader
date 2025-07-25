from database import SessionLocal, User
from auth import hash_password

# Create DB session
db = SessionLocal()

# Create a normal user
user = User(username="user1", password=hash_password("userpass"), role="user")
db.add(user)

# Create an admin user
admin = User(username="admin", password=hash_password("adminpass"), role="admin")
db.add(admin)

# Save to database
db.commit()

print("Users created successfully!")

# Close session
db.close()

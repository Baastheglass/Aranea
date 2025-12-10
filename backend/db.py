import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime
import bcrypt

class Database:
    def __init__(self):
        load_dotenv()
        self.uri = os.getenv("MONGODB_URI")
        self.client = MongoClient(self.uri)
        self.database = self.client.get_database("aranea")
        self.users = self.database.get_collection("users")
        
    # User Authentication Functions
    def create_user(self, username, email, password):
        """
        Create a new user with hashed password
        Returns: (success: bool, message: str, user_data: dict or None)
        """
        try:
            # Check if username already exists
            if self.users.find_one({"username": username}):
                return False, "Username already exists", None
            
            # Check if email already exists
            if self.users.find_one({"email": email}):
                return False, "Email already exists", None
            
            # Hash the password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # Create user document
            user_doc = {
                "username": username,
                "email": email,
                "password": hashed_password,
                "created_at": datetime.utcnow(),
                "last_login": None
            }
            
            # Insert user
            result = self.users.insert_one(user_doc)
            
            # Return user data without password
            user_data = {
                "username": username,
                "email": email,
                "created_at": user_doc["created_at"]
            }
            
            return True, "User created successfully", user_data
            
        except Exception as e:
            return False, f"Error creating user: {str(e)}", None
    
    def authenticate_user(self, username, password):
        """
        Authenticate user by username and password
        Returns: (success: bool, message: str, user_data: dict or None)
        """
        try:
            # Find user by username
            user = self.users.find_one({"username": username})
            
            if not user:
                return False, "Invalid username or password", None
            
            # Verify password
            if bcrypt.checkpw(password.encode('utf-8'), user["password"]):
                # Update last login
                self.users.update_one(
                    {"username": username},
                    {"$set": {"last_login": datetime.utcnow()}}
                )
                
                # Return user data without password
                user_data = {
                    "username": user["username"],
                    "email": user["email"],
                    "created_at": user["created_at"],
                    "last_login": datetime.utcnow()
                }
                
                return True, "Authentication successful", user_data
            else:
                return False, "Invalid username or password", None
                
        except Exception as e:
            return False, f"Error authenticating user: {str(e)}", None
    
    def get_user_by_username(self, username):
        """
        Get user information by username (without password)
        Returns: user_data dict or None
        """
        try:
            user = self.users.find_one({"username": username}, {"password": 0})
            return user
        except Exception as e:
            return None
        
    def close_connection(self):
        self.client.close()

if __name__ == "__main__":
    pass
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime
import bcrypt
from bson import ObjectId

class Database:
    def __init__(self):
        load_dotenv()
        self.uri = os.getenv("MONGODB_URI")
        self._client = None
        self._database = None
        self._users = None
        self._chats = None
        self._messages = None
    
    @property
    def client(self):
        if self._client is None:
            self._client = MongoClient(self.uri)
        return self._client
    
    @property
    def database(self):
        if self._database is None:
            self._database = self.client.get_database("aranea")
        return self._database
    
    @property
    def users(self):
        if self._users is None:
            self._users = self.database.get_collection("users")
        return self._users
    
    @property
    def chats(self):
        if self._chats is None:
            self._chats = self.database.get_collection("chats")
        return self._chats
    
    @property
    def messages(self):
        if self._messages is None:
            self._messages = self.database.get_collection("messages")
        return self._messages
        
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
    
    # Chat Management Functions
    def create_chat(self, username, title=None):
        """
        Create a new chat session for a user
        Returns: (success: bool, message: str, chat_data: dict or None)
        """
        try:
            chat_doc = {
                "username": username,
                "title": title or f"New Chat",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = self.chats.insert_one(chat_doc)
            
            chat_data = {
                "chat_id": str(result.inserted_id),
                "username": username,
                "title": chat_doc["title"],
                "created_at": chat_doc["created_at"],
                "updated_at": chat_doc["updated_at"]
            }
            
            return True, "Chat created successfully", chat_data
            
        except Exception as e:
            return False, f"Error creating chat: {str(e)}", None
    
    def get_user_chats(self, username):
        """
        Get all chat sessions for a user
        Returns: list of chat_data dicts
        """
        try:
            chats = list(self.chats.find(
                {"username": username}
            ).sort("updated_at", -1))
            
            chat_list = []
            for chat in chats:
                # Get last message for preview
                last_message = self.messages.find_one(
                    {"chat_id": str(chat["_id"])},
                    sort=[("timestamp", -1)]
                )
                
                chat_data = {
                    "chat_id": str(chat["_id"]),
                    "title": chat["title"],
                    "created_at": chat["created_at"],
                    "updated_at": chat["updated_at"],
                    "last_message": last_message["text"] if last_message else None
                }
                chat_list.append(chat_data)
            
            return chat_list
            
        except Exception as e:
            print(f"Error getting user chats: {str(e)}")
            return []
    
    def get_chat_messages(self, chat_id):
        """
        Get all messages for a specific chat
        Returns: list of message dicts
        """
        try:
            messages = list(self.messages.find(
                {"chat_id": chat_id}
            ).sort("timestamp", 1))
            
            message_list = []
            for msg in messages:
                message_data = {
                    "message_id": str(msg["_id"]),
                    "chat_id": msg["chat_id"],
                    "sender": msg["sender"],
                    "text": msg["text"],
                    "timestamp": msg["timestamp"]
                }
                message_list.append(message_data)
            
            return message_list
            
        except Exception as e:
            print(f"Error getting chat messages: {str(e)}")
            return []
    
    def save_message(self, chat_id, sender, text):
        """
        Save a message to a chat
        Returns: (success: bool, message: str, message_data: dict or None)
        """
        try:
            message_doc = {
                "chat_id": chat_id,
                "sender": sender,
                "text": text,
                "timestamp": datetime.utcnow()
            }
            
            result = self.messages.insert_one(message_doc)
            
            # Update chat's updated_at timestamp
            self.chats.update_one(
                {"_id": ObjectId(chat_id)},
                {"$set": {"updated_at": datetime.utcnow()}}
            )
            
            message_data = {
                "message_id": str(result.inserted_id),
                "chat_id": chat_id,
                "sender": sender,
                "text": text,
                "timestamp": message_doc["timestamp"]
            }
            
            return True, "Message saved successfully", message_data
            
        except Exception as e:
            return False, f"Error saving message: {str(e)}", None
    
    def update_chat_title(self, chat_id, title):
        """
        Update the title of a chat
        Returns: (success: bool, message: str)
        """
        try:
            self.chats.update_one(
                {"_id": ObjectId(chat_id)},
                {"$set": {"title": title, "updated_at": datetime.utcnow()}}
            )
            return True, "Chat title updated successfully"
        except Exception as e:
            return False, f"Error updating chat title: {str(e)}"
    
    def delete_chat(self, chat_id):
        """
        Delete a chat and all its messages
        Returns: (success: bool, message: str)
        """
        try:
            # Delete all messages in the chat
            self.messages.delete_many({"chat_id": chat_id})
            
            # Delete the chat
            self.chats.delete_one({"_id": ObjectId(chat_id)})
            
            return True, "Chat deleted successfully"
        except Exception as e:
            return False, f"Error deleting chat: {str(e)}"
        
    def close_connection(self):
        self.client.close()

if __name__ == "__main__":
    pass
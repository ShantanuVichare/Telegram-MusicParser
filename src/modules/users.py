import os
import uuid
import json
import time

admin_users = os.environ.get("ADMIN_USER_IDS")
if not admin_users:
    raise ValueError("ADMIN_USER_IDS environment variable is not set")
admin_users = [int(user_id) for user_id in admin_users.split(",")]

expiration_interval = 60*15  # seconds
tokens = dict() # {token: {"user_id": user_id, "timestamp": timestamp}}
authorized_user_tokens = dict() # {user_id: token}

class AuthManager:
        
    def is_authorized(user_id: int):
        user_token = authorized_user_tokens.get(user_id)
        if not user_token:
            return False
        if time.time() - tokens[user_token]["timestamp"] > expiration_interval:
            del tokens[user_token]
            del authorized_user_tokens[user_id]
            return False
        return True
    
    def is_admin(user_id: int):
        return user_id in admin_users
    
    def generate_token(user_id: int):
        if not AuthManager.is_admin(user_id):
            return None
        token = str(uuid.uuid4())[:4]
        tokens[token] = {"timestamp": time.time(), "user_id": None}
        return token
    
    def authorize_user(user_id: int, new_token: str):
        # Cases:
        # 1. User is already authorized with valid token
        # 2. User was authorized but now invalid token
        # 3. User was not authorized
        # 4. User is admin
        # 5. Invalid new token
        # Unhandled: User is authorized but needs to be refreshed with newer token
        
        if AuthManager.is_admin(user_id) or AuthManager.is_authorized(user_id):
            return True
        
        if new_token in tokens and (time.time() - tokens[new_token]["timestamp"]) < expiration_interval:
            tokens[new_token]["user_id"] = user_id
            authorized_user_tokens[user_id] = new_token
            return True
        return False



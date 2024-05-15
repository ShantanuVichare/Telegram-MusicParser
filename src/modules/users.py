import os
import uuid
import json
import time

filepath = os.environ["USERS_METADATA_PATH"]
expiration_interval = 60  # seconds

user_data = None
token = {"value": None, "timestamp": time.time()}


def _refresh_data(updated_data=None):
    # If new data, persist it
    if updated_data:
        with open(filepath, "w") as f:
            json.dump(updated_data, f)
    # Sync with persisted data
    global user_data
    with open(filepath, "r") as f:
        user_data = json.load(f)
    return


def _refresh_token():
    global token
    token["value"] = str(uuid.uuid4())[:4]
    token["timestamp"] = time.time()
    return


_refresh_data()


def is_allowed(user_id):
    global user_data
    return user_id in user_data["allowed_users"]


def is_admin(user_id):
    global user_data
    return user_id in user_data["admin_users"]


def get_token(admin_user_id):
    if not is_admin(admin_user_id):
        return False
    _refresh_token()
    return token["value"]


def request_user(user_id, token_value):
    global user_data
    if user_id in user_data["allowed_users"]:
        return True
    if token_value == token["value"] and (
        time.time() - token["timestamp"] < expiration_interval
    ):
        user_data["allowed_users"].append(user_id)
        _refresh_data(user_data)
        return True
    return False

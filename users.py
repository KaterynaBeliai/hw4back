import hashlib


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


USERS = {
    "john": {
        "password_hash": hash_password("john123"),
        "email": "john@example.com",
        "role": "user",
    },
    "admin": {
        "password_hash": hash_password("adminpass"),
        "email": "admin@example.com",
        "role": "admin",
    },
}


def check_password(username, password):
    user = USERS.get(username)
    if not user:
        return False
    return user["password_hash"] == hash_password(password)

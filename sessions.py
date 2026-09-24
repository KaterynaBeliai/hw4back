import secrets

SESSIONS = {}


def create_session(data):
    sid = secrets.token_hex(16)
    SESSIONS[sid] = data
    return sid


def get_session(session_id):
    if not session_id:
        return None
    return SESSIONS.get(session_id)


def delete_session(session_id):
    if not session_id:
        return
    SESSIONS.pop(session_id, None)

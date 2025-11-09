import secrets
import time
import threading

from utils.logger import logger

#In-memory session store and thread lock for concurrency
_sessions = {}
_sessions_lock = threading.Lock()

def create_session(user_info):
    """
    Ceate a new sesssion for the use_info
    Returns a secure session ID.
    """
    session_id = secrets.token_hex(32)
    session_data = {
        "user_info" : user_info,
        "start_time" : time.time()
    }
    with _sessions_lock:
        _sessions[session_id] = session_data
    logger.info(f"Session created for user: {user_info} with session {session_id}" )
    return session_id
def get_session(session_id):
    """
    Retrieves the session data for the given session_id
    Reurn None if the session does not exist.
    """
    with _sessions_lock:
        session = _sessions.get(session_id)
    if session:
        logger.info(f"Session accessed: {session_id}")
    else:
        logger.warning(f"Session not found: {session_id}")
    return session
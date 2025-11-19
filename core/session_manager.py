import secrets
import time
import threading

from utils.logger import logger
from firewall.firewall_manager import revoke_access

# In-memory session store and thread lock for concurrency
_sessions = {}
_sessions_lock = threading.Lock()

# Session timeout in seconds (e.g., 1 hour)
SESSION_TIMEOUT = 3600

def create_session(user_info):
    """
    Create a new session for the user_info.
    Returns a secure session ID.
    
    Args:
        user_info (dict): Dictionary containing user information, e.g., {"username": "user", "ip": "192.168.1.1"}
    """
    session_id = secrets.token_hex(32)
    session_data = {
        "user_info": user_info,
        "start_time": time.time(),
        "expiry_time": time.time() + SESSION_TIMEOUT
    }
    with _sessions_lock:
        _sessions[session_id] = session_data
    logger.info(f"Session created for user: {user_info} with session {session_id}")
    return session_id

def get_session(session_id):
    """
    Retrieves the session data for the given session_id.
    Return None if the session does not exist or is expired.
    """
    with _sessions_lock:
        session = _sessions.get(session_id)
        if session and time.time() <= session.get("expiry_time", 0):
            logger.info(f"Session accessed: {session_id}")
            return session
        elif session:
            logger.warning(f"Session expired: {session_id}")
        else:
            logger.warning(f"Session not found: {session_id}")
    return None

def cleanup_expired_sessions():
    """
    Iterate over all active sessions, check their expiration timestamp using time.time(),
    and if expired, remove them from memory and call revoke_access(user_ip) to block network access.
    """
    current_time = time.time()
    expired_sessions = []
    
    with _sessions_lock:
        for session_id, session in list(_sessions.items()):
            if current_time > session.get("expiry_time", 0):
                expired_sessions.append((session_id, session))
    
    for session_id, session in expired_sessions:
        user_ip = session["user_info"].get("ip")
        if user_ip:
            revoke_access(user_ip)
            logger.info(f"Revoked access for IP {user_ip} due to expired session {session_id}")
        with _sessions_lock:
            del _sessions[session_id]
        logger.info(f"Expired session {session_id} cleaned up for user {session['user_info'].get('username', 'unknown')}")
import secrets
import time
import threading
import csv
import os
from datetime import datetime

from utils.logger import logger
from firewall.firewall_manager import revoke_access

# In-memory session store and thread lock for concurrency
_sessions = {}
_sessions_lock = threading.Lock()

# Session timeout in seconds (e.g., 1 hour)
SESSION_TIMEOUT = 3600

def log_session_action(action, username, ip):
    """
    Log session actions to a CSV file.
    
    Args:
        action (str): The action type (LOGIN/LOGOUT/EXPIRED).
        username (str): The username.
        ip (str): The IP address.
    """
    file_path = "data/session_log.csv"
    # Ensure the directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        # Write headers if file is empty
        if os.stat(file_path).st_size == 0:
            writer.writerow(["timestamp", "username", "ip", "action"])
        writer.writerow([datetime.now().isoformat(), username, ip, action])

def create_session(user_info):
    """
    Create a new session for the user_info, including the client's source IP address.
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
    log_session_action("LOGIN", user_info["username"], user_info["ip"])
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

def destroy_session(session_id):
    """
    Destroy the session with the given session_id.
    
    Args:
        session_id (str): The session ID to destroy.
    
    Returns:
        bool: True if the session was destroyed, False if not found.
    """
    with _sessions_lock:
        if session_id in _sessions:
            session = _sessions[session_id]
            log_session_action("LOGOUT", session["user_info"]["username"], session["user_info"]["ip"])
            del _sessions[session_id]
            logger.info(f"Session {session_id} destroyed")
            return True
    return False

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
        username = session["user_info"].get("username", "unknown")
        log_session_action("EXPIRED", username, user_ip)
        if user_ip:
            revoke_access(user_ip)
            logger.info(f"Revoked access for IP {user_ip} due to expired session {session_id}")
        with _sessions_lock:
            del _sessions[session_id]
        logger.info(f"Expired session {session_id} cleaned up for user {username}")
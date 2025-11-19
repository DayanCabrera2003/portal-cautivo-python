import hashlib
import os
from utils.data_handler import load_json
from utils.logger import logger

def hash_password(password):
    """
    Hash a password with a random salt using SHA-256.
    
    Args:
        password(str): The password to hash.
        
    Returns:
        tuple: (salt_hex, hash_hex) where salt_hex is the hex-encoded salt and hash_hex is the hex-encoded hash.
    """
    salt = os.urandom(16)
    hash_obj = hashlib.sha256(salt + password.encode('utf-8'))
    return salt.hex(), hash_obj.hexdigest()

def validate_credentials(username, password):
    """
    Validate user credentials by comparing with saved data.
    
    Args:
        username(str): The username to validate
        password(str): The password to validate
        
    Returns: bool: True is valid data, false is not valid data
    
    Raises: FileNotFoundError: If the user data file does not exist
    ValueError: If the user data file contains valid JSON format
    """
    try:
        #Load user data from the json file
        user_data = load_json("data/users.json")
        
        #Check if the username exist and have the corects fields
        if username in user_data and 'salt' in user_data[username] and 'hash' in user_data[username]:
            stored_salt = bytes.fromhex(user_data[username]['salt'])
            stored_hash = user_data[username]['hash']
            
            #Hash the provided password with the stored salt
            hash_obj = hashlib.sha256(stored_salt + password.encode('utf-8'))
            computed_hash = hash_obj.hexdigest()
            
            if computed_hash == stored_hash:
                logger.info(f"Authentification succes for user '{username}'")
                return True
            else:
                logger.warning(f"Authentication failed: incorrect password for '{username}'")
                return False
        else:
            logger.warning(f"Athentification failed for the user '{username}'")
            return False
        
    except FileNotFoundError:
        logger.error("The file 'data/users.json' does not exist")
        raise FileNotFoundError(f"The file 'data/user.json' does not exist")
    except ValueError as e:
        logger.error("Error loading user data: {e}")
        raise ValueError (f"Error loading user data: {e}")
        
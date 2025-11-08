from utils.data_handler import load_json

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
        user_data = load_json("data/user.json")
        
        #Check if the username is correct
        if username in user_data and user_data[username] == password: return True
        
        return False
    except FileNotFoundError:
        raise FileNotFoundError(f"The file 'data/user.json' does not exist")
    except ValueError as e:
        raise ValueError (f"Error loading user data: {e}")
        
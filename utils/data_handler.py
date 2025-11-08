import json

def load_json(file_path):
    """
    Load json data from a file
    Args: file_path (str): path to the json file
    Returns: dict: Parsed json data.
    Raises: FileNotFoundError: If the file does not exist.
    ValueError: If contains invalid json format.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"The file '{file_path}' does not exist")
    except json.JSONDecodeError as e:
        raise ValueError(f"Inavlid json format in file '{file_path}'")
    
def save_json (file_path, data):
    """
    Save data in json format in file
    Args:
    - file_path(str): path to save the data
    - data (dict): data to save in the file
    Raises:
    ValueError: If the data cannot be convet to json
    IOError: It there is an error writing to the file
    """
    try: 
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4)
    except TypeError as e:
        raise ValueError(f"Data provided is not valid")
    except IOError as e:
        raise IOError(f"Eror writing in file '{file_path}'")
import subprocess
from utils.logger import logger

def execute_command(command, args):
    """
    Execute a system command using subprocess, have handle errors and logger
    
    Args:
        command (str): The command to execute ('iptables')
        ags (list): Arguments for the command
    Returns: 
        tuple: (returncode, stdout, stderr) returncode is the exit code, stout and stderr are the captured outputs as strings
    """
    
    full_command = [command] + args
    logger.info(f"Executing command: {' '.join(full_command)}")
    
    try: 
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            check=False
        )
        returncode = result.returncode
        stdout = result.stdout
        stderr = result.stderr
        
        if returncode == 0:
            logger.info(f"Command execute succefully. Output: {stdout.strip()}")
        else: 
            logger.warning(f"Command failed with return code {returncode}")
        return returncode, stdout, stderr
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        return -1, "", str(e)
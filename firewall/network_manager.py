"""
Network management functions for the captive portal.
Handles DNS configuration and network setup.
"""
import os
import shutil
from utils.logger import logger

DNSMASQ_SHARED_DIR = "/etc/NetworkManager/dnsmasq-shared.d"
DNSMASQ_CONF_FILE = "captive-portal.conf"

def setup_captive_dns():
    """
    Configure dnsmasq to intercept DNS queries for captive portal detection.
    Copies the dnsmasq configuration file to NetworkManager's shared directory.
    
    Returns:
        bool: True if successful, False otherwise
    """
    src_file = "dnsmasq-captive.conf"
    dst_file = os.path.join(DNSMASQ_SHARED_DIR, DNSMASQ_CONF_FILE)
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(DNSMASQ_SHARED_DIR, exist_ok=True)
        
        # Check if source file exists
        if not os.path.exists(src_file):
            logger.error(f"DNS configuration file not found: {src_file}")
            return False
        
        # Copy configuration file
        shutil.copy2(src_file, dst_file)
        logger.info(f"DNS configuration copied to {dst_file}")
        return True
        
    except PermissionError:
        logger.error(f"Permission denied: Cannot write to {DNSMASQ_SHARED_DIR}")
        return False
    except Exception as e:
        logger.error(f"Failed to setup captive DNS: {e}")
        return False

def cleanup_captive_dns():
    """
    Remove the captive portal DNS configuration.
    
    Returns:
        bool: True if successful, False otherwise
    """
    dst_file = os.path.join(DNSMASQ_SHARED_DIR, DNSMASQ_CONF_FILE)
    
    try:
        if os.path.exists(dst_file):
            os.remove(dst_file)
            logger.info(f"DNS configuration removed from {dst_file}")
        return True
    except PermissionError:
        logger.error(f"Permission denied: Cannot remove {dst_file}")
        return False
    except Exception as e:
        logger.error(f"Failed to cleanup captive DNS: {e}")
        return False

from firewall.cli_executor import execute_command
from utils.logger import logger

def initialize_rules():
    """
    Initialize the firewall rules
    This sets up a basic captive portal firewall configuration
    """
    # Flush existing rules
    execute_command("iptables", ["-F"])
    execute_command("iptables", ["-X"])
    
    # Set default policies to DROP for INPUT and FORWARD
    execute_command("iptables", ["-P", "INPUT", "DROP"])
    execute_command("iptables", ["-P", "FORWARD", "DROP"])
    
    # Allow loopback traffic
    execute_command("iptables", ["-A", "INPUT", "-i", "lo", "-j", "ACCEPT"])
    
    # Allow established and related connections
    execute_command("iptables", ["-A", "INPUT", "-m", "conntrack", "--ctstate", "ESTABLISHED,RELATED", "-j", "ACCEPT"])
    
    # Allow traffic to the captive portal server
    execute_command("iptables", ["-A", "INPUT", "-p", "tcp", "--dport", "8080", "-j", "ACCEPT"])

def initialize_firewall():
    """
    Initialize the firewall by setting the default policy for external network traffic (FORWARD chain) to DROP.
    This blocks forwarding traffic until users are authenticated.
    Includes an exception to allow inbound HTTP traffic to the captive portal server.
    """
    # Allow inbound HTTP traffic to the captive portal server (port 8080)
    returncode_allow, stdout_allow, stderr_allow = execute_command("iptables", ["-I", "INPUT", "-p", "tcp", "--dport", "8080", "-j", "ACCEPT"])
    if returncode_allow == 0:
        logger.info("Successfully added rule to allow inbound HTTP traffic on port 8080.")
    else:
        logger.error(f"Failed to add rule for inbound HTTP traffic. Stderr: {stderr_allow}")
    
    # Set default policy for FORWARD chain to DROP
    returncode_drop, stdout_drop, stderr_drop = execute_command("iptables", ["-P", "FORWARD", "DROP"])
    if returncode_drop == 0:
        logger.info("Successfully set default policy for FORWARD chain to DROP, blocking external network traffic.")
    else:
        logger.error(f"Failed to set FORWARD policy to DROP. Stderr: {stderr_drop}")

def allow_user_access(ip_address):
    """
    Allow network access for a specific IP address after successful authentication by adding a rule to accept all outgoing traffic.
    
    Args:
        ip_address (str): The IP address to allow access for.
    """
    # Add rule to allow all outgoing traffic from the authenticated IP
    returncode, stdout, stderr = execute_command("iptables", ["-I", "OUTPUT", "-s", ip_address, "-j", "ACCEPT"])
    if returncode == 0:
        logger.info(f"Successfully added rule to allow all outgoing traffic from {ip_address}.")
    else:
        logger.error(f"Failed to add rule for outgoing traffic from {ip_address}. Stderr: {stderr}")
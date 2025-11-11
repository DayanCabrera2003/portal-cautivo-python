from firewall.cli_executor import execute_command

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

def allow_user_access(ip_address):
    """
    Allow network access for a specific IP address after successful authentication.
    
    Args:
        ip_address (str): The IP address to allow access for.
    """
    # Add rule to allow all traffic from the authenticated IP
    execute_command("iptables", ["-I", "INPUT", "-s", ip_address, "-j", "ACCEPT"])
    execute_command("iptables", ["-I", "FORWARD", "-s", ip_address, "-j", "ACCEPT"])
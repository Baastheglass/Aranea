import subprocess
import netifaces
import ipaddress
import re

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
    
    def check_if_host_active(self, ip_address):
        result = subprocess.run(["nmap", "-sn", ip_address], capture_output=True, text=True)
        if(result.stdout):
            return result.stdout
        else:
            return result.stderr
    
    def scan_entire_network(self):
        for iface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(iface)
            if netifaces.AF_INET in addrs:
                ipv4 = addrs[netifaces.AF_INET][0]
                ip = ipv4['addr']
                mask = ipv4['netmask']
                try:
                    network = ipaddress.ip_network(f"{ip}/{mask}", strict=False)
                    print("Network being scanned: ", network)
                    result = subprocess.run(["nmap", "-sn", str(network)], capture_output=True, text=True)
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
        
    def get_open_ports(self, ip_address):
        result = subprocess.run(["nmap", "-p-", ip_address], capture_output=True, text=True)
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
    def __init__(self):
        pass
    
    def find_vulnerabilities_for_service(self, vulnerability):
        result = subprocess.run(["msfconsole"], capture_output=True, text=True)
        if(result.stdout):
            return result.stdout
        else:
            return result.stderr
        
if __name__ == "__main__":
    scanner = Scanner()
    exploiter = Exploiter()
    #scanner.scan_entire_network()
    # print(scanner.get_open_ports("192.168.1.138"))
    # print(scanner.get_running_services("192.168.1.138"))
    #print(scanner.get_ip_of_website("https://flexstudent.nu.edu.pk/Login"))
    exploiter.find_vulnerabilities_for_service("rstp")
import os
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv
from agent_tools import Scanner, Exploiter

class FormatterAgent:
    def __init__(self):
        pass
    
    def format_scan_target_result(self, raw_result: str, ip_address: str) -> str:
        """Parse and format scan_target output from rustscan/nmap"""
        lines = raw_result.split('\n')
        ports_info = []
        
        # First, try to parse rustscan "Open" lines
        for line in lines:
            if line.startswith('Open '):
                # Format: "Open 192.168.64.2:80"
                match = re.search(r'Open\s+[\d\.]+:(\d+)', line)
                if match:
                    port = match.group(1)
                    # Map common ports to services
                    service = self._get_service_name(port)
                    ports_info.append((port, service))
        
        # If no rustscan results, try parsing nmap table
        if not ports_info:
            in_port_table = False
            for line in lines:
                # Look for the PORT STATE SERVICE header
                if 'PORT' in line and 'STATE' in line and 'SERVICE' in line:
                    in_port_table = True
                    continue
                
                # Stop when we hit the end of the table
                if in_port_table and (line.startswith('Read data') or line.startswith('Nmap done') or not line.strip()):
                    if not line.strip() or line.startswith('Read data') or line.startswith('Nmap done'):
                        break
                
                # Parse port lines
                if in_port_table and '/tcp' in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        port_proto = parts[0]  # e.g., "21/tcp"
                        port = port_proto.split('/')[0]
                        service = parts[2]  # service name
                        ports_info.append((port, service))
        
        # Format the output
        if not ports_info:
            return f"No open ports found on {ip_address}."
        
        result = f"## Scan Results for {ip_address}\n\n"
        result += f"**Found {len(ports_info)} open ports:**\n\n"
        result += "| Port | Service |\n"
        result += "|------|----------|\n"
        
        for port, service in ports_info:
            result += f"| {port} | {service} |\n"
        
        result += f"\n**Next steps:** You can run service version detection with `get_running_services` to identify specific versions and potential vulnerabilities."
        
        return result
    
    def _get_service_name(self, port: str) -> str:
        """Map common port numbers to service names"""
        port_map = {
            '21': 'ftp', '22': 'ssh', '23': 'telnet', '25': 'smtp',
            '53': 'dns', '80': 'http', '110': 'pop3', '111': 'rpcbind',
            '135': 'msrpc', '139': 'netbios-ssn', '143': 'imap',
            '443': 'https', '445': 'microsoft-ds', '512': 'exec',
            '513': 'login', '514': 'shell', '587': 'smtp',
            '993': 'imaps', '995': 'pop3s', '1099': 'rmiregistry',
            '1433': 'mssql', '1524': 'ingreslock', '2049': 'nfs',
            '2121': 'ftp', '3306': 'mysql', '3389': 'rdp',
            '3632': 'distccd', '5432': 'postgresql', '5900': 'vnc',
            '6000': 'x11', '8080': 'http-proxy', '8443': 'https-alt'
        }
        return port_map.get(port, 'unknown')
    
    def format_result(self, function_name: str, function_arguments: dict, raw_result: str) -> str:
        """Format raw function results into comprehensive, user-friendly output"""
        if function_name == "scan_target":
            ip_address = function_arguments.get("ip_address", "target") if function_arguments else "target"
            return self.format_scan_target_result(raw_result, ip_address)
        
        # For other functions, return raw result for now
        return f"**{function_name} Results:**\n\n```\n{raw_result}\n```"

class Agent:
    def __init__(self):
        load_dotenv()
        self._client = None
        self._chat = None
        self.formatter = FormatterAgent()
        self.scanner_functions = list()
        callables = [name for name in dir(Scanner) if callable(getattr(Scanner, name))]
        self.scanner_functions.extend(callables)
        self.exploiter_functions = list()
        callables = [name for name in dir(Exploiter) if callable(getattr(Exploiter, name))]
        self.exploiter_functions.extend(callables)
        self.prompt = """You are Aranea, an expert penetration testing assistant designed to help security professionals conduct network reconnaissance and vulnerability assessments. Your role is to guide users through pentesting activities using available tools and provide clear, actionable insights.

                        AVAILABLE FUNCTIONS:
                        - scan_entire_network(): Scan the entire local network to discover active hosts
                        - get_ip_of_website(website: str): Resolve the IP address of a domain/website
                        - scan_target(ip_address: str): Scan all ports on a target IP to identify open ports
                        - scan_specific_port(ip_address: str, port: str): Scan a specific port on a target IP
                        - scan_specific_ports(ip_address: str, ports: list): Scan multiple specific ports on a target IP
                        - get_running_services(ip_address: str): Identify services and versions running on open ports of a target
                        - find_vulnerabilities_for_service(service_name: str): Search for known vulnerabilities for a specific service

                        RESPONSE FORMAT:
                        You must always respond in this exact format:
                        response: <your detailed response to the user>
                        function_to_execute: <function_name or null>
                        function_arguments: <dict of arguments or null>

                        RULES:
                        1. Analyze the user's request carefully to determine if a function needs to be executed
                        2. If the user wants to scan hosts, check ports, identify services, or find vulnerabilities, select the appropriate function
                        3. Extract any parameters (IP addresses, domains, service names, etc.) from the user's message and provide them as function_arguments
                        4. Provide clear, professional guidance in your response
                        5. If multiple steps are needed, suggest the logical next step and return only ONE function at a time
                        6. If no function execution is needed (e.g., user is asking a question or having a conversation), return null for both function_to_execute and function_arguments
                        7. Always prioritize security best practices and ethical hacking principles
                        8. Be concise but informative in your responses
                        9. Format function_arguments as a valid Python dictionary, e.g., {"ip_address": "192.168.1.100"} or {"service_name": "apache"}

                        EXAMPLES:
                        User: "Scan the network for active hosts"
                        response: I'll scan your local network to discover all active hosts. This will help identify potential targets for further analysis.
                        function_to_execute: scan_entire_network
                        function_arguments: null

                        User: "What ports are open on 192.168.1.100?"
                        response: I'll perforscan_target
                        function_arguments: {"ip_address": "192.168.1.100"}

                        User: "Scan port 80 on 10.0.0.5"
                        response: I'll scan port 80 on 10.0.0.5 to check if it's open.
                        function_to_execute: scan_specific_port
                        function_arguments: {"ip_address": "10.0.0.5", "port": "80
                        function_arguments: {"ip_address": "10.0.0.5"}

                        User: "Find vulnerabilities for Apache"
                        response: I'll search for known vulnerabilities affecting Apache.
                        function_to_execute: find_vulnerabilities_for_service
                        function_arguments: {"service_name": "apache"}

                        User: "What is penetration testing?"
                        response: Penetration testing is a simulated cyber attack against your system to identify exploitable vulnerabilities. It helps organizations strengthen their security posture by finding weaknesses before malicious actors do.
                        function_to_execute: null
                        function_arguments: null"""
        
    @property
    def client(self):
        if self._client is None:
            self._client = genai.Client()
        return self._client
    
    @property
    def chat(self):
        if self._chat is None:
            self._chat = self.client.chats.create(model="gemini-2.5-flash")
        return self._chat
        
    def generate(self, query):
        response = self.chat.send_message(message=query,
                                          config=types.GenerateContentConfig(
                                              system_instruction=self.prompt))
        return response.text
    
    async def respond(self, query, ws_manager = None, session_id = None):
        response = self.generate(query)
        # Simple parsing logic to extract response, function_to_execute, and function_arguments
        try:
            response_lines = response.split('\n')
            response_text = ""
            function_to_execute = None
            function_arguments = None
            
            for line in response_lines:
                if line.startswith("response:"):
                    response_text = line.replace("response:", "").strip()
                elif line.startswith("function_to_execute:"):
                    func = line.replace("function_to_execute:", "").strip()
                    function_to_execute = func if func != "null" else None
                elif line.startswith("function_arguments:"):
                    args = line.replace("function_arguments:", "").strip()
                    if args != "null":
                        # Parse the dictionary string
                        import ast
                        function_arguments = ast.literal_eval(args)
            
            if ws_manager and session_id:
                if(function_to_execute and function_to_execute in self.scanner_functions):
                    await ws_manager.send_event(session_id, "text_response_with_function", response_text)
                    print(f"Executing function: {function_to_execute}")
                    print(f"With arguments: {function_arguments}")
                    function = getattr(Scanner(), function_to_execute)
                    # Call function with or without arguments
                    if function_arguments:
                        result = function(**function_arguments)
                    else:
                        result = function()
                    print("Raw function result:", result)
                    
                    # Format the result using FormatterAgent
                    formatted_result = self.formatter.format_result(
                        function_name=function_to_execute,
                        function_arguments=function_arguments,
                        raw_result=str(result)
                    )
                    
                    await ws_manager.send_event(session_id, "function_result", formatted_result)
                    print("Formatted result sent to client")
                elif(function_to_execute and function_to_execute in self.exploiter_functions):
                    await ws_manager.send_event(session_id, "text_response_with_function", response_text)
                    print(f"Executing function: {function_to_execute}")
                    print(f"With arguments: {function_arguments}")
                    function = getattr(Exploiter(), function_to_execute)
                    # Call function with or without arguments
                    if function_arguments:
                        result = function(**function_arguments)
                    else:
                        result = function()
                    print("Raw function result:", result)
                    
                    # Format the result using FormatterAgent
                    formatted_result = self.formatter.format_result(
                        function_name=function_to_execute,
                        function_arguments=function_arguments,
                        raw_result=str(result)
                    )
                    
                    await ws_manager.send_event(session_id, "function_result", formatted_result)
                    print("Formatted result sent to client")
                else:
                    await ws_manager.send_event(session_id, "text_response_no_function", response_text)   
        except Exception as e:
            await ws_manager.send_event(session_id, "error", {"message": str(e)})
            print(f"Error in respond method: {e}")
    
if __name__ == "__main__":
    agent = Agent()
    explanation = agent.respond("Scan the network")
    print(explanation)
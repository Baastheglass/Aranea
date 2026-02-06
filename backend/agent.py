import os
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv
from agent_tools import Scanner, Exploiter, Attacker
from datetime import datetime
from constants import DOCUMENTER_AGENT_PROMPT, AGENT_PROMPT

class DocumenterAgent:
    def __init__(self):
        load_dotenv()
        self._client = None
        self._chat = None
        self.prompt = DOCUMENTER_AGENT_PROMPT
    
    @property
    def client(self):
        if self._client is None:
            documenter_api_key = os.getenv('GOOGLE_DOCUMENTER_API_KEY')
            self._client = genai.Client(api_key=documenter_api_key)
        return self._client
    
    @property
    def chat(self):
        if self._chat is None:
            self._chat = self.client.chats.create(model="gemini-2.5-flash")
        return self._chat
    
    def generate_report(self, history_data: list, engagement_info: dict = None) -> str:
        """
        Generate a comprehensive penetration testing report from agent history
        
        Args:
            history_data: List of history entries from Agent.get_history()
            engagement_info: Optional dict with engagement metadata (client, date, tester, etc.)
        
        Returns:
            Formatted penetration testing report in Markdown
        """
        # Prepare engagement metadata
        if engagement_info is None:
            engagement_info = {}
        
        engagement_info.setdefault('date', datetime.now().strftime('%Y-%m-%d'))
        engagement_info.setdefault('tester', 'Aranea Security Team')
        engagement_info.setdefault('client', 'Client Organization')
        engagement_info.setdefault('engagement_type', 'Internal Network Penetration Test')
        
        # Format history for the AI
        formatted_history = self._format_history_for_report(history_data)
        
        # Create the prompt for report generation
        report_prompt = f"""Generate a comprehensive penetration testing report based on the following engagement information and testing activities:

ENGAGEMENT INFORMATION:
- Client: {engagement_info['client']}
- Engagement Type: {engagement_info['engagement_type']}
- Test Date: {engagement_info['date']}
- Performed By: {engagement_info['tester']}

TESTING ACTIVITIES AND RESULTS:
{formatted_history}

Please generate a complete, professional penetration testing report following the structure and guidelines provided in your system instructions. Include all sections, proper severity ratings, detailed findings with evidence, and actionable recommendations."""

        # Generate the report using the AI
        response = self.chat.send_message(
            message=report_prompt,
            config=types.GenerateContentConfig(
                system_instruction=self.prompt,
                temperature=0.4  # Lower temperature for more consistent, professional output
            )
        )
        
        return response.text
    
    def _format_history_for_report(self, history_data: list) -> str:
        """Format history data into a readable structure for the AI"""
        if not history_data:
            return "No testing activities recorded."
        
        formatted = []
        for idx, entry in enumerate(history_data, 1):
            formatted.append(f"\n{'='*60}")
            formatted.append(f"ACTIVITY #{idx}")
            formatted.append(f"{'='*60}")
            formatted.append(f"\nUser Query: {entry['query']}")
            formatted.append(f"\nAgent Response: {entry['response']}")
            
            if entry['function_executed']:
                formatted.append(f"\nFunction Executed: {entry['function_executed']}")
                
                if entry['function_arguments']:
                    formatted.append(f"Function Arguments: {entry['function_arguments']}")
                
                if entry['function_result']:
                    formatted.append(f"\nRaw Results:")
                    formatted.append("```")
                    formatted.append(str(entry['function_result']))
                    formatted.append("```")
                
                if entry['formatted_result']:
                    formatted.append(f"\nFormatted Output:")
                    formatted.append(entry['formatted_result'])
            else:
                formatted.append("\nNo function executed (conversational interaction)")
        
        return '\n'.join(formatted)
    
    def generate_quick_summary(self, history_data: list) -> dict:
        """Generate a quick statistical summary of the engagement"""
        if not history_data:
            return {
                'total_interactions': 0,
                'functions_executed': 0,
                'scans_performed': 0,
                'exploits_attempted': 0,
                'unique_targets': set()
            }
        
        stats = {
            'total_interactions': len(history_data),
            'functions_executed': 0,
            'scans_performed': 0,
            'exploits_attempted': 0,
            'unique_targets': set()
        }
        
        for entry in history_data:
            if entry['function_executed']:
                stats['functions_executed'] += 1
                
                # Count specific activity types
                if 'scan' in entry['function_executed'].lower():
                    stats['scans_performed'] += 1
                
                if 'exploit' in entry['function_executed'].lower() or 'run_exploit' in entry['function_executed']:
                    stats['exploits_attempted'] += 1
                
                # Extract target IPs
                if entry['function_arguments']:
                    if 'ip_address' in entry['function_arguments']:
                        stats['unique_targets'].add(entry['function_arguments']['ip_address'])
                    if 'target_ip' in entry['function_arguments']:
                        stats['unique_targets'].add(entry['function_arguments']['target_ip'])
        
        stats['unique_targets'] = list(stats['unique_targets'])
        
        return stats

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
    
    def format_scan_specific_port_result(self, raw_result: str, ip_address: str, port: str) -> str:
        """Parse and format scan_specific_port output with detailed service information"""
        lines = raw_result.split('\n')
        
        # Initialize variables
        port_state = None
        service_name = None
        service_version = None
        nse_output = []
        latency = None
        
        # Parse the nmap output
        in_port_section = False
        in_nse_output = False
        current_nse_script = None
        
        for line in lines:
            # Extract latency
            if 'latency' in line.lower():
                lat_match = re.search(r'\(([\d.]+)s latency\)', line)
                if lat_match:
                    latency = lat_match.group(1)
            
            # Find the PORT STATE SERVICE line (table header)
            if 'PORT' in line and 'STATE' in line and 'SERVICE' in line:
                in_port_section = True
                continue
            
            # Parse port information line
            if in_port_section and '/tcp' in line:
                parts = line.split()
                if len(parts) >= 4:
                    port_state = parts[1]  # e.g., "open"
                    service_name = parts[2]  # e.g., "mysql"
                    service_version = ' '.join(parts[3:])  # Everything after service name
                in_port_section = False
                in_nse_output = True
                continue
            
            # Parse NSE script output
            if in_nse_output and line.strip().startswith('|'):
                # This is NSE script output
                nse_output.append(line.strip())
            elif in_nse_output and not line.strip().startswith('|') and 'NSE:' not in line:
                # End of NSE output
                if line.strip() and not line.startswith('NSE:') and not line.startswith('Read data') and not line.startswith('Service detection') and not line.startswith('Nmap done'):
                    in_nse_output = False
        
        # Format the output
        result = f"## Port {port} Scan Results for {ip_address}\n\n"
        
        if not port_state:
            result += f"❌ **Port {port} appears to be closed or filtered.**\n"
            return result
        
        # Port status
        status_emoji = "✅" if port_state == "open" else "⚠️"
        result += f"{status_emoji} **Port Status:** {port_state.upper()}\n\n"
        
        # Service information
        result += "### Service Information\n\n"
        result += f"**Service:** {service_name}\n\n"
        if service_version:
            result += f"**Version:** {service_version}\n\n"
        if latency:
            result += f"**Latency:** {latency}s\n\n"
        
        # NSE Script Results
        if nse_output:
            result += "### Detailed Information (NSE Scripts)\n\n"
            result += "```\n"
            for line in nse_output:
                result += line + "\n"
            result += "```\n\n"
        
        # Extract specific information from NSE output
        extra_info = self._extract_service_details(nse_output, service_name)
        if extra_info:
            result += "### Key Details\n\n"
            for key, value in extra_info.items():
                result += f"- **{key}:** {value}\n"
            result += "\n"
        
        # Security recommendations
        result += "### 🔍 Next Steps\n\n"
        result += self._get_security_recommendations(service_name, service_version)
        
        return result
    
    def _extract_service_details(self, nse_lines: list, service: str) -> dict:
        """Extract specific details from NSE script output based on service type"""
        details = {}
        
        if service == 'mysql':
            for line in nse_lines:
                if 'Protocol:' in line:
                    details['Protocol Version'] = line.split('Protocol:')[1].strip()
                elif 'Version:' in line and 'Protocol' not in line:
                    details['MySQL Version'] = line.split('Version:')[1].strip()
                elif 'Thread ID:' in line:
                    details['Thread ID'] = line.split('Thread ID:')[1].strip()
                elif 'Status:' in line:
                    details['Status'] = line.split('Status:')[1].strip()
        
        elif service in ['ssh', 'openssh']:
            for line in nse_lines:
                if 'protocol version' in line.lower():
                    details['SSH Protocol'] = line.split(':')[1].strip()
                elif 'key type' in line.lower():
                    details['Key Type'] = line.split(':')[1].strip()
        
        elif service in ['http', 'https', 'http-proxy']:
            for line in nse_lines:
                if 'title:' in line.lower():
                    details['Page Title'] = line.split('title:')[1].strip()
                elif 'server:' in line.lower():
                    details['Web Server'] = line.split('server:')[1].strip()
        
        elif service == 'ftp':
            for line in nse_lines:
                if 'anonymous' in line.lower():
                    details['Anonymous Login'] = 'Enabled' if 'allowed' in line.lower() else 'Disabled'
        
        return details
    
    def _get_security_recommendations(self, service: str, version: str) -> str:
        """Provide security recommendations based on service type"""
        recommendations = []
        
        if service == 'mysql':
            recommendations.append("- Check for default credentials (root with no password)")
            recommendations.append("- Search for MySQL version-specific vulnerabilities using `find_vulnerabilities_for_service`")
            recommendations.append("- Test for SQL injection vulnerabilities")
            if version and '5.0' in version:
                recommendations.append("- ⚠️ MySQL 5.0 is **very old** and likely has critical vulnerabilities")
        
        elif service in ['ssh', 'openssh']:
            recommendations.append("- Test for weak SSH credentials")
            recommendations.append("- Check if password authentication is enabled")
            recommendations.append("- Verify SSH version for known exploits")
        
        elif service in ['http', 'https']:
            recommendations.append("- Perform web application scanning")
            recommendations.append("- Check for common web vulnerabilities (SQLi, XSS, CSRF)")
            recommendations.append("- Enumerate directories and files")
        
        elif service == 'ftp':
            recommendations.append("- Test anonymous FTP access")
            recommendations.append("- Check for weak credentials")
            recommendations.append("- Look for version-specific exploits")
        
        elif service == 'smb' or service == 'microsoft-ds':
            recommendations.append("- Check for EternalBlue (MS17-010) vulnerability")
            recommendations.append("- Enumerate SMB shares")
            recommendations.append("- Test for weak credentials")
        
        else:
            recommendations.append(f"- Search for known vulnerabilities: `find_vulnerabilities_for_service {service}`")
            recommendations.append("- Check for default credentials")
            recommendations.append("- Research service-specific attack vectors")
        
        return '\n'.join(recommendations)
    
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
        
        elif function_name == "scan_specific_port":
            ip_address = function_arguments.get("ip_address", "target") if function_arguments else "target"
            port = function_arguments.get("port", "unknown") if function_arguments else "unknown"
            return self.format_scan_specific_port_result(raw_result, ip_address, port)
        
        elif function_name == "find_website_servers":
            hostname = function_arguments.get("hostname", "website") if function_arguments else "website"
            return self.format_find_website_servers_result(raw_result, hostname)
        
        # For other functions, return raw result for now
        return f"**{function_name} Results:**\n\n```\n{raw_result}\n```"
    
    def format_find_website_servers_result(self, raw_result: str, hostname: str) -> str:
        """Format find_website_servers output into a readable summary"""
        import json
        
        try:
            # Parse the result if it's a JSON string
            if isinstance(raw_result, str):
                servers = json.loads(raw_result)
            else:
                servers = raw_result
            
            # Check if there's an error
            if isinstance(servers, dict) and 'error' in servers:
                return f"❌ **Error searching Shodan for {hostname}:**\n\n{servers.get('message', servers['error'])}"
            
            if not servers or len(servers) == 0:
                return f"**No servers found for {hostname}** on Shodan.\n\nThis could mean:\n- The domain is not publicly accessible\n- No servers are indexed by Shodan yet\n- The hostname is incorrect"
            
            result = f"## Shodan Results for {hostname}\n\n"
            result += f"**Found {len(servers)} server(s):**\n\n"
            
            for idx, (ip, info) in enumerate(servers.items(), 1):
                result += f"### Server {idx}: {ip}\n\n"
                
                # Last seen
                if info.get('last_seen'):
                    result += f"**Last Seen:** {info['last_seen']}\n\n"
                
                # Hostnames
                if info.get('hostnames'):
                    result += f"**Hostnames:**\n"
                    for hostname_entry in info['hostnames']:
                        result += f"- {hostname_entry}\n"
                    result += "\n"
                
                # Organization
                if info.get('organization'):
                    result += f"**Organization:** {info['organization']}\n\n"
                
                # Location
                if info.get('location'):
                    loc = info['location']
                    if loc.get('city') and loc.get('country'):
                        result += f"**Location:** {loc['city']}, {loc['country']}\n\n"
                    elif loc.get('country'):
                        result += f"**Location:** {loc['country']}\n\n"
                
                # Technologies
                if info.get('technologies'):
                    result += f"**Technologies:** {', '.join(info['technologies'])}\n\n"
                
                # Tags
                if info.get('tags'):
                    result += f"**Tags:** {', '.join(info['tags'])}\n\n"
                
                # SSL Certificate
                if info.get('ssl_certificate'):
                    ssl = info['ssl_certificate']
                    if ssl.get('issued_to') or ssl.get('issued_by'):
                        result += f"**SSL Certificate:**\n"
                        if ssl.get('issued_to', {}).get('common_name'):
                            result += f"- Common Name: {ssl['issued_to']['common_name']}\n"
                        if ssl.get('issued_by', {}).get('common_name'):
                            result += f"- Issued By: {ssl['issued_by']['common_name']}\n"
                        if ssl.get('issued_by', {}).get('organization'):
                            result += f"- CA: {ssl['issued_by']['organization']}\n"
                        if ssl.get('ssl_versions'):
                            result += f"- SSL/TLS Versions: {', '.join(ssl['ssl_versions'])}\n"
                        result += "\n"
                
                # Banner (HTTP response)
                if info.get('banner'):
                    result += f"**HTTP Response:**\n```\n{info['banner']}\n```\n\n"
                
                result += "---\n\n"
            
            result += f"\n**💡 Next Steps:**\n"
            result += f"- Scan discovered IPs: `scan_target <ip_address>`\n"
            result += f"- Identify services: `scan_specific_port <ip_address> <port>`\n"
            result += f"- Check for vulnerabilities on identified services\n"
            
            return result
            
        except Exception as e:
            # If parsing fails, return raw result
            return f"**find_website_servers Results:**\n\n```\n{raw_result}\n```\n\nError formatting results: {str(e)}"

class Agent:
    def __init__(self, exploiter=None):
        load_dotenv()
        self._client = None
        self._chat = None
        self.formatter = FormatterAgent()
        self.history = []
        self.scanner_functions = list()
        callables = [name for name in dir(Scanner) if callable(getattr(Scanner, name))]
        self.scanner_functions.extend(callables)
        self.exploiter = exploiter
        self.exploiter_functions = list()
        if exploiter:
            callables = [name for name in dir(Exploiter) if callable(getattr(Exploiter, name))]
            self.exploiter_functions.extend(callables)
        self.attacker = Attacker()
        self.attacker_functions = list()
        callables = [name for name in dir(Attacker) if callable(getattr(Attacker, name))]
        self.attacker_functions.extend(callables)
        self.documenter_functions = ['generate_pentest_report', 'get_engagement_summary']
        self.prompt = AGENT_PROMPT
        
    @property
    def client(self):
        if self._client is None:
            api_key = os.getenv('GOOGLE_API_KEY')
            self._client = genai.Client(api_key=api_key)
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
        print("Unformatted Agent response received:", response)
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
            
            # Ensure response_text is never empty
            if not response_text:
                response_text = "I'm processing your request."
            
            # Initialize history entry
            history_entry = {
                "query": query,
                "response": response_text,
                "function_executed": function_to_execute,
                "function_arguments": function_arguments,
                "function_result": None,
                "formatted_result": None
            }
            
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
                    
                    # Add results to history entry
                    history_entry["function_result"] = str(result)
                    history_entry["formatted_result"] = formatted_result
                    
                    await ws_manager.send_event(session_id, "function_result", formatted_result)
                    print("Formatted result sent to client")
                elif(function_to_execute and function_to_execute in self.exploiter_functions):
                    await ws_manager.send_event(session_id, "text_response_with_function", response_text)
                    print(f"Executing function: {function_to_execute}")
                    print(f"With arguments: {function_arguments}")
                    if not self.exploiter:
                        raise RuntimeError("Exploiter instance not initialized")
                    function = getattr(self.exploiter, function_to_execute)
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
                    
                    # Add results to history entry
                    history_entry["function_result"] = str(result)
                    history_entry["formatted_result"] = formatted_result
                    
                    await ws_manager.send_event(session_id, "function_result", formatted_result)
                    print("Formatted result sent to client")
                elif(function_to_execute and function_to_execute in self.attacker_functions):
                    await ws_manager.send_event(session_id, "text_response_with_function", response_text)
                    print(f"Executing attacker function: {function_to_execute}")
                    print(f"With arguments: {function_arguments}")
                    function = getattr(self.attacker, function_to_execute)
                    # Call function with or without arguments
                    if function_arguments:
                        result = function(**function_arguments)
                    else:
                        result = function()
                    print("Raw attacker function result:", result)
                    
                    # Format the result
                    formatted_result = self.formatter.format_result(
                        function_name=function_to_execute,
                        function_arguments=function_arguments,
                        raw_result=str(result)
                    )
                    
                    # Add results to history entry
                    history_entry["function_result"] = str(result)
                    history_entry["formatted_result"] = formatted_result
                    
                    await ws_manager.send_event(session_id, "function_result", formatted_result)
                    print("Attacker result sent to client")
                elif(function_to_execute and function_to_execute in self.documenter_functions):
                    await ws_manager.send_event(session_id, "text_response_with_function", response_text)
                    print(f"Executing documenter function: {function_to_execute}")
                    print(f"With arguments: {function_arguments}")
                    
                    # Call the documenter function
                    if function_to_execute == 'generate_pentest_report':
                        engagement_info = None
                        if function_arguments and 'engagement_info' in function_arguments:
                            engagement_info = function_arguments['engagement_info']
                        result = self.generate_pentest_report(engagement_info)
                    elif function_to_execute == 'get_engagement_summary':
                        result = self.get_engagement_summary()
                    else:
                        result = "Unknown documenter function"
                    
                    print("Documenter function executed")
                    
                    # Format the result
                    if function_to_execute == 'generate_pentest_report':
                        formatted_result = result  # Report is already formatted in Markdown
                    elif function_to_execute == 'get_engagement_summary':
                        # Format summary as readable text
                        formatted_result = f"""**Engagement Summary:**

- **Total Interactions:** {result['total_interactions']}
- **Functions Executed:** {result['functions_executed']}
- **Scans Performed:** {result['scans_performed']}
- **Exploits Attempted:** {result['exploits_attempted']}
- **Unique Targets:** {', '.join(result['unique_targets']) if result['unique_targets'] else 'None'}"""
                    else:
                        formatted_result = str(result)
                    
                    # Add results to history entry
                    history_entry["function_result"] = str(result)
                    history_entry["formatted_result"] = formatted_result
                    
                    await ws_manager.send_event(session_id, "function_result", formatted_result)
                    print("Documenter result sent to client")
                else:
                    await ws_manager.send_event(session_id, "text_response_no_function", response_text)
            else:
                # Handle execution without websocket (for testing/CLI usage)
                if function_to_execute:
                    if function_to_execute in self.scanner_functions:
                        function = getattr(Scanner(), function_to_execute)
                        result = function(**function_arguments) if function_arguments else function()
                        history_entry["function_result"] = str(result)
                    elif function_to_execute in self.exploiter_functions:
                        if not self.exploiter:
                            raise RuntimeError("Exploiter instance not initialized")
                        function = getattr(self.exploiter, function_to_execute)
                        result = function(**function_arguments) if function_arguments else function()
                        history_entry["function_result"] = str(result)
                    elif function_to_execute in self.attacker_functions:
                        function = getattr(self.attacker, function_to_execute)
                        result = function(**function_arguments) if function_arguments else function()
                        history_entry["function_result"] = str(result)
                    elif function_to_execute in self.documenter_functions:
                        if function_to_execute == 'generate_pentest_report':
                            engagement_info = function_arguments.get('engagement_info') if function_arguments else None
                            result = self.generate_pentest_report(engagement_info)
                        elif function_to_execute == 'get_engagement_summary':
                            result = self.get_engagement_summary()
                        history_entry["function_result"] = str(result)
            
            # Append to history
            self.history.append(history_entry)
            
        except Exception as e:
            if ws_manager and session_id:
                await ws_manager.send_event(session_id, "error", {"message": str(e)})
            print(f"Error in respond method: {e}")
    
    def get_history(self):
        """Get the complete history of interactions"""
        return self.history
    
    def get_last_n_history(self, n=5):
        """Get the last N entries from history"""
        return self.history[-n:] if len(self.history) >= n else self.history
    
    def clear_history(self):
        """Clear the history"""
        self.history = []
        return "History cleared"
    
    def generate_pentest_report(self, engagement_info: dict = None) -> str:
        """
        Generate a comprehensive penetration testing report
        
        Args:
            engagement_info: Optional dict with engagement metadata
                - client: Client organization name
                - engagement_type: Type of engagement
                - date: Test date
                - tester: Tester name/team
        
        Returns:
            Complete penetration testing report in Markdown format
        """
        documenter = DocumenterAgent()
        report = documenter.generate_report(self.history, engagement_info)
        return report
    
    def get_engagement_summary(self) -> dict:
        """Get a quick statistical summary of the engagement"""
        documenter = DocumenterAgent()
        return documenter.generate_quick_summary(self.history)
    
if __name__ == "__main__":
    agent = Agent()
    explanation = agent.respond("Scan the network")
    print(explanation)
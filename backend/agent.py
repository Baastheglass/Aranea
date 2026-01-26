import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from agent_tools import Scanner, Exploiter
class Agent:
    def __init__(self):
        load_dotenv()
        self.client = genai.Client()
        self.chat = self.client.chats.create(model="gemini-2.5-flash")
        self.scanner_functions = list()
        callables = [name for name in dir(Scanner) if callable(getattr(Scanner, name))]
        self.scanner_functions.extend(callables)
        self.exploiter_functions = list()
        callables = [name for name in dir(Exploiter) if callable(getattr(Exploiter, name))]
        self.exploiter_functions.extend(callables)
        self.prompt = """You are Aranea, an expert penetration testing assistant designed to help security professionals conduct network reconnaissance and vulnerability assessments. Your role is to guide users through pentesting activities using available tools and provide clear, actionable insights.

                        AVAILABLE FUNCTIONS:
                        - check_if_host_active(ip_address: str): Check if a specific IP address is active on the network
                        - scan_entire_network(): Scan the entire local network to discover active hosts
                        - get_ip_of_website(website: str): Resolve the IP address of a domain/website
                        - get_open_ports(ip_address: str): Scan all ports on a target IP to identify open ports
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
                        response: I'll perform a comprehensive port scan on 192.168.1.100 to identify all open ports. This may take a few minutes.
                        function_to_execute: get_open_ports
                        function_arguments: {"ip_address": "192.168.1.100"}

                        User: "Is 10.0.0.5 active?"
                        response: I'll check if the host at 10.0.0.5 is active and responding on the network.
                        function_to_execute: check_if_host_active
                        function_arguments: {"ip_address": "10.0.0.5"}

                        User: "Find vulnerabilities for Apache"
                        response: I'll search for known vulnerabilities affecting Apache.
                        function_to_execute: find_vulnerabilities_for_service
                        function_arguments: {"service_name": "apache"}

                        User: "What is penetration testing?"
                        response: Penetration testing is a simulated cyber attack against your system to identify exploitable vulnerabilities. It helps organizations strengthen their security posture by finding weaknesses before malicious actors do.
                        function_to_execute: null
                        function_arguments: null"""
        
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
                    await ws_manager.send_event(session_id, "text_response_with_function", response)
                    print(f"Executing function: {function_to_execute}")
                    print(f"With arguments: {function_arguments}")
                    function = getattr(Scanner(), function_to_execute)
                    # Call function with or without arguments
                    if function_arguments:
                        result = function(**function_arguments)
                    else:
                        result = function()
                    await ws_manager.send_event(session_id, "function_result", result)
                    print("Function result:", result)
                elif(function_to_execute and function_to_execute in self.exploiter_functions):
                    await ws_manager.send_event(session_id, "text_response_with_function", response)
                    print(f"Executing function: {function_to_execute}")
                    print(f"With arguments: {function_arguments}")
                    function = getattr(Exploiter(), function_to_execute)
                    # Call function with or without arguments
                    if function_arguments:
                        result = function(**function_arguments)
                    else:
                        result = function()
                    await ws_manager.send_event(session_id, "function_result", result)
                    print("Function result:", result)
                else:
                    await ws_manager.send_event(session_id, "text_response_no_function", response)   
        except Exception as e:
            await ws_manager.send_event(session_id, "error", {"message": str(e)})
            print(f"Error in respond method: {e}")
    
if __name__ == "__main__":
    agent = Agent()
    explanation = agent.respond("Scan the network")
    print(explanation)
import { useState, useRef, useEffect } from "react";
import { BACKEND_URL, WS_URL } from "../constants";

export default function ChatInterface({ username, chatId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState(null);
  const [loading, setLoading] = useState(true);
  const inputRef = useRef(null);
  const wsRef = useRef(null);
  const streamingIntervalRef = useRef(null);
  const messagesEndRef = useRef(null);

  // Load messages when chatId changes
  useEffect(() => {
    if (!chatId) {
      setMessages([]);
      setLoading(false);
      return;
    }

    const loadMessages = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${BACKEND_URL}/chats/${chatId}/messages`);
        const data = await response.json();
        
        if (data.success) {
          // Transform API messages to component format
          const loadedMessages = data.messages.map((msg, index) => ({
            id: index + 1,
            sender: msg.sender,
            text: msg.text,
          }));
          
          // Add welcome message if no messages exist
          if (loadedMessages.length === 0) {
            loadedMessages.push({
              id: 1,
              sender: "aranea",
              text: `Welcome ${username}. I am Aranea, a distributed neural web. How may I assist you today?`
            });
          }
          
          setMessages(loadedMessages);
        }
      } catch (error) {
        console.error("Error loading messages:", error);
        // Add welcome message on error
        setMessages([{
          id: 1,
          sender: "aranea",
          text: `Welcome ${username}. I am Aranea, a distributed neural web. How may I assist you today?`
        }]);
      } finally {
        setLoading(false);
      }
    };

    loadMessages();
  }, [chatId, username]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingMessage]);

  // Function to stop streaming
  const stopStreaming = () => {
    if (streamingIntervalRef.current) {
      clearInterval(streamingIntervalRef.current);
      streamingIntervalRef.current = null;
    }
    
    // Add partial message if any
    if (streamingMessage && streamingMessage.text) {
      setMessages(prev => [...prev, {
        ...streamingMessage,
        wasStreamed: true
      }]);
    }
    
    setStreamingMessage(null);
    setIsTyping(false);
  };

  // Listen for ESC key to stop streaming
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && (isTyping || streamingMessage)) {
        stopStreaming();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isTyping, streamingMessage]);

  // Function to format find_website_servers results
  const formatWebsiteServersResults = (text) => {
    try {
      // Check if this is a find_website_servers result
      if (!text.includes('find_website_servers Results:')) {
        return text;
      }

      // Extract the content between triple backticks
      const jsonMatch = text.match(/```\s*([\s\S]*?)\s*```/);
      if (!jsonMatch) return text;

      let pythonDict = jsonMatch[1].trim();
      
      // More robust Python dict to JSON conversion
      // Step 1: Replace Python boolean/null values
      pythonDict = pythonDict
        .replace(/\bNone\b/g, 'null')
        .replace(/\bTrue\b/g, 'true')
        .replace(/\bFalse\b/g, 'false');
      
      // Step 2: Handle single quotes more carefully
      // This regex handles escaped quotes and converts single quotes to double quotes
      // It preserves escaped characters within strings
      pythonDict = pythonDict.replace(/'/g, '"');
      
      // Step 3: Fix any JSON formatting issues
      // Remove trailing commas before closing braces/brackets
      pythonDict = pythonDict.replace(/,(\s*[}\]])/g, '$1');
      
      let data;
      try {
        data = JSON.parse(pythonDict);
      } catch (parseError) {
        // If parsing fails, try an alternative approach
        console.warn('Direct JSON parse failed, attempting eval approach:', parseError.message);
        // Return original text with a note
        return text.replace('```', '```\n(Note: Could not parse results for formatting)\n');
      }
      
      // Format as readable text
      let formatted = '**Website Servers Found:**\n\n';
      let count = 1;
      
      for (const [key, server] of Object.entries(data)) {
        formatted += `═══════════════════════════════════════\n`;
        formatted += `[${count}] ${server.ip_address || key}\n`;
        formatted += `═══════════════════════════════════════\n`;
        
        if (server.hostnames && server.hostnames.length > 0) {
          formatted += `Hostnames:\n`;
          const hostnames = Array.isArray(server.hostnames) ? server.hostnames : [server.hostnames];
          hostnames.forEach(h => formatted += `  • ${h}\n`);
        }
        
        if (server.organization) {
          formatted += `\nOrganization: ${server.organization}\n`;
        }
        
        if (server.location) {
          formatted += `Location: ${server.location.city || 'Unknown'}, ${server.location.country || 'Unknown'}\n`;
        }
        
        if (server.technologies && server.technologies.length > 0) {
          formatted += `Technologies: ${server.technologies.join(', ')}\n`;
        }
        
        if (server.tags && server.tags.length > 0) {
          formatted += `Tags: ${server.tags.join(', ')}\n`;
        }
        
        if (server.ssl_certificate) {
          if (server.ssl_certificate.issued_to && server.ssl_certificate.issued_to.common_name) {
            formatted += `\nSSL Certificate:\n`;
            formatted += `  • Issued To: ${server.ssl_certificate.issued_to.common_name}\n`;
            if (server.ssl_certificate.issued_by && server.ssl_certificate.issued_by.common_name) {
              formatted += `  • Issued By: ${server.ssl_certificate.issued_by.common_name}\n`;
            }
            if (server.ssl_certificate.ssl_versions && server.ssl_certificate.ssl_versions.length > 0) {
              formatted += `  • SSL Versions: ${server.ssl_certificate.ssl_versions.join(', ')}\n`;
            }
          }
        }
        
        if (server.banner) {
          // Truncate long banners
          const bannerPreview = server.banner.length > 200 
            ? server.banner.substring(0, 200) + '...' 
            : server.banner;
          formatted += `\nBanner:\n${bannerPreview}\n`;
        }
        
        if (server.last_seen) {
          formatted += `\nLast Seen: ${server.last_seen}\n`;
        }
        
        formatted += '\n';
        count++;
      }
      
      formatted += `\nTotal servers found: ${count - 1}`;
      
      return formatted;
    } catch (error) {
      console.error('Error formatting website servers results:', error);
      console.error('Error details:', error.message);
      // Return original text if parsing fails
      return text;
    }
  };

  // Function to stream text character by character
  const streamText = (text, messageId) => {
    return new Promise((resolve) => {
      // Format the text if it's a find_website_servers result
      const formattedText = formatWebsiteServersResults(text);
      
      let index = 0;
      const newMessage = {
        id: messageId || Date.now() + Math.random(),
        sender: "aranea",
        text: ""
      };
      
      setStreamingMessage(newMessage);
      
      // Clear any existing interval
      if (streamingIntervalRef.current) {
        clearInterval(streamingIntervalRef.current);
      }
      
      streamingIntervalRef.current = setInterval(() => {
        if (index < formattedText.length) {
          const char = formattedText[index];
          setStreamingMessage(prev => ({
            ...prev,
            text: prev.text + char
          }));
          index++;
        } else {
          clearInterval(streamingIntervalRef.current);
          streamingIntervalRef.current = null;
          
          // Add completed message to messages array with wasStreamed flag
          setMessages(prev => [...prev, {
            ...newMessage,
            text: formattedText,
            wasStreamed: true
          }]);
          setStreamingMessage(null);
          resolve();
        }
      }, 5); // Adjust speed here (milliseconds per character)
    });
  };

  useEffect(() => {
    // Only connect WebSocket if chatId is available
    if (!chatId) return;
    
    // Connect to WebSocket
    const ws = new WebSocket(`${WS_URL}/ws/${username}/${chatId}`);
    
    ws.onopen = () => {
      console.log("WebSocket connected for chat:", chatId);
    };
    
    ws.onmessage = async (event) => {
      const eventData = JSON.parse(event.data);
      console.log("Received event:", eventData);
      
      // Handle different event types
      if (eventData.event === "thinking") {
        setIsTyping(true);
      } else if (eventData.event === "text_response_no_function") {
        setIsTyping(false);
        // Extract response text from the data
        let responseText = eventData.data;
        if (typeof responseText === 'string' && responseText.includes('response:')) {
          const lines = responseText.split('\n');
          for (const line of lines) {
            if (line.trim().startsWith('response:')) {
              responseText = line.replace('response:', '').trim();
              break;
            }
          }
        }
        // Stream the response only if not empty
        if (responseText && String(responseText).trim()) {
          await streamText(responseText);
        }
      } else if (eventData.event === "text_response_with_function") {
        setIsTyping(true);
        // Extract response text from the data
        let responseText = eventData.data;
        if (typeof responseText === 'string' && responseText.includes('response:')) {
          const lines = responseText.split('\n');
          for (const line of lines) {
            if (line.trim().startsWith('response:')) {
              responseText = line.replace('response:', '').trim();
              break;
            }
          }
        }
        // Stream the response only if not empty
        if (responseText && String(responseText).trim()) {
          await streamText(responseText);
        }
      } else if (eventData.event === "function_result") {
        setIsTyping(false);
        // Format the result data
        let resultText = '';
        if (typeof eventData.data === 'string') {
          // If it's a string with escaped newlines, preserve them
          resultText = eventData.data;
        } else {
          resultText = JSON.stringify(eventData.data, null, 2);
        }
        // Stream the result only if not empty
        if (resultText && resultText.trim()) {
          await streamText(resultText);
        }
      } else if (eventData.event === "response" || eventData.event === "error") {
        setIsTyping(false);
        const responseText = eventData.data.message || eventData.data.text || JSON.stringify(eventData.data);
        // Stream the response only if not empty
        if (responseText && responseText.trim()) {
          await streamText(responseText);
        }
      } else if (eventData.event === "tool_call" || eventData.event === "tool_result") {
        // Optionally display tool calls
        const toolText = `[${eventData.event}] ${eventData.data.message || JSON.stringify(eventData.data)}`;
        // Stream tool info only if not empty
        if (toolText && toolText.trim()) {
          await streamText(toolText);
        }
      }
    };
    
    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      setIsTyping(false);
    };
    
    ws.onclose = () => {
      console.log("WebSocket disconnected");
      setIsTyping(false);
    };
    
    wsRef.current = ws;
    
    // Cleanup on unmount or when chat changes
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
      if (streamingIntervalRef.current) {
        clearInterval(streamingIntervalRef.current);
      }
    };
  }, [chatId, username]);

  const handleContainerClick = () => {
    // Focus input when clicking anywhere in the chat area
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isTyping) return;

    const userMessage = {
      id: Date.now(),
      sender: username,
      text: trimmed
    };

    // Immediately show user message
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    
    // Show typing indicator
    setIsTyping(true);

    // Send message via WebSocket
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: "query",
        message: trimmed
      }));
    } else {
      // Fallback error if WebSocket is not connected
      setIsTyping(false);
      const errorReply = {
        id: Date.now() + 1,
        sender: "aranea",
        text: "WebSocket not connected. Please refresh the page."
      };
      setMessages((prev) => [...prev, errorReply]);
    }
  };

  // Show loading state
  if (loading) {
    return (
      <div className="chat-root">
        <div className="chat-shell">
          <main className="chat-main">
            <div className="loading-state">Loading messages...</div>
          </main>
        </div>
      </div>
    );
  }

  // Show "No chat selected" state
  if (!chatId) {
    return (
      <div className="chat-root">
        <div className="chat-shell">
          <main className="chat-main">
            <div className="empty-state">
              <h2>No chat selected</h2>
              <p>Select a chat from the sidebar or create a new one to get started.</p>
            </div>
          </main>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-root">
      <div className="ascii-layer">
        <pre className="ascii-globe">
{String.raw`⠀⠀⠀⠀⠀⠀⢰⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡄⠀⠀⠀⠀⠀⠀



⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⠀

⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⠀

⠀⠀⠀⠀⠀⠀⣾⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⠀

⡇⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⢀

⡇⠀⠀⠀⠀⠀⢨⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⡃⠀⠀⠀⠀⠀⠘

⢰⠀⠀⠀⠀⠀⢰⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⡆⠀⠀⠀⠀⠀⡇

⢸⡄⠀⠀⠀⠀⠀⣿⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣿⠀⠀⠀⠀⠀⢠⠇

⠘⣧⠀⠀⠀⠀⠀⢸⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⠀⣼⠀

⠀⠹⣆⠀⠀⠀⠀⠀⣿⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣿⠀⠀⠀⠀⠀⣰⠏⠀

⠀⠀⠹⣧⠀⠀⠀⠀⠸⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⡏⠀⠀⠀⠀⣰⠏⠀⠀

⠀⠀⠀⠹⣧⠀⠀⠀⠀⠹⣷⡀⠀⠀⠀⠀⠀⠀⢀⣾⠍⠀⠀⠀⠀⣴⠏⠀⠀⠀

⠀⠀⠀⠀⠙⡧⣀⠀⠀⠀⠘⣿⡄⠀⠀⠀⠀⢠⣾⠏⠀⠀⠀⣀⣼⠏⠀⠀⠀⠀

⠀⠀⠀⠀⠀⠈⠙⠻⣶⣤⡀⠘⢿⡄⣀⣀⢠⣿⠃⠀⣠⣴⡾⠛⠁⠀⠀⠀⠀⠀

⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠻⢷⣜⣿⣿⣿⣿⣣⣶⠿⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀

⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣠⣤⣽⣿⣿⣿⣿⣯⣅⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀

⠀⠀⠀⠀⢀⣤⣴⠾⠿⠛⢋⣥⣿⣿⣿⣿⣿⣿⣍⠛⠻⠿⢶⣤⣄⡀⠀⠀⠀⠀

⠀⠀⠀⢰⡟⠉⠀⠀⠀⣠⡾⣻⢟⣥⣶⣿⣿⣿⡿⣷⣄⠀⠀⠈⠀⢿⡄⠀⠀⠀

⠀⠀⢠⡟⠀⠀⠀⣠⡾⠋⢰⣯⣾⣿⣿⣿⣿⣿⣿⡈⠻⣷⣄⠀⠀⠈⢷⡀⠀⠀

⠀⢀⡾⠁⠀⠀⣼⠋⠀⠀⢸⢸⣿⡿⠿⣿⠿⣿⣿⡇⠀⠈⢫⣧⠀⠀⠘⣷⠀⠀

⠀⣼⠃⠀⠀⢠⣿⠀⠀⠀⠸⣿⣿⣿⡆⠀⣼⡟⣹⠀⠀⠀⠀⣿⠀⠀⠀⠸⣧⠀

⠀⡟⠀⠀⠀⢸⡏⠀⠀⠀⠀⠙⢿⣯⣶⣶⣮⡿⠃⠀⠀⠀⠀⢹⡇⠀⠀⠀⣿⠀

⠀⡇⠀⠀⠀⣼⠇⠀⠀⠀⠀⠀⠀⠉⠛⠋⠉⠀⠀⠀⠀⠀⠀⢸⣇⠀⠀⠀⢸⠀

⠀⡇⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⠀⠀⠀⢸⠀

⠀⡇⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀⠀⠀⢸⠀

⠀⡇⠀⠀⠀⢸⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⡏⠀⠀⠀⢸⠀

⠀⠁⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⠁⠀⠀⠀⠈⠀

⠀⠀⠀⠀⠀⠀⠸⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡇⠀⠀⠀⠀⠀⠀

⠀⠀⠀⠀⠀⠀⠀⢧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡸⠀⠀⠀⠀⠀⠀⠀

⠀⠀⠀⠀⠀⠀⠀⠈⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠁⠀⠀⠀⠀⠀⠀⠀`}
        </pre>
      </div>

      <div className="chat-shell" onClick={handleContainerClick}>
        <main className="chat-main">
          <div className="chat-messages">
            <pre className="terminal-header">
{String.raw`⠀⠀⠀⠀⠀⠀⠀⢀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀    ___                                 
⠀⠀⠀⠀⢠⣴⣿⣿⣿⣷⣼⣿⠀⣴⠾⠷⠶⠦⡄⠀⠀⠀   /   |  _________ _____  ___  ____  
⠀⢠⡤⢶⣦⣾⣿⣿⣿⣿⣿⣿⠀⣿⣶⣶⣦⣄⠳⣤⣤⠄  / /| | / ___/ __ \`/ __ \/ _ \/ __\
⠀⢀⣼⣳⡿⢻⣿⣿⣿⣿⣿⣿⣶⣿⣿⣗⠈⠙⠻⣶⣄⡀ / ___ |/ /  / /_/ / / / /  __/ /_/ / 
⠀⣰⠿⠁⢀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡄⠀⠀⠈⠳/_/  |_/_/   \__,_/_/ /_/\___/\__,_/  
⢀⡟⠀⢰⣿⠟⠻⢿⣿⣿⣿⣿⣿⣿⠉⠁⠈⠻⣶⣄⠀⠀
⣼⠃⠀⣼⡟⠀⠀⢸⣿⡿⠉⣿⡿⠿⠛⣿⡄⠀⠀⠙⠿⣆  TERMINAL v1.0.0 
⠁⠀⢸⡟⠀⠀⠀⢸⣿⠀⠀⣿⠁⠀⠀⠈⠃⠀⠀⠀⠀⠘  ════════════════════════════════════════
⠀⠀⣼⠃⠀⠀⠀⢸⡟⠀⠀⡿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⣠⡏⠀⠀⠀⠀⣼⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠻⠃⠀⠀⠀⠀⣻⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠻⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
`}
            </pre>
            {messages.map((m) => {
              // Format the text if it contains find_website_servers results
              const displayText = m.sender === "aranea" ? formatWebsiteServersResults(m.text) : m.text;
              return (
                <div
                  key={m.id}
                  className={
                    m.sender !== "aranea" ? "message-row user" : "message-row sentinel"
                  }
                >
                  <pre className={m.wasStreamed ? "message-line no-animation" : "message-line"}>
{m.sender !== "aranea"
  ? `${m.sender}@web:~$ ${displayText}`
  : `aranea@web:~$ ${displayText}`}
                  </pre>
                </div>
              );
            })}
            {streamingMessage && (
              <div className="message-row sentinel">
                <pre className="message-line">
{`aranea@web:~$ ${streamingMessage.text}`}<span className="cursor">▊</span>
                </pre>
              </div>
            )}
            {isTyping && !streamingMessage && (
              <div className="message-row sentinel">
                <pre className="message-line typing-indicator">
{`aranea@web:~$ `}<span className="typing-dots">
  <span className="dot">.</span>
  <span className="dot">.</span>
  <span className="dot">.</span>
</span>
                </pre>
              </div>
            )}
            {!isTyping && !streamingMessage && (
              <form onSubmit={handleSend} className="terminal-input-row">
                <span className="prompt-label">{username}@web:~$</span>
                <input
                  ref={inputRef}
                  type="text"
                  className="chat-input"
                  placeholder=""
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                />
              </form>
            )}
            <div ref={messagesEndRef} />
          </div>
        </main>
      </div>
    </div>
  );
}



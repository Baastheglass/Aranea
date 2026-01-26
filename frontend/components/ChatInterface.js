import { useState, useRef, useEffect } from "react";

export default function ChatInterface({ username }) {
  const initialMessages = [
    {
      id: 1,
      sender: "aranea",
      text: `Welcome ${username}. I am Aranea, a distributed neural web. How may I assist you today?`
    }
  ];

  const [messages, setMessages] = useState(initialMessages);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const inputRef = useRef(null);
  const wsRef = useRef(null);
  const sessionIdRef = useRef(`session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`);

  useEffect(() => {
    // Connect to WebSocket
    const ws = new WebSocket(`ws://localhost:8000/ws/${sessionIdRef.current}`);
    
    ws.onopen = () => {
      console.log("WebSocket connected");
    };
    
    ws.onmessage = (event) => {
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
        const araneaReply = {
          id: Date.now() + Math.random(),
          sender: "aranea",
          text: responseText
        };
        setMessages((prev) => [...prev, araneaReply]);
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
        const araneaReply = {
          id: Date.now() + Math.random(),
          sender: "aranea",
          text: responseText
        };
        setMessages((prev) => [...prev, araneaReply]);
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
        const resultMessage = {
          id: Date.now() + Math.random(),
          sender: "aranea",
          text: resultText
        };
        setMessages((prev) => [...prev, resultMessage]);
      } else if (eventData.event === "response" || eventData.event === "error") {
        setIsTyping(false);
        const araneaReply = {
          id: Date.now() + Math.random(),
          sender: "aranea",
          text: eventData.data.message || eventData.data.text || JSON.stringify(eventData.data)
        };
        setMessages((prev) => [...prev, araneaReply]);
      } else if (eventData.event === "tool_call" || eventData.event === "tool_result") {
        // Optionally display tool calls
        const toolMessage = {
          id: Date.now() + Math.random(),
          sender: "aranea",
          text: `[${eventData.event}] ${eventData.data.message || JSON.stringify(eventData.data)}`
        };
        setMessages((prev) => [...prev, toolMessage]);
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
    
    // Cleanup on unmount
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []);

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
      sender: "user",
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
            {messages.map((m) => (
              <div
                key={m.id}
                className={
                  m.sender === "user" ? "message-row user" : "message-row sentinel"
                }
              >
                <pre className="message-line">
{m.sender === "user"
  ? `user@web:~$ ${m.text}`
  : `aranea@web:~$ ${m.text}`}
                </pre>
              </div>
            ))}
            {isTyping && (
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
            <form onSubmit={handleSend} className="terminal-input-row">
              <span className="prompt-label">user@web:~$</span>
              <input
                ref={inputRef}
                type="text"
                className="chat-input"
                placeholder=""
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={isTyping}
              />
            </form>
          </div>
        </main>
      </div>
    </div>
  );
}



import { useState } from "react";

const initialMessages = [
  {
    id: 1,
    sender: "aranea",
    text:
      "I am Aranea, a distributed neural web. Connect your backend and I will start weaving insights from your data."
  }
];

export default function ChatInterface() {
  const [messages, setMessages] = useState(initialMessages);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  const handleSend = async (e) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed) return;

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

    try {
      // Call backend API
      const response = await fetch("http://localhost:8000/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: trimmed }),
      });

      const data = await response.json();

      // Hide typing indicator
      setIsTyping(false);

      // Add Aranea response
      const araneaReply = {
        id: Date.now() + 1,
        sender: "aranea",
        text: data.response
      };

      setMessages((prev) => [...prev, araneaReply]);
    } catch (error) {
      setIsTyping(false);
      const errorReply = {
        id: Date.now() + 1,
        sender: "aranea",
        text: "Error connecting to backend. Please ensure the server is running on port 8000."
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

      <div className="chat-shell">
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
                type="text"
                className="chat-input"
                placeholder=""
                value={input}
                onChange={(e) => setInput(e.target.value)}
              />
            </form>
          </div>
        </main>
      </div>
    </div>
  );
}



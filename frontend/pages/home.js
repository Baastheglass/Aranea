import { useEffect, useState } from "react";
import { useRouter } from "next/router";

export default function Home() {
  const [username, setUsername] = useState("");
  const router = useRouter();

  useEffect(() => {
    const currentUser = localStorage.getItem("currentUser");
    if (!currentUser) {
      router.push("/login");
    } else {
      setUsername(currentUser);
    }
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("currentUser");
    router.push("/login");
  };

  const handleAccessTerminal = () => {
    router.push("/chat");
  };

  if (!username) return null;

  return (
    <div className="home-container">
      <div className="home-content">
        <div className="home-header">
          <pre className="home-logo">
{String.raw`⠀⠀⠀⠀⠀⠀⠀⢀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⢠⣴⣿⣿⣿⣷⣼⣿⠀⣴⠾⠷⠶⠦⡄⠀⠀⠀
⠀⢠⡤⢶⣦⣾⣿⣿⣿⣿⣿⣿⠀⣿⣶⣶⣦⣄⠳⣤⣤⠄
⠀⢀⣼⣳⡿⢻⣿⣿⣿⣿⣿⣿⣶⣿⣿⣗⠈⠙⠻⣶⣄⡀
⠀⣰⠿⠁⢀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡄⠀⠀⠈⠳
⢀⡟⠀⢰⣿⠟⠻⢿⣿⣿⣿⣿⣿⣿⠉⠁⠈⠻⣶⣄⠀⠀
⣼⠃⠀⣼⡟⠀⠀⢸⣿⡿⠉⣿⡿⠿⠛⣿⡄⠀⠀⠙⠿⣆
⠁⠀⢸⡟⠀⠀⠀⢸⣿⠀⠀⣿⠁⠀⠀⠈⠃⠀⠀⠀⠀⠘
⠀⠀⣼⠃⠀⠀⠀⢸⡟⠀⠀⡿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⣠⡏⠀⠀⠀⠀⣼⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠻⠃⠀⠀⠀⠀⣻⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠻⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀`}
          </pre>
          <h1 className="home-title">ARANEA</h1>
          <p className="home-subtitle">Neural Web Interface</p>
        </div>

        <div className="home-terminal">
          <pre className="home-welcome">
{`┌────────────────────────────────────────┐
│                                        │
│  Welcome back, ${username.padEnd(24)}│
│  Status: Connected to Aranea Web       │
│  Neural Nodes: Online                  │
│  Access Level: Authenticated           │
│                                        │
└────────────────────────────────────────┘`}
          </pre>

          <div className="home-actions">
            <button onClick={handleAccessTerminal} className="home-btn primary">
              ACCESS TERMINAL
            </button>
            <button onClick={handleLogout} className="home-btn secondary">
              DISCONNECT
            </button>
          </div>

          <div className="home-info">
            <div className="info-card">
              <h3>Neural Analysis</h3>
              <p>Access advanced AI insights through the distributed neural web</p>
            </div>
            <div className="info-card">
              <h3>Web Intelligence</h3>
              <p>Weaving connections across data to deliver meaningful patterns</p>
            </div>
            <div className="info-card">
              <h3>Real-time Processing</h3>
              <p>Instant responses powered by cutting-edge language models</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

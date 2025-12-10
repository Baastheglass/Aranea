import { useState } from "react";
import { useRouter } from "next/router";

export default function AuthForm({ mode }) {
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
  });
  const [error, setError] = useState("");
  const router = useRouter();

  const handleSubmit = (e) => {
    e.preventDefault();
    setError("");

    // Validation
    if (!formData.username || !formData.password) {
      setError("Username and password are required");
      return;
    }

    if (mode === "signup" && !formData.email) {
      setError("Email is required for signup");
      return;
    }

    if (mode === "signup") {
      // Store user data in localStorage for demo
      const users = JSON.parse(localStorage.getItem("araneaUsers") || "{}");
      
      if (users[formData.username]) {
        setError("Username already exists");
        return;
      }

      users[formData.username] = {
        email: formData.email,
        password: formData.password, // In production, this would be hashed
      };

      localStorage.setItem("araneaUsers", JSON.stringify(users));
      localStorage.setItem("currentUser", formData.username);
      router.push("/home");
    } else {
      // Login
      const users = JSON.parse(localStorage.getItem("araneaUsers") || "{}");
      
      if (!users[formData.username]) {
        setError("User not found");
        return;
      }

      if (users[formData.username].password !== formData.password) {
        setError("Invalid password");
        return;
      }

      localStorage.setItem("currentUser", formData.username);
      router.push("/home");
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-header">
        <pre className="auth-logo">
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
        <h1 className="auth-title">ARANEA</h1>
        <p className="auth-subtitle">Distributed Neural Web</p>
      </div>

      <form onSubmit={handleSubmit} className="auth-form">
        <div className="auth-field">
          <label className="auth-label">username@web:~$</label>
          <input
            type="text"
            className="auth-input"
            placeholder="username"
            value={formData.username}
            onChange={(e) => setFormData({ ...formData, username: e.target.value })}
          />
        </div>

        {mode === "signup" && (
          <div className="auth-field">
            <label className="auth-label">email@web:~$</label>
            <input
              type="email"
              className="auth-input"
              placeholder="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
          </div>
        )}

        <div className="auth-field">
          <label className="auth-label">password@web:~$</label>
          <input
            type="password"
            className="auth-input"
            placeholder="password"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
          />
        </div>

        {error && <div className="auth-error">{error}</div>}

        <button type="submit" className="auth-submit">
          {mode === "signup" ? "CONNECT TO WEB" : "ACCESS TERMINAL"}
        </button>

        <div className="auth-switch">
          {mode === "signup" ? (
            <p>
              Already connected?{" "}
              <a href="/login" className="auth-link">
                Access Terminal
              </a>
            </p>
          ) : (
            <p>
              New to Aranea?{" "}
              <a href="/signup" className="auth-link">
                Join the Web
              </a>
            </p>
          )}
        </div>
      </form>
    </div>
  );
}

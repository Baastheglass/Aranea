import { useState, useEffect } from "react";
import { useRouter } from "next/router";
import styles from "../styles/ChatSidebar.module.css";
import { BACKEND_URL } from "../constants";

export default function ChatSidebar({ username, currentChatId, onChatSelect, onNewChat, width = 280, onResize }) {
  const router = useRouter();
  const [chats, setChats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingChatId, setEditingChatId] = useState(null);
  const [editTitle, setEditTitle] = useState("");
  const [isResizing, setIsResizing] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(null);

  useEffect(() => {
    fetchChats();
  }, [username]);

  // Handle resize
  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e) => {
      const newWidth = e.clientX;
      // Constrain width between 200px and 600px
      if (newWidth >= 200 && newWidth <= 600) {
        onResize(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing, onResize]);

  const handleResizeStart = () => {
    setIsResizing(true);
  };

  // Sort chats by created_at, most recent first
  const sortChatsByDate = (chatList) => {
    return [...chatList].sort((a, b) => {
      const dateA = new Date(a.created_at);
      const dateB = new Date(b.created_at);
      return dateB - dateA; // Descending order (most recent first)
    });
  };

  const fetchChats = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${BACKEND_URL}/chats/${username}`);
      const data = await response.json();
      
      if (data.success) {
        setChats(sortChatsByDate(data.chats));
      }
    } catch (error) {
      console.error("Error fetching chats:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/chats/create`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: username,
          title: `Chat ${new Date().toLocaleDateString()}`,
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        // Add new chat and sort to ensure it's at the top
        const updatedChats = [data.chat, ...chats];
        setChats(sortChatsByDate(updatedChats));
        onNewChat(data.chat.chat_id);
      }
    } catch (error) {
      console.error("Error creating new chat:", error);
    }
  };

  const handleDeleteChat = async (chatId, e) => {
    e.stopPropagation(); // Prevent triggering chat selection
    
    if (!confirm("Are you sure you want to delete this chat?")) {
      return;
    }

    try {
      const response = await fetch(`${BACKEND_URL}/chats/${chatId}`, {
        method: "DELETE",
      });

      const data = await response.json();
      
      if (data.success) {
        const remainingChats = chats.filter(chat => chat.chat_id !== chatId);
        setChats(sortChatsByDate(remainingChats));
        
        // If the deleted chat was the current one, select another chat
        if (chatId === currentChatId && chats.length > 1) {
          const otherChat = chats.find(chat => chat.chat_id !== chatId);
          if (otherChat) {
            onChatSelect(otherChat.chat_id);
          }
        }
      }
    } catch (error) {
      console.error("Error deleting chat:", error);
    }
  };

  const handleStartEdit = (chat, e) => {
    e.stopPropagation(); // Prevent triggering chat selection
    setEditingChatId(chat.chat_id);
    setEditTitle(chat.title);
  };

  const handleCancelEdit = () => {
    setEditingChatId(null);
    setEditTitle("");
  };

  const handleSaveEdit = async (chatId, e) => {
    e.stopPropagation();
    
    if (!editTitle.trim()) {
      handleCancelEdit();
      return;
    }

    try {
      const response = await fetch(`${BACKEND_URL}/chats/title`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          chat_id: chatId,
          title: editTitle.trim(),
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        // Update the chat title, maintain sort order
        const updatedChats = chats.map(chat => 
          chat.chat_id === chatId 
            ? { ...chat, title: editTitle.trim() }
            : chat
        );
        setChats(updatedChats);
        handleCancelEdit();
      }
    } catch (error) {
      console.error("Error updating chat title:", error);
    }
  };

  const handleEditKeyDown = (chatId, e) => {
    if (e.key === "Enter") {
      handleSaveEdit(chatId, e);
    } else if (e.key === "Escape") {
      handleCancelEdit();
    }
  };

  const handleGenerateReport = async (chatId, e) => {
    e.stopPropagation();
    
    // Store button reference before async operations
    const button = e.currentTarget;
    
    try {
      // Show loading state
      setGeneratingReport(chatId);
      button.disabled = true;
      button.style.opacity = '0.5';
      
      // Fetch the PDF report
      const response = await fetch(`${BACKEND_URL}/chats/${chatId}/report`);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Server response:', errorText);
        throw new Error(`Failed to generate report: ${response.status} ${response.statusText}`);
      }
      
      // Get the blob from the response
      const blob = await response.blob();
      
      // Create a download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      
      // Extract filename from Content-Disposition header if available
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = 'pentest_report.pdf';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+?)"?$/i);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }
      
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      
      // Cleanup
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      // Re-enable button
      setGeneratingReport(null);
      button.disabled = false;
      button.style.opacity = '1';
    } catch (error) {
      console.error('Error generating report:', error);
      alert('Failed to generate report. Please make sure the backend server is running and try again.');
      
      // Re-enable button using stored reference
      setGeneratingReport(null);
      if (button) {
        button.disabled = false;
        button.style.opacity = '1';
      }
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return "Unknown";
    
    // Handle MongoDB date objects and ISO strings
    let date;
    if (dateString.$date) {
      // MongoDB extended JSON format
      date = new Date(dateString.$date);
    } else if (typeof dateString === 'object' && dateString.getTime) {
      // Already a Date object
      date = dateString;
    } else {
      // ISO string or other format
      date = new Date(dateString);
    }
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
      return "Invalid date";
    }
    
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined 
    });
  };

  const truncateText = (text, maxLength = 50) => {
    if (!text) return "No messages yet";
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + "...";
  };

  const handleSignOut = () => {
    // Clear any stored session data
    localStorage.removeItem("username");
    // Redirect to login page
    router.push("/login");
  };

  if (loading) {
    return (
      <div className={styles.sidebar} style={{ width: `${width}px` }}>
        <div className={styles.header}>
          <h2>Chats</h2>
          <button className={styles.newChatBtn} onClick={handleNewChat}>
            <span>+</span>
          </button>
        </div>
        <div className={styles.loading}>Loading chats...</div>
      </div>
    );
  }

  return (
    <div className={styles.sidebar} style={{ width: `${width}px` }}>
      <div className={styles.header}>
        <h2>Chats</h2>
        <button className={styles.newChatBtn} onClick={handleNewChat} title="New Chat">
          <span>+</span>
        </button>
      </div>

      <div className={styles.chatList}>
        {chats.length === 0 ? (
          <div className={styles.emptyState}>
            <p>No chats yet</p>
            <button className={styles.createFirstChat} onClick={handleNewChat}>
              Create your first chat
            </button>
          </div>
        ) : (
          chats.map((chat) => (
            <div
              key={chat.chat_id}
              className={`${styles.chatItem} ${
                chat.chat_id === currentChatId ? styles.active : ""
              }`}
              onClick={() => onChatSelect(chat.chat_id)}
            >
              <div className={styles.chatInfo}>
                {editingChatId === chat.chat_id ? (
                  <input
                    type="text"
                    className={styles.chatTitleInput}
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    onKeyDown={(e) => handleEditKeyDown(chat.chat_id, e)}
                    onBlur={(e) => handleSaveEdit(chat.chat_id, e)}
                    onClick={(e) => e.stopPropagation()}
                    autoFocus
                  />
                ) : (
                  <div className={styles.chatTitle}>{chat.title}</div>
                )}
                <div className={styles.chatPreview}>
                  {truncateText(chat.last_message)}
                </div>
                <div className={styles.chatDate}>
                  {formatDate(chat.created_at)}
                </div>
              </div>
              <div className={styles.chatActions}>
                <button
                  className={styles.reportBtn}
                  onClick={(e) => handleGenerateReport(chat.chat_id, e)}
                  title="Generate pentesting report"
                  disabled={generatingReport === chat.chat_id}
                >
                  {generatingReport === chat.chat_id ? (
                    <span className={styles.spinner}>⏳</span>
                  ) : (
                    "📄"
                  )}
                </button>
                <button
                  className={styles.editBtn}
                  onClick={(e) => handleStartEdit(chat, e)}
                  title="Rename chat"
                >
                  ✎
                </button>
                <button
                  className={styles.deleteBtn}
                  onClick={(e) => handleDeleteChat(chat.chat_id, e)}
                  title="Delete chat"
                >
                  ×
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      <div className={styles.footer}>
        <div className={styles.userInfo}>
          <div className={styles.userAvatar}>
            <img src="/aranea_pfp.png" alt="Profile" />
          </div>
          <div className={styles.username}>{username}</div>
        </div>
        <button className={styles.signoutBtn} onClick={handleSignOut} title="Sign Out">
          <span>⏻</span>
        </button>
      </div>
      
      <div 
        className={styles.resizeHandle}
        onMouseDown={handleResizeStart}
      />
    </div>
  );
}

import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import ChatInterface from "../components/ChatInterface";
import ChatSidebar from "../components/ChatSidebar";

export default function Chat() {
  const [username, setUsername] = useState("");
  const [currentChatId, setCurrentChatId] = useState(null);
  const [sidebarWidth, setSidebarWidth] = useState(280);
  const router = useRouter();

  useEffect(() => {
    const currentUser = localStorage.getItem("currentUser");
    if (!currentUser) {
      router.push("/login");
    } else {
      setUsername(currentUser);
      // Try to load the last active chat from localStorage
      const lastChatId = localStorage.getItem(`lastChatId_${currentUser}`);
      if (lastChatId) {
        setCurrentChatId(lastChatId);
      }
      // Load saved sidebar width
      const savedWidth = localStorage.getItem("sidebarWidth");
      if (savedWidth) {
        setSidebarWidth(parseInt(savedWidth, 10));
      }
    }
  }, [router]);

  const handleChatSelect = (chatId) => {
    setCurrentChatId(chatId);
    // Remember the last active chat
    if (username) {
      localStorage.setItem(`lastChatId_${username}`, chatId);
    }
  };

  const handleNewChat = (chatId) => {
    setCurrentChatId(chatId);
    // Remember the last active chat
    if (username) {
      localStorage.setItem(`lastChatId_${username}`, chatId);
    }
  };

  const handleSidebarResize = (newWidth) => {
    setSidebarWidth(newWidth);
    localStorage.setItem("sidebarWidth", newWidth.toString());
  };

  if (!username) return null;

  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden" }}>
      <ChatSidebar
        username={username}
        currentChatId={currentChatId}
        onChatSelect={handleChatSelect}
        onNewChat={handleNewChat}
        width={sidebarWidth}
        onResize={handleSidebarResize}
      />
      <ChatInterface username={username} chatId={currentChatId} />
    </div>
  );
}

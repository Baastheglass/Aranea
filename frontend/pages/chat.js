import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import ChatInterface from "../components/ChatInterface";

export default function Chat() {
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

  if (!username) return null;

  return <ChatInterface username={username} />;
}

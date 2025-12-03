import { useState } from "react";
import LoadingScreen from "@/components/LoadingScreen";
import ChatInterface from "@/components/ChatInterface";

export default function Home() {
  const [loadingComplete, setLoadingComplete] = useState(false);

  return (
    <div className="app-root">
      {!loadingComplete ? (
        <LoadingScreen onComplete={() => setLoadingComplete(true)} />
      ) : (
        <ChatInterface />
      )}
    </div>
  );
}



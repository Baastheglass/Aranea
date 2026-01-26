import { useEffect } from "react";
import { useRouter } from "next/router";
import LoadingScreen from "@/components/LoadingScreen";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const currentUser = localStorage.getItem("currentUser");
    if (currentUser) {
      router.push("/home");
    } else {
      router.push("/login");
    }
  }, [router]);

  const handleLoadingComplete = () => {
    console.log("Loading complete");
  };

  return (
    <div className="app-root">
      <LoadingScreen onComplete={handleLoadingComplete} />
    </div>
  );
}



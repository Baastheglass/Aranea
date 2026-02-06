import { useRouter } from "next/router";
import LoadingScreen from "../components/LoadingScreen";

export default function Loading() {
  const router = useRouter();

  const handleLoadingComplete = () => {
    router.push("/chat");
  };

  return <LoadingScreen onComplete={handleLoadingComplete} />;
}

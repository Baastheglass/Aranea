import AuthForm from "../components/AuthForm";
import { useEffect } from "react";
import { useRouter } from "next/router";

export default function Signup() {
  const router = useRouter();

  useEffect(() => {
    // Redirect if already logged in
    const currentUser = localStorage.getItem("currentUser");
    if (currentUser) {
      router.push("/home");
    }
  }, [router]);

  return <AuthForm mode="signup" />;
}

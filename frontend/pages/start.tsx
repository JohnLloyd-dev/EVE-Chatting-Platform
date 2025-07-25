import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Head from "next/head";

export default function StartChat() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initializeChat = async () => {
      try {
        // Get URL parameters from Tally redirect
        const urlParams = new URLSearchParams(window.location.search);
        const responseId =
          urlParams.get("responseId") || urlParams.get("response_id");
        const respondentId =
          urlParams.get("respondentId") || urlParams.get("respondent_id");

        if (!responseId && !respondentId) {
          setError("No form response found. Please submit the form first.");
          setLoading(false);
          return;
        }

        // Find user by Tally response ID
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/user/by-tally-response`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              response_id: responseId,
              respondent_id: respondentId,
            }),
          }
        );

        if (!response.ok) {
          throw new Error("Failed to find your chat session");
        }

        const userData = await response.json();

        // Redirect to chat with user ID
        router.push(`/chat/${userData.user_id}`);
      } catch (err) {
        console.error("Error initializing chat:", err);
        setError("Failed to start your chat session. Please try again.");
        setLoading(false);
      }
    };

    initializeChat();
  }, [router]);

  if (loading) {
    return (
      <>
        <Head>
          <title>Starting Your Chat Session...</title>
        </Head>
        <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-white mx-auto mb-4"></div>
            <h1 className="text-2xl font-bold text-white mb-2">
              Starting Your Chat Session...
            </h1>
            <p className="text-gray-300">
              Please wait while we prepare your personalized experience
            </p>
          </div>
        </div>
      </>
    );
  }

  if (error) {
    return (
      <>
        <Head>
          <title>Chat Session Error</title>
        </Head>
        <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
          <div className="text-center max-w-md mx-auto p-6">
            <div className="text-red-400 text-6xl mb-4">⚠️</div>
            <h1 className="text-2xl font-bold text-white mb-4">
              Oops! Something went wrong
            </h1>
            <p className="text-gray-300 mb-6">{error}</p>
            <button
              onClick={() => (window.location.href = "/")}
              className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded transition duration-200"
            >
              Go Back to Home
            </button>
          </div>
        </div>
      </>
    );
  }

  return null;
}

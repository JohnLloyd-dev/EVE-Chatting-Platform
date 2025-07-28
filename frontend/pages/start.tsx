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

        // Debug: Log all URL parameters
        console.log("All URL parameters:", Object.fromEntries(urlParams));
        console.log("responseId:", responseId);
        console.log("respondentId:", respondentId);

        // Check if we have valid IDs (not placeholder text)
        const hasValidResponseId =
          responseId &&
          !responseId.includes("@") &&
          responseId !== "Respondent ID";
        const hasValidRespondentId =
          respondentId &&
          !respondentId.includes("@") &&
          respondentId !== "Respondent ID";

        if (!hasValidResponseId && !hasValidRespondentId) {
          setError(
            "Invalid form response parameters. Please submit the form again with a valid redirect URL."
          );
          setLoading(false);
          return;
        }

        // Find user by Tally response ID
        // Note: Sometimes Tally sends respondent_id as responseId parameter
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/user/by-tally-response`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              response_id: hasValidResponseId ? responseId : null,
              respondent_id: hasValidRespondentId
                ? respondentId
                : hasValidResponseId
                ? responseId
                : null,
            }),
          }
        );

        if (!response.ok) {
          const errorData = await response
            .json()
            .catch(() => ({ detail: "Unknown error" }));

          // Handle specific error cases
          if (response.status === 404) {
            throw new Error(
              "We couldn't find your chat session. Please make sure you submitted the form first and try clicking the link from your email again."
            );
          } else if (response.status === 403) {
            throw new Error(
              "Your account has been blocked. Please contact support if you believe this is an error."
            );
          } else {
            throw new Error(
              errorData.detail || "Failed to find your chat session"
            );
          }
        }

        const userData = await response.json();

        // Redirect to chat with user ID
        router.push(`/chat/${userData.user_id}`);
      } catch (err) {
        console.error("Error initializing chat:", err);
        setError(
          err instanceof Error
            ? err.message
            : "Failed to start your chat session. Please try again."
        );
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
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-800 flex items-center justify-center animate-gradient-x">
          <div className="text-center animate-fade-in">
            <div className="relative mb-8">
              {/* Outer spinning ring */}
              <div className="animate-spin rounded-full h-20 w-20 border-4 border-purple-500/30 border-t-purple-500 mx-auto"></div>
              {/* Inner pulsing dot */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full animate-pulse"></div>
              </div>
            </div>

            <div className="space-y-4 animate-slide-up">
              <h1 className="text-3xl font-bold text-white mb-2 animate-pulse">
                Starting Your Chat Session...
              </h1>
              <p className="text-gray-300 text-lg">
                Please wait while we prepare your personalized experience
              </p>

              {/* Progress dots */}
              <div className="flex justify-center space-x-2 mt-6">
                <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce"></div>
                <div
                  className="w-2 h-2 bg-purple-500 rounded-full animate-bounce"
                  style={{ animationDelay: "0.1s" }}
                ></div>
                <div
                  className="w-2 h-2 bg-purple-500 rounded-full animate-bounce"
                  style={{ animationDelay: "0.2s" }}
                ></div>
              </div>
            </div>
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
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-800 flex items-center justify-center animate-gradient-x">
          <div className="text-center max-w-md mx-auto p-8 bg-gray-800/80 backdrop-blur-sm rounded-xl shadow-2xl border border-gray-700/50 animate-fade-in">
            <div className="text-red-400 text-6xl mb-6 animate-bounce">⚠️</div>
            <h1 className="text-3xl font-bold text-white mb-4 animate-slide-up">
              Oops! Something went wrong
            </h1>
            <p className="text-gray-300 mb-8 text-lg animate-slide-up-delay">
              {error}
            </p>
            <div className="space-y-4">
              {error.includes("submitted the form first") && (
                <a
                  href="https://tally.so/r/mYPJPz"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 transform hover:scale-105 animate-slide-up-delay-2"
                >
                  Submit the Form First
                </a>
              )}
              <button
                onClick={() => window.location.reload()}
                className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 transform hover:scale-105 animate-slide-up-delay-2 mr-4"
              >
                Try Again
              </button>
              <button
                onClick={() => (window.location.href = "/")}
                className="bg-gradient-to-r from-gray-600 to-gray-700 hover:from-gray-700 hover:to-gray-800 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 transform hover:scale-105 animate-slide-up-delay-2"
              >
                Go Back to Home
              </button>
            </div>
          </div>
        </div>
      </>
    );
  }

  return null;
}

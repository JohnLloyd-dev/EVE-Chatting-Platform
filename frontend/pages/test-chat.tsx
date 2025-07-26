import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Head from "next/head";
import { getOrCreateDeviceId } from "../lib/deviceId";

export default function TestChat() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initializeTestChat = async () => {
      try {
        // Get URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const encodedPrompt = urlParams.get("prompt");
        const deviceParam = urlParams.get("device");

        if (!encodedPrompt) {
          setError("No prompt provided in the URL");
          setLoading(false);
          return;
        }

        // Decode the prompt
        const customPrompt = decodeURIComponent(encodedPrompt);

        // Get or generate device ID
        let deviceId = deviceParam;
        if (!deviceId) {
          deviceId = getOrCreateDeviceId();
        }

        console.log("Creating device session with:", {
          deviceId,
          promptLength: customPrompt.length,
        });

        // Create device-based session
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/user/device-session`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              device_id: deviceId,
              custom_prompt: customPrompt,
            }),
          }
        );

        if (!response.ok) {
          const errorData = await response
            .json()
            .catch(() => ({ detail: "Unknown error" }));
          throw new Error(
            errorData.detail || "Failed to create test chat session"
          );
        }

        const sessionData = await response.json();
        console.log("Session created:", sessionData);

        // Redirect to chat with user ID
        router.push(`/chat/${sessionData.user_id}`);
      } catch (err) {
        console.error("Error initializing test chat:", err);
        setError(
          err instanceof Error
            ? err.message
            : "Failed to start your test chat session. Please try again."
        );
        setLoading(false);
      }
    };

    // Only run if we have the router query
    if (router.isReady) {
      initializeTestChat();
    }
  }, [router.isReady, router]);

  if (loading) {
    return (
      <>
        <Head>
          <title>Starting Test Chat Session...</title>
        </Head>
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-800 flex items-center justify-center animate-gradient-x">
          <div className="text-center animate-fade-in">
            <div className="relative mb-8">
              {/* Outer spinning ring */}
              <div className="animate-spin rounded-full h-20 w-20 border-4 border-green-500/30 border-t-green-500 mx-auto"></div>
              {/* Inner pulsing dot */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-8 h-8 bg-gradient-to-r from-green-500 to-blue-500 rounded-full animate-pulse"></div>
              </div>
            </div>

            <div className="space-y-4 animate-slide-up">
              <h1 className="text-3xl font-bold text-white mb-2 animate-pulse">
                Starting Test Chat Session...
              </h1>
              <p className="text-gray-300 text-lg">
                Setting up your custom AI character
              </p>

              {/* Progress dots */}
              <div className="flex justify-center space-x-2 mt-6">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce"></div>
                <div
                  className="w-2 h-2 bg-green-500 rounded-full animate-bounce"
                  style={{ animationDelay: "0.1s" }}
                ></div>
                <div
                  className="w-2 h-2 bg-green-500 rounded-full animate-bounce"
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
          <title>Test Chat Error</title>
        </Head>
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-800 flex items-center justify-center animate-gradient-x">
          <div className="text-center max-w-md mx-auto p-8 bg-gray-800/80 backdrop-blur-sm rounded-xl shadow-2xl border border-gray-700/50 animate-fade-in">
            <div className="text-red-400 text-6xl mb-6 animate-bounce">⚠️</div>
            <h1 className="text-3xl font-bold text-white mb-4 animate-slide-up">
              Test Chat Error
            </h1>
            <p className="text-gray-300 mb-8 text-lg animate-slide-up-delay">
              {error}
            </p>
            <div className="flex gap-3 justify-center">
              <button
                onClick={() => router.push("/test-generator")}
                className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 transform hover:scale-105 animate-slide-up-delay-2"
              >
                Generate New Link
              </button>
              <button
                onClick={() => (window.location.href = "/")}
                className="bg-gradient-to-r from-gray-600 to-gray-700 hover:from-gray-700 hover:to-gray-800 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 transform hover:scale-105 animate-slide-up-delay-2"
              >
                Go Home
              </button>
            </div>
          </div>
        </div>
      </>
    );
  }

  return null;
}

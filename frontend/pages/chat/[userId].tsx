import { useRouter } from "next/router";
import { useState, useEffect } from "react";
import { useQuery } from "react-query";
import ChatInterface from "../../components/ChatInterface";
import ErrorBoundary from "../../components/ErrorBoundary";
import Link from "next/link";
import { userSession } from "../../lib/userSession";
import { chatApi } from "../../lib/api";
import { ChatSession } from "../../types";

export default function ChatPage() {
  const router = useRouter();
  const { userId } = router.query;

  // Get chat session to display user_code
  const { data: session } = useQuery<ChatSession>(
    ["chatSession", userId],
    () => chatApi.getSession(userId as string),
    {
      enabled: !!userId && typeof userId === "string",
    }
  );

  useEffect(() => {
    // Validate session when page loads
    if (userId && typeof userId === "string") {
      const userSessionData = userSession.get();
      if (!userSessionData || userSessionData.userId !== userId) {
        // Session doesn't match, save current user
        userSession.save(userId, "tally");
      }
    }
  }, [userId]);

  const handleLogout = () => {
    userSession.clear();
    router.push("/");
  };

  if (!userId || typeof userId !== "string") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-800 flex items-center justify-center animate-gradient-x">
        <div className="text-center p-8 bg-gray-800/80 backdrop-blur-sm rounded-xl shadow-2xl border border-gray-700/50 animate-fade-in">
          <div className="text-red-400 text-6xl mb-4">⚠️</div>
          <div className="text-gray-300 mb-6 text-lg">Invalid user ID</div>
          <Link
            href="/"
            className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 transform hover:scale-105"
          >
            Go Home
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-800 animate-gradient-x">
      {/* Header */}
      <div className="bg-gray-800/80 backdrop-blur-sm shadow-2xl border-b border-gray-700/50">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="animate-fade-in">
              <h1 className="text-xl font-semibold text-white">Chat Session</h1>
              <p className="text-sm text-gray-300">
                User ID: {session?.user_code || userId}
              </p>
            </div>
            <button
              onClick={handleLogout}
              className="bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white font-medium py-2 px-4 rounded-lg transition-all duration-300 transform hover:scale-105 animate-fade-in-delay"
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Chat Interface */}
      <div className="max-w-4xl mx-auto animate-slide-up">
        <div
          className="bg-gray-800/60 backdrop-blur-sm shadow-2xl border-x border-gray-700/50"
          style={{ height: "calc(100vh - 120px)" }}
        >
          <ErrorBoundary>
            <ChatInterface userId={userId} />
          </ErrorBoundary>
        </div>
      </div>
    </div>
  );
}

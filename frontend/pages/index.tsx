import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import Link from "next/link";
import { userSession } from "../lib/userSession";

export default function Home() {
  const router = useRouter();
  const [userId, setUserId] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    // Check if user already has a valid session
    const existingSession = userSession.get();
    if (existingSession) {
      // User already logged in, redirect to chat
      const chatPath = `/chat/${existingSession.userId}`;
      if (router.pathname !== chatPath) {
        router.push(chatPath);
      } else {
        setIsLoading(false);
      }
      return;
    }

    // Check if user ID is in URL params (from Tally redirect)
    const { user_id } = router.query;
    if (user_id && typeof user_id === "string") {
      // Save user session and redirect to chat immediately
      userSession.save(user_id, "tally");
      const chatPath = `/chat/${user_id}`;
      if (router.pathname !== chatPath) {
        router.push(chatPath);
      } else {
        setIsLoading(false);
      }
      return;
    }

    // No session and no URL params, show login form
    setIsLoading(false);
  }, [router.query, router.pathname]);

  const handleStartChat = () => {
    if (userId.trim()) {
      // Save session for manual login and redirect
      userSession.save(userId.trim(), "tally");
      const chatPath = `/chat/${userId.trim()}`;
      if (router.pathname !== chatPath) {
        router.push(chatPath);
      }
    }
  };

  // Show loading spinner while checking session
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-800 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center animate-spin">
            <span className="text-2xl">💬</span>
          </div>
          <p className="text-white mt-4">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-800 animate-gradient-x">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-md mx-auto bg-gray-800/80 backdrop-blur-sm rounded-xl shadow-2xl p-8 border border-gray-700/50 transform transition-all duration-500 hover:scale-105">
          <div className="text-center mb-8">
            <div className="mb-4">
              <div className="w-16 h-16 mx-auto bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center animate-pulse">
                <span className="text-2xl">💬</span>
              </div>
            </div>
            <h1 className="text-3xl font-bold text-white mb-2 animate-fade-in">
              Welcome to Your Chat
            </h1>
            <p className="text-gray-300 animate-fade-in-delay">
              Enter your user ID to start chatting
            </p>
          </div>

          <div className="space-y-4">
            <div className="animate-slide-up">
              <label
                htmlFor="userId"
                className="block text-sm font-medium text-gray-300 mb-2"
              >
                User ID
              </label>
              <input
                type="text"
                id="userId"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                placeholder="Enter your user ID"
                className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent text-white placeholder-gray-400 transition-all duration-200"
              />
            </div>

            <button
              onClick={handleStartChat}
              disabled={!userId.trim()}
              className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 animate-slide-up-delay"
            >
              Start Chat
            </button>
          </div>

          <div className="mt-8 pt-6 border-t border-gray-700/50">
            <div className="text-center space-y-2 animate-fade-in-delay-2">
              <div>
                <Link
                  href="/admin"
                  className="text-purple-400 hover:text-purple-300 text-sm transition-colors duration-200"
                >
                  Admin Dashboard
                </Link>
              </div>
              <div>
                <Link
                  href="/test-generator"
                  className="text-green-400 hover:text-green-300 text-sm transition-colors duration-200"
                >
                  Test Link Generator
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

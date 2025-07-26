import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import Link from "next/link";

export default function Home() {
  const router = useRouter();
  const [userId, setUserId] = useState<string>("");

  useEffect(() => {
    // Check if user ID is in URL params (from Tally redirect)
    const { user_id } = router.query;
    if (user_id && typeof user_id === "string") {
      setUserId(user_id);
    }
  }, [router.query]);

  const handleStartChat = () => {
    if (userId.trim()) {
      router.push(`/chat/${userId.trim()}`);
    }
  };

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
            <div className="text-center animate-fade-in-delay-2">
              <Link
                href="/admin"
                className="text-purple-400 hover:text-purple-300 text-sm transition-colors duration-200"
              >
                Admin Dashboard
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

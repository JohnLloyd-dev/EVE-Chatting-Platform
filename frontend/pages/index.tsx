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
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-gray-100">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-md mx-auto bg-white rounded-lg shadow-lg p-8">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Welcome to Your Chat
            </h1>
            <p className="text-gray-600">
              Enter your user ID to start chatting
            </p>
          </div>

          <div className="space-y-4">
            <div>
              <label
                htmlFor="userId"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                User ID
              </label>
              <input
                type="text"
                id="userId"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                placeholder="Enter your user ID"
                className="input-field"
              />
            </div>

            <button
              onClick={handleStartChat}
              disabled={!userId.trim()}
              className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Start Chat
            </button>
          </div>

          <div className="mt-8 pt-6 border-t border-gray-200">
            <div className="text-center">
              <Link
                href="/admin"
                className="text-primary-600 hover:text-primary-700 text-sm"
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

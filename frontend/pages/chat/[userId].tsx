import { useRouter } from "next/router";
import { useState } from "react";
import ChatInterface from "../../components/ChatInterface";
import Link from "next/link";

export default function ChatPage() {
  const router = useRouter();
  const { userId } = router.query;

  if (!userId || typeof userId !== "string") {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-gray-600 mb-4">Invalid user ID</div>
          <Link href="/" className="btn-primary">
            Go Home
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold text-gray-900">
                Chat Session
              </h1>
              <p className="text-sm text-gray-600">User ID: {userId}</p>
            </div>
            <Link href="/" className="btn-secondary">
              Exit Chat
            </Link>
          </div>
        </div>
      </div>

      {/* Chat Interface */}
      <div className="max-w-4xl mx-auto">
        <div
          className="bg-white shadow-sm"
          style={{ height: "calc(100vh - 120px)" }}
        >
          <ChatInterface userId={userId} />
        </div>
      </div>
    </div>
  );
}

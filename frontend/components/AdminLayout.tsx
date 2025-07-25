import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useQuery } from "react-query";
import { adminApi } from "../lib/api";

interface AdminLayoutProps {
  children: React.ReactNode;
}

export default function AdminLayout({ children }: AdminLayoutProps) {
  const router = useRouter();
  const [adminUser, setAdminUser] = useState<any>(null);

  useEffect(() => {
    const token = localStorage.getItem("admin_token");
    const user = localStorage.getItem("admin_user");

    if (!token || !user) {
      router.push("/admin");
      return;
    }

    setAdminUser(JSON.parse(user));
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("admin_token");
    localStorage.removeItem("admin_user");
    router.push("/admin");
  };

  if (!adminUser) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-8">
              <h1 className="text-xl font-semibold text-gray-900">
                Admin Dashboard
              </h1>
              <nav className="flex space-x-4">
                <Link
                  href="/admin/dashboard"
                  className={`px-3 py-2 rounded-md text-sm font-medium ${
                    router.pathname === "/admin/dashboard"
                      ? "bg-primary-100 text-primary-700"
                      : "text-gray-600 hover:text-gray-900"
                  }`}
                >
                  Overview
                </Link>
                <Link
                  href="/admin/conversations"
                  className={`px-3 py-2 rounded-md text-sm font-medium ${
                    router.pathname === "/admin/conversations"
                      ? "bg-primary-100 text-primary-700"
                      : "text-gray-600 hover:text-gray-900"
                  }`}
                >
                  Conversations
                </Link>
              </nav>
            </div>

            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                Welcome, {adminUser.username}
              </span>
              <button onClick={handleLogout} className="btn-secondary text-sm">
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
}

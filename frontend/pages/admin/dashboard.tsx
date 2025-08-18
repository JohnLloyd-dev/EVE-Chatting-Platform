import { useQuery } from "react-query";
import { adminApi } from "../../lib/api";
import AdminLayout from "../../components/AdminLayout";
import { DashboardStats } from "../../types";

export default function AdminDashboard() {
  const {
    data: stats,
    isLoading,
    error,
  } = useQuery<DashboardStats>("dashboardStats", adminApi.getStats, {
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  if (isLoading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </AdminLayout>
    );
  }

  if (error) {
    return (
      <AdminLayout>
        <div className="text-center py-8">
          <div className="text-red-600 mb-4">
            Failed to load dashboard stats
          </div>
          <button
            onClick={() => window.location.reload()}
            className="btn-primary"
          >
            Retry
          </button>
        </div>
      </AdminLayout>
    );
  }

  const statCards = [
    {
      title: "Total Users",
      value: stats?.total_users || 0,
      icon: "👥",
      color: "bg-blue-500",
    },
    {
      title: "Active Sessions",
      value: stats?.active_sessions || 0,
      icon: "💬",
      color: "bg-green-500",
    },
    {
      title: "Total Messages",
      value: stats?.total_messages || 0,
      icon: "📝",
      color: "bg-purple-500",
    },
    {
      title: "Blocked Users",
      value: stats?.blocked_users || 0,
      icon: "🚫",
      color: "bg-red-500",
    },
    {
      title: "Messages Today",
      value: stats?.messages_today || 0,
      icon: "📊",
      color: "bg-yellow-500",
    },
    {
      title: "New Users Today",
      value: stats?.new_users_today || 0,
      icon: "✨",
      color: "bg-indigo-500",
    },
  ];

  return (
    <AdminLayout>
      <div className="space-y-8">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            Dashboard Overview
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {statCards.map((card, index) => (
              <div
                key={index}
                className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
              >
                <div className="flex items-center">
                  <div
                    className={`${card.color} rounded-lg p-3 text-white text-2xl mr-4`}
                  >
                    {card.icon}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-600">
                      {card.title}
                    </p>
                    <p className="text-3xl font-bold text-gray-900">
                      {card.value}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Quick Actions
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <a
              href="/admin/conversations"
              className="block p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center">
                <div className="text-2xl mr-3">💬</div>
                <div>
                  <h4 className="font-medium text-gray-900">
                    View Conversations
                  </h4>
                  <p className="text-sm text-gray-600">
                    Monitor and manage user chats
                  </p>
                </div>
              </div>
            </a>

            <a
              href="/admin/users"
              className="block p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center">
                <div className="text-2xl mr-3">👥</div>
                <div>
                  <h4 className="font-medium text-gray-900">User Management</h4>
                  <p className="text-sm text-gray-600">
                    View, block, and manage users
                  </p>
                </div>
              </div>
            </a>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            System Status
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Chat System</span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                ✓ Online
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Response System</span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                ✓ Active
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Database</span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                ✓ Connected
              </span>
            </div>
          </div>
        </div>

        {/* System monitoring - no AI references for users */}
      </div>
    </AdminLayout>
  );
}

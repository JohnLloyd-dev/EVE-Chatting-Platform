import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "react-query";
import { adminApi } from "../../lib/api";
import AdminLayout from "../../components/AdminLayout";
import UserDetailsModal from "../../components/UserDetailsModal";
import { UserWithStats, UsersResponse } from "../../types";
import { format } from "date-fns";
import toast from "react-hot-toast";

export default function AdminUsers() {
  const [currentPage, setCurrentPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState("");
  const [userTypeFilter, setUserTypeFilter] = useState<string>("");
  const [blockedFilter, setBlockedFilter] = useState<string>("");
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(
    null
  );

  const pageSize = 20;
  const queryClient = useQueryClient();

  // Fetch users
  const {
    data: usersData,
    isLoading,
    error,
  } = useQuery<UsersResponse>(
    ["users", currentPage, searchTerm, userTypeFilter, blockedFilter],
    () =>
      adminApi.getUsers({
        skip: (currentPage - 1) * pageSize,
        limit: pageSize,
        search: searchTerm || undefined,
        user_type: userTypeFilter || undefined,
        is_blocked:
          blockedFilter === "true"
            ? true
            : blockedFilter === "false"
            ? false
            : undefined,
      }),
    {
      keepPreviousData: true,
      refetchInterval: 30000,
    }
  );

  // Block/Unblock user mutation
  const blockUserMutation = useMutation(
    ({ userId, isBlocked }: { userId: string; isBlocked: boolean }) =>
      adminApi.toggleUserBlock(userId, isBlocked),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries("users");
        toast.success(data.message);
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || "Failed to update user");
      },
    }
  );

  // Delete user mutation
  const deleteUserMutation = useMutation(
    (userId: string) => adminApi.deleteUser(userId),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries("users");
        toast.success(data.message);
        setShowDeleteConfirm(null);
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || "Failed to delete user");
      },
    }
  );

  const handleBlockUser = (user: UserWithStats) => {
    blockUserMutation.mutate({
      userId: user.id,
      isBlocked: !user.is_blocked,
    });
  };

  const handleDeleteUser = (userId: string) => {
    deleteUserMutation.mutate(userId);
  };

  const totalPages = Math.ceil((usersData?.total || 0) / pageSize);

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
          <div className="text-red-600 mb-4">Failed to load users</div>
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

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-900">User Management</h2>
          <div className="text-sm text-gray-600">
            Total: {usersData?.total || 0} users
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Search
              </label>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setCurrentPage(1);
                }}
                placeholder="Search by ID, email, or response ID..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                User Type
              </label>
              <select
                value={userTypeFilter}
                onChange={(e) => {
                  setUserTypeFilter(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Types</option>
                <option value="tally">Tally</option>
                <option value="device">Device</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                value={blockedFilter}
                onChange={(e) => {
                  setBlockedFilter(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Users</option>
                <option value="false">Active</option>
                <option value="true">Blocked</option>
              </select>
            </div>

            <div className="flex items-end">
              <button
                onClick={() => {
                  setSearchTerm("");
                  setUserTypeFilter("");
                  setBlockedFilter("");
                  setCurrentPage(1);
                }}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Clear Filters
              </button>
            </div>
          </div>
        </div>

        {/* Users Table */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Activity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {usersData?.users.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {user.id}
                        </div>
                        {user.email && (
                          <div className="text-sm text-gray-500">
                            {user.email}
                          </div>
                        )}
                        {user.tally_response_id && (
                          <div className="text-xs text-gray-400">
                            Tally: {user.tally_response_id.substring(0, 8)}...
                          </div>
                        )}
                        {user.device_id && (
                          <div className="text-xs text-gray-400">
                            Device: {user.device_id}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          user.user_type === "tally"
                            ? "bg-blue-100 text-blue-800"
                            : "bg-green-100 text-green-800"
                        }`}
                      >
                        {user.user_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div>
                        <div>{user.session_count} sessions</div>
                        <div className="text-gray-500">
                          {user.message_count} messages
                        </div>
                        {user.last_session_at && (
                          <div className="text-xs text-gray-400">
                            Last:{" "}
                            {format(
                              new Date(user.last_session_at),
                              "MMM d, HH:mm"
                            )}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          user.is_blocked
                            ? "bg-red-100 text-red-800"
                            : "bg-green-100 text-green-800"
                        }`}
                      >
                        {user.is_blocked ? "Blocked" : "Active"}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {format(new Date(user.created_at), "MMM d, yyyy")}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                      <button
                        onClick={() => setSelectedUserId(user.id)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        View
                      </button>
                      <button
                        onClick={() => handleBlockUser(user)}
                        disabled={blockUserMutation.isLoading}
                        className={`${
                          user.is_blocked
                            ? "text-green-600 hover:text-green-900"
                            : "text-yellow-600 hover:text-yellow-900"
                        }`}
                      >
                        {user.is_blocked ? "Unblock" : "Block"}
                      </button>
                      <button
                        onClick={() => setShowDeleteConfirm(user.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200">
              <div className="flex-1 flex justify-between sm:hidden">
                <button
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() =>
                    setCurrentPage(Math.min(totalPages, currentPage + 1))
                  }
                  disabled={currentPage === totalPages}
                  className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  Next
                </button>
              </div>
              <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm text-gray-700">
                    Showing{" "}
                    <span className="font-medium">
                      {(currentPage - 1) * pageSize + 1}
                    </span>{" "}
                    to{" "}
                    <span className="font-medium">
                      {Math.min(currentPage * pageSize, usersData?.total || 0)}
                    </span>{" "}
                    of{" "}
                    <span className="font-medium">{usersData?.total || 0}</span>{" "}
                    results
                  </p>
                </div>
                <div>
                  <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                    <button
                      onClick={() =>
                        setCurrentPage(Math.max(1, currentPage - 1))
                      }
                      disabled={currentPage === 1}
                      className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                    >
                      Previous
                    </button>
                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                      const page = i + 1;
                      return (
                        <button
                          key={page}
                          onClick={() => setCurrentPage(page)}
                          className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                            currentPage === page
                              ? "z-10 bg-blue-50 border-blue-500 text-blue-600"
                              : "bg-white border-gray-300 text-gray-500 hover:bg-gray-50"
                          }`}
                        >
                          {page}
                        </button>
                      );
                    })}
                    <button
                      onClick={() =>
                        setCurrentPage(Math.min(totalPages, currentPage + 1))
                      }
                      disabled={currentPage === totalPages}
                      className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                    >
                      Next
                    </button>
                  </nav>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Delete Confirmation Modal */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3 text-center">
                <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                  <svg
                    className="h-6 w-6 text-red-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
                    />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mt-2">
                  Delete User
                </h3>
                <div className="mt-2 px-7 py-3">
                  <p className="text-sm text-gray-500">
                    Are you sure you want to delete this user? This action will
                    permanently remove the user and all associated data
                    including sessions and messages. This action cannot be
                    undone.
                  </p>
                </div>
                <div className="items-center px-4 py-3">
                  <button
                    onClick={() => handleDeleteUser(showDeleteConfirm)}
                    disabled={deleteUserMutation.isLoading}
                    className="px-4 py-2 bg-red-500 text-white text-base font-medium rounded-md w-24 mr-2 hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-300 disabled:opacity-50"
                  >
                    {deleteUserMutation.isLoading ? "..." : "Delete"}
                  </button>
                  <button
                    onClick={() => setShowDeleteConfirm(null)}
                    className="px-4 py-2 bg-gray-500 text-white text-base font-medium rounded-md w-24 hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-300"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* User Details Modal */}
        {selectedUserId && (
          <UserDetailsModal
            userId={selectedUserId}
            onClose={() => setSelectedUserId(null)}
          />
        )}
      </div>
    </AdminLayout>
  );
}

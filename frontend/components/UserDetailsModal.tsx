import { useQuery } from "react-query";
import { adminApi } from "../lib/api";
import { UserDetails } from "../types";
import { format } from "date-fns";
import { useState } from "react";

interface UserDetailsModalProps {
  userId: string;
  onClose: () => void;
}

interface TallyFormDataSectionProps {
  formData: any;
}

const TallyFormDataSection: React.FC<TallyFormDataSectionProps> = ({
  formData,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between w-full text-left font-medium text-gray-700 hover:text-gray-900 transition-colors"
      >
        <span>Raw Form Data:</span>
        <svg
          className={`w-4 h-4 transition-transform ${
            isExpanded ? "rotate-180" : ""
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>
      {isExpanded && (
        <pre className="mt-2 text-xs bg-white p-3 rounded border overflow-x-auto max-h-64 overflow-y-auto">
          {JSON.stringify(formData, null, 2)}
        </pre>
      )}
    </div>
  );
};

export default function UserDetailsModal({
  userId,
  onClose,
}: UserDetailsModalProps) {
  const {
    data: userDetails,
    isLoading,
    error,
  } = useQuery<UserDetails>(
    ["userDetails", userId],
    () => adminApi.getUserDetails(userId),
    {
      enabled: !!userId,
    }
  );

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
        <div className="relative top-20 mx-auto p-5 border w-4/5 max-w-4xl shadow-lg rounded-md bg-white">
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !userDetails) {
    return (
      <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
        <div className="relative top-20 mx-auto p-5 border w-4/5 max-w-4xl shadow-lg rounded-md bg-white">
          <div className="text-center py-8">
            <div className="text-red-600 mb-4">Failed to load user details</div>
            <button onClick={onClose} className="btn-primary">
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }

  const { user, sessions, recent_messages, tally_submission } = userDetails;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-10 mx-auto p-5 border w-4/5 max-w-6xl shadow-lg rounded-md bg-white mb-10">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-2xl font-bold text-gray-900">User Details</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
          >
            ×
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* User Information */}
          <div className="space-y-6">
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-lg font-semibold text-gray-900 mb-3">
                User Information
              </h4>
              <div className="space-y-2">
                <div>
                  <span className="font-medium text-gray-700">User Code:</span>
                  <span className="ml-2 text-xl font-bold text-blue-600">
                    {user.user_code}
                  </span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">
                    Internal ID:
                  </span>
                  <span className="ml-2 text-gray-900 font-mono text-sm">
                    {user.id}
                  </span>
                </div>
                {user.email && (
                  <div>
                    <span className="font-medium text-gray-700">Email:</span>
                    <span className="ml-2 text-gray-900">{user.email}</span>
                  </div>
                )}
                <div>
                  <span className="font-medium text-gray-700">Type:</span>
                  <span
                    className={`ml-2 inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      user.user_type === "tally"
                        ? "bg-blue-100 text-blue-800"
                        : "bg-green-100 text-green-800"
                    }`}
                  >
                    {user.user_type}
                  </span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Status:</span>
                  <span
                    className={`ml-2 inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      user.is_blocked
                        ? "bg-red-100 text-red-800"
                        : "bg-green-100 text-green-800"
                    }`}
                  >
                    {user.is_blocked ? "Blocked" : "Active"}
                  </span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Created:</span>
                  <span className="ml-2 text-gray-900">
                    {format(new Date(user.created_at), "MMM d, yyyy HH:mm")}
                  </span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">
                    Last Active:
                  </span>
                  <span className="ml-2 text-gray-900">
                    {format(new Date(user.last_active), "MMM d, yyyy HH:mm")}
                  </span>
                </div>
                {user.tally_response_id && (
                  <div>
                    <span className="font-medium text-gray-700">
                      Tally Response ID:
                    </span>
                    <span className="ml-2 text-gray-900 font-mono text-sm">
                      {user.tally_response_id}
                    </span>
                  </div>
                )}
                {user.tally_respondent_id && (
                  <div>
                    <span className="font-medium text-gray-700">
                      Tally Respondent ID:
                    </span>
                    <span className="ml-2 text-gray-900 font-mono text-sm">
                      {user.tally_respondent_id}
                    </span>
                  </div>
                )}
                {user.device_id && (
                  <div>
                    <span className="font-medium text-gray-700">
                      Device ID:
                    </span>
                    <span className="ml-2 text-gray-900 font-mono text-sm">
                      {user.device_id}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Tally Submission */}
            {tally_submission && (
              <div className="bg-blue-50 rounded-lg p-4">
                <h4 className="text-lg font-semibold text-gray-900 mb-3">
                  Tally Submission
                </h4>
                <div className="space-y-2">
                  <div>
                    <span className="font-medium text-gray-700">Form ID:</span>
                    <span className="ml-2 text-gray-900 font-mono text-sm">
                      {tally_submission.form_id}
                    </span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">
                      Submitted:
                    </span>
                    <span className="ml-2 text-gray-900">
                      {format(
                        new Date(tally_submission.submitted_at),
                        "MMM d, yyyy HH:mm"
                      )}
                    </span>
                  </div>
                  {tally_submission.generated_prompt && (
                    <div>
                      <span className="font-medium text-gray-700">
                        Generated Prompt:
                      </span>
                      <div className="mt-2 p-3 bg-green-50 border border-green-200 rounded-lg">
                        <p className="text-sm text-gray-800 leading-relaxed">
                          {tally_submission.generated_prompt}
                        </p>
                      </div>
                    </div>
                  )}
                  {tally_submission.form_data && (
                    <TallyFormDataSection
                      formData={tally_submission.form_data}
                    />
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Sessions and Messages */}
          <div className="space-y-6">
            {/* Sessions */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-lg font-semibold text-gray-900 mb-3">
                Chat Sessions ({sessions.length})
              </h4>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {sessions.length === 0 ? (
                  <p className="text-gray-500 text-sm">No sessions found</p>
                ) : (
                  sessions.map((session) => (
                    <div
                      key={session.id}
                      className="bg-white p-3 rounded border text-sm"
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="font-medium text-gray-900">
                            Session {session.id.substring(0, 8)}...
                          </div>
                          <div className="text-gray-500">
                            {session.message_count} messages
                          </div>
                        </div>
                        <div className="text-right">
                          <div
                            className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              session.is_active
                                ? "bg-green-100 text-green-800"
                                : "bg-gray-100 text-gray-800"
                            }`}
                          >
                            {session.is_active ? "Active" : "Inactive"}
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            {format(
                              new Date(session.updated_at),
                              "MMM d, HH:mm"
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Recent Messages */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-lg font-semibold text-gray-900 mb-3">
                Recent Messages ({recent_messages.length})
              </h4>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {recent_messages.length === 0 ? (
                  <p className="text-gray-500 text-sm">No messages found</p>
                ) : (
                  recent_messages.map((message) => (
                    <div
                      key={message.id}
                      className={`p-3 rounded text-sm ${
                        message.is_from_user
                          ? "bg-blue-100 ml-4"
                          : "bg-white mr-4"
                      }`}
                    >
                      <div className="flex justify-between items-start mb-1">
                        <span
                          className={`text-xs font-medium ${
                            message.is_from_user
                              ? "text-blue-800"
                              : "text-gray-800"
                          }`}
                        >
                          {message.is_from_user ? "User" : "AI"}
                        </span>
                        <span className="text-xs text-gray-500">
                          {format(new Date(message.created_at), "MMM d, HH:mm")}
                        </span>
                      </div>
                      <div className="text-gray-900">
                        {message.content.length > 200
                          ? `${message.content.substring(0, 200)}...`
                          : message.content}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        Session: {message.session_id.substring(0, 8)}...
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-500 text-white text-base font-medium rounded-md hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-300"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

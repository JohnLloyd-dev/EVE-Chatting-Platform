import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "react-query";
import { adminApi } from "../../lib/api";
import AdminLayout from "../../components/AdminLayout";
import { ConversationSummary, MessageHistory } from "../../types";
import { format } from "date-fns";
import toast from "react-hot-toast";

export default function AdminConversations() {
  const [selectedConversation, setSelectedConversation] = useState<
    string | null
  >(null);
  const [interventionMessage, setInterventionMessage] = useState("");
  const queryClient = useQueryClient();

  // Get conversations list
  const {
    data: conversations,
    isLoading,
    error,
  } = useQuery<ConversationSummary[]>(
    "conversations",
    () => adminApi.getConversations(),
    {
      refetchInterval: 10000, // Refetch every 10 seconds
    }
  );

  // Get conversation details
  const { data: conversationDetails, isLoading: isLoadingDetails } =
    useQuery<MessageHistory>(
      ["conversationDetails", selectedConversation],
      () => adminApi.getConversationDetails(selectedConversation!),
      {
        enabled: !!selectedConversation,
        refetchInterval: 5000, // Refetch every 5 seconds
      }
    );

  // Admin intervention mutation
  const interventionMutation = useMutation(
    ({ sessionId, message }: { sessionId: string; message: string }) =>
      adminApi.intervene(sessionId, message),
    {
      onSuccess: () => {
        setInterventionMessage("");
        toast.success("Intervention sent successfully");
        queryClient.invalidateQueries([
          "conversationDetails",
          selectedConversation,
        ]);
      },
      onError: (error: any) => {
        toast.error(
          error.response?.data?.detail || "Failed to send intervention"
        );
      },
    }
  );

  // Block user mutation
  const blockUserMutation = useMutation(
    ({ userId, block }: { userId: string; block: boolean }) =>
      adminApi.blockUser(userId, block),
    {
      onSuccess: (_, variables) => {
        toast.success(
          `User ${variables.block ? "blocked" : "unblocked"} successfully`
        );
        queryClient.invalidateQueries("conversations");
        queryClient.invalidateQueries([
          "conversationDetails",
          selectedConversation,
        ]);
      },
      onError: (error: any) => {
        toast.error(
          error.response?.data?.detail || "Failed to update user status"
        );
      },
    }
  );

  const handleIntervention = () => {
    if (!selectedConversation || !interventionMessage.trim()) return;

    interventionMutation.mutate({
      sessionId: selectedConversation,
      message: interventionMessage.trim(),
    });
  };

  const handleBlockUser = (userId: string, block: boolean) => {
    blockUserMutation.mutate({ userId, block });
  };

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
          <div className="text-red-600 mb-4">Failed to load conversations</div>
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
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            Conversations
          </h2>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Conversations List */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">
                All Conversations
              </h3>
              <p className="text-sm text-gray-600">
                {conversations?.length || 0} total conversations
              </p>
            </div>

            <div className="max-h-96 overflow-y-auto">
              {conversations?.map((conversation) => (
                <div
                  key={conversation.session_id}
                  className={`p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 ${
                    selectedConversation === conversation.session_id
                      ? "bg-primary-50"
                      : ""
                  }`}
                  onClick={() =>
                    setSelectedConversation(conversation.session_id)
                  }
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-medium text-gray-900">
                        {conversation.user_email ||
                          `User #${conversation.user_id}`}
                      </span>
                      {conversation.user_blocked && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                          Blocked
                        </span>
                      )}
                    </div>
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        conversation.is_active
                          ? "bg-green-100 text-green-800"
                          : "bg-gray-100 text-gray-800"
                      }`}
                    >
                      {conversation.is_active ? "Active" : "Inactive"}
                    </span>
                  </div>

                  <div className="text-sm text-gray-600 mb-2">
                    {conversation.message_count} messages
                  </div>

                  {conversation.last_message && (
                    <div className="text-sm text-gray-500 truncate">
                      {conversation.last_message}
                    </div>
                  )}

                  <div className="text-xs text-gray-400 mt-2">
                    Updated:{" "}
                    {format(new Date(conversation.updated_at), "MMM dd, HH:mm")}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Conversation Details */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            {selectedConversation ? (
              <>
                <div className="p-4 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-900">
                      Conversation Details
                    </h3>
                    {conversationDetails && (
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() =>
                            handleBlockUser(
                              conversationDetails.user_info.id,
                              !conversationDetails.user_info.is_blocked
                            )
                          }
                          className={`text-sm px-3 py-1 rounded ${
                            conversationDetails.user_info.is_blocked
                              ? "bg-green-100 text-green-700 hover:bg-green-200"
                              : "bg-red-100 text-red-700 hover:bg-red-200"
                          }`}
                          disabled={blockUserMutation.isLoading}
                        >
                          {conversationDetails.user_info.is_blocked
                            ? "Unblock"
                            : "Block"}{" "}
                          User
                        </button>
                      </div>
                    )}
                  </div>

                  {conversationDetails && (
                    <div className="mt-2 text-sm text-gray-600">
                      <div>
                        User:{" "}
                        {conversationDetails.user_info.email ||
                          `User #${conversationDetails.user_info.id}`}
                      </div>
                      <div>Session: {conversationDetails.session_info.id}</div>
                    </div>
                  )}
                </div>

                {isLoadingDetails ? (
                  <div className="flex items-center justify-center h-64">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                  </div>
                ) : conversationDetails ? (
                  <>
                    {/* Messages */}
                    <div className="max-h-64 overflow-y-auto p-4 space-y-3">
                      {conversationDetails.messages.map((message) => (
                        <div
                          key={message.id}
                          className={`flex ${
                            message.is_from_user
                              ? "justify-end"
                              : "justify-start"
                          }`}
                        >
                          <div
                            className={`max-w-xs px-3 py-2 rounded-lg text-sm ${
                              message.is_from_user
                                ? "bg-primary-600 text-white"
                                : message.is_admin_intervention
                                ? "bg-yellow-100 text-yellow-800 border border-yellow-300"
                                : "bg-gray-200 text-gray-800"
                            }`}
                          >
                            <div>{message.content}</div>
                            <div
                              className={`text-xs mt-1 ${
                                message.is_from_user
                                  ? "text-primary-200"
                                  : "text-gray-500"
                              }`}
                            >
                              {format(new Date(message.created_at), "HH:mm")}
                              {message.is_admin_intervention && (
                                <span className="ml-1 font-medium">
                                  (Admin)
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Admin Intervention */}
                    <div className="p-4 border-t border-gray-200">
                      <div className="space-y-3">
                        <label className="block text-sm font-medium text-gray-700">
                          Send Admin Message
                        </label>
                        <textarea
                          value={interventionMessage}
                          onChange={(e) =>
                            setInterventionMessage(e.target.value)
                          }
                          placeholder="Type your intervention message..."
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                          rows={3}
                        />
                        <button
                          onClick={handleIntervention}
                          disabled={
                            !interventionMessage.trim() ||
                            interventionMutation.isLoading
                          }
                          className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {interventionMutation.isLoading
                            ? "Sending..."
                            : "Send Intervention"}
                        </button>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="p-4 text-center text-gray-500">
                    Failed to load conversation details
                  </div>
                )}
              </>
            ) : (
              <div className="p-8 text-center text-gray-500">
                Select a conversation to view details
              </div>
            )}
          </div>
        </div>
      </div>
    </AdminLayout>
  );
}

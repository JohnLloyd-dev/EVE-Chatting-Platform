import { useState, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "react-query";
import { chatApi } from "../lib/api";
import { ChatMessage, ChatSession } from "../types";
import { format } from "date-fns";
import toast from "react-hot-toast";

interface ChatInterfaceProps {
  userId: string;
}

export default function ChatInterface({ userId }: ChatInterfaceProps) {
  const [message, setMessage] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();

  // Get chat session
  const {
    data: session,
    isLoading,
    error,
  } = useQuery<ChatSession>(
    ["chatSession", userId],
    () => chatApi.getSession(userId),
    {
      refetchInterval: 5000, // Refetch every 5 seconds to get new messages
    }
  );

  // Send message mutation
  const sendMessageMutation = useMutation(
    ({ sessionId, message }: { sessionId: string; message: string }) =>
      chatApi.sendMessage(sessionId, message),
    {
      onSuccess: (data) => {
        setMessage("");
        setIsProcessing(true);
        // Poll for AI response
        pollForResponse(data.task_id);
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || "Failed to send message");
      },
    }
  );

  // Poll for AI response
  const pollForResponse = async (taskId: string) => {
    const maxAttempts = 30; // 30 seconds max
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await chatApi.getResponseStatus(taskId);

        if (response.status === "completed") {
          setIsProcessing(false);
          // Refetch session to get new messages
          queryClient.invalidateQueries(["chatSession", userId]);
        } else if (response.status === "failed") {
          setIsProcessing(false);
          toast.error("AI response failed");
        } else if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 1000); // Poll every second
        } else {
          setIsProcessing(false);
          toast.error("AI response timeout");
        }
      } catch (error) {
        setIsProcessing(false);
        toast.error("Failed to get AI response status");
      }
    };

    poll();
  };

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [session?.messages]);

  const handleSendMessage = () => {
    if (!message.trim() || !session || sendMessageMutation.isLoading) return;

    sendMessageMutation.mutate({
      sessionId: session.id,
      message: message.trim(),
    });
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <div className="text-red-600 mb-4">
          {(error as any)?.response?.data?.detail ||
            "Failed to load chat session"}
        </div>
        <button
          onClick={() => window.location.reload()}
          className="btn-primary"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="text-center py-8">
        <div className="text-gray-600">No active chat session found</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {session.messages.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            Start the conversation by sending a message!
          </div>
        ) : (
          session.messages.map((msg: ChatMessage) => (
            <div
              key={msg.id}
              className={`flex ${
                msg.is_from_user ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`chat-message ${
                  msg.is_from_user
                    ? "chat-message-user"
                    : msg.is_admin_intervention
                    ? "chat-message-admin"
                    : "chat-message-ai"
                }`}
              >
                <div className="text-sm">{msg.content}</div>
                <div
                  className={`text-xs mt-1 ${
                    msg.is_from_user ? "text-primary-200" : "text-gray-500"
                  }`}
                >
                  {format(new Date(msg.created_at), "HH:mm")}
                  {msg.is_admin_intervention && (
                    <span className="ml-2 font-medium">(Admin)</span>
                  )}
                </div>
              </div>
            </div>
          ))
        )}

        {isProcessing && (
          <div className="flex justify-start">
            <div className="chat-message chat-message-ai">
              <div className="flex items-center space-x-2">
                <div className="animate-pulse">AI is thinking...</div>
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: "0.1s" }}
                  ></div>
                  <div
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: "0.2s" }}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-4">
        <div className="flex space-x-2">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            className="flex-1 resize-none input-field"
            rows={2}
            disabled={sendMessageMutation.isLoading || isProcessing}
          />
          <button
            onClick={handleSendMessage}
            disabled={
              !message.trim() || sendMessageMutation.isLoading || isProcessing
            }
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed px-6"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

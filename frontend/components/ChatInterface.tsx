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
  const [showLoadingAnimation, setShowLoadingAnimation] = useState(true);
  const [loadingStep, setLoadingStep] = useState(0);
  const [hasInitializedAI, setHasInitializedAI] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
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

  // No AI health status needed for users - keep it clean and human-like

  // Send message mutation using new integrated AI
  const sendMessageMutation = useMutation(
    ({ sessionId, message }: { sessionId: string; message: string }) =>
      chatApi.sendMessage(sessionId, message),
    {
      onSuccess: (data) => {
        setMessage("");
        // isProcessing removed - using sendMessageMutation.isLoading instead
        // AI response is immediate with new integrated approach
        // Refetch session to get new messages
        queryClient.invalidateQueries(["chatSession", userId]);
        toast.success("Message sent!");
      },
      onError: (error: any) => {
        // Safely extract error message
        let errorMessage = "Failed to send message";
        if (error?.response?.data?.detail) {
          if (typeof error.response.data.detail === "string") {
            errorMessage = error.response.data.detail;
          } else if (Array.isArray(error.response.data.detail)) {
            // Handle validation error array
            const firstError = error.response.data.detail[0];
            if (
              firstError &&
              typeof firstError === "object" &&
              "msg" in firstError
            ) {
              errorMessage = firstError.msg;
            }
          }
        }
        toast.error(errorMessage);
      },
    }
  );

  // AI response is now immediate with integrated approach - no polling needed

  // Loading animation effect
  useEffect(() => {
    if (showLoadingAnimation) {
      const steps = [
        "Hold please…",
        "Loading your preferences…",
        "Connecting you with your partner…",
      ];

      const interval = setInterval(() => {
        setLoadingStep((prev) => {
          if (prev < steps.length - 1) {
            return prev + 1;
          } else {
            clearInterval(interval);
            setTimeout(() => {
              setShowLoadingAnimation(false);
            }, 1000);
            return prev;
          }
        });
      }, 1500);

      return () => clearInterval(interval);
    }
  }, [showLoadingAnimation]);

  // Auto-focus text input when component mounts and maintain focus
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  }, []);

  // Re-focus after loading animation completes
  useEffect(() => {
    if (!showLoadingAnimation && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [showLoadingAnimation]);

  // Re-focus after sending a message
  useEffect(() => {
    if (!sendMessageMutation.isLoading && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [sendMessageMutation.isLoading]);

  // Global keyboard event listener to focus input on any key press
  useEffect(() => {
    const handleGlobalKeyPress = (e: KeyboardEvent) => {
      // Don't interfere with special keys or if user is typing in another input
      if (
        e.ctrlKey ||
        e.altKey ||
        e.metaKey ||
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement ||
        sendMessageMutation.isLoading
      ) {
        return;
      }

      // Focus the textarea if it's not already focused
      if (
        textareaRef.current &&
        document.activeElement !== textareaRef.current
      ) {
        textareaRef.current.focus();
      }
    };

    document.addEventListener("keydown", handleGlobalKeyPress);
    return () => document.removeEventListener("keydown", handleGlobalKeyPress);
  }, [sendMessageMutation.isLoading]);

  // Send initial AI message using new integrated approach
  useEffect(() => {
    if (
      session &&
      !hasInitializedAI &&
      !showLoadingAnimation &&
      session.messages.length === 0
    ) {
      setHasInitializedAI(true);
      // Initialize AI session and show "hi" message
      const initializeAI = async () => {
        try {
          // AI is now integrated - no need to initialize separately
          // Show AI "hi" message automatically
          console.log("AI system ready - showing initial 'hi' message");
          
          // Add AI "hi" message to the display
          const aiHiMessage = {
            id: "ai-init",
            content: "hi",
            is_from_user: false,
            is_admin_intervention: false,
            created_at: new Date().toISOString(),
          };
          
          // Update session messages to include AI "hi"
          if (session.messages.length === 0) {
            session.messages = [aiHiMessage];
            // Force re-render
            queryClient.invalidateQueries(["chatSession", userId]);
          }
        } catch (error) {
          console.error("Failed to initialize AI system:", error);
          toast.error("Failed to initialize AI system");
        }
      };

      initializeAI();
    }
  }, [session, hasInitializedAI, showLoadingAnimation]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [session?.messages]);

  const handleSendMessage = async () => {
    if (!message.trim() || !session || sendMessageMutation.isLoading) return;

    try {
      // Use the integrated AI endpoint
      await sendMessageMutation.mutateAsync({
        sessionId: session.id,
        message: message.trim(),
      });
    } catch (error: any) {
      // Log error for debugging
      console.error("Failed to send message:", error);

      // Safely extract error message
      let errorMessage = "Failed to send message";
      if (error?.response?.data?.detail) {
        if (typeof error.response.data.detail === "string") {
          errorMessage = error.response.data.detail;
        } else if (Array.isArray(error.response.data.detail)) {
          // Handle validation error array
          const firstError = error.response.data.detail[0];
          if (
            firstError &&
            typeof firstError === "object" &&
            "msg" in firstError
          ) {
            errorMessage = firstError.msg;
          }
        }
      }
      toast.error(errorMessage);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Handle clicking anywhere in the chat area to focus the input
  const handleChatAreaClick = () => {
    if (textareaRef.current && !sendMessageMutation.isLoading) {
      textareaRef.current.focus();
    }
  };

  if (isLoading || showLoadingAnimation) {
    const loadingSteps = [
      "Hold please…",
      "Loading your preferences…",
      "Connecting you with your partner…",
    ];

    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="relative mb-8">
            <div className="animate-spin rounded-full h-16 w-16 border-4 border-purple-500/30 border-t-purple-500 mx-auto"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-6 h-6 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full animate-pulse"></div>
            </div>
          </div>
          <div className="space-y-2">
            {loadingSteps.map((step, index) => (
              <div
                key={index}
                className={`text-lg transition-all duration-500 ${
                  index <= loadingStep
                    ? "text-white opacity-100 transform translate-y-0"
                    : "text-gray-500 opacity-50 transform translate-y-2"
                }`}
              >
                {index < loadingStep && "✓ "}
                {index === loadingStep && (
                  <span className="inline-block w-2 h-2 bg-purple-500 rounded-full animate-pulse mr-2"></span>
                )}
                {step}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    // Debug: Log the error object to see its structure
    console.log("Error object:", error);
    console.log("Error type:", typeof error);
    console.log(
      "Error keys:",
      error && typeof error === "object" ? Object.keys(error) : "N/A"
    );

    // Safely extract error message
    let errorMessage = "Failed to load chat session";

    if (error && typeof error === "object") {
      if ("response" in error && error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if ("message" in error && typeof error.message === "string") {
        errorMessage = error.message;
      } else if ("detail" in error && typeof error.detail === "string") {
        errorMessage = error.detail;
      }
    }

    return (
      <div className="text-center py-8">
        <div className="text-red-400 mb-4 text-lg">{errorMessage}</div>
        <button
          onClick={() => window.location.reload()}
          className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold py-2 px-4 rounded-lg transition-all duration-300 transform hover:scale-105"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="text-center py-8">
        <div className="text-gray-300">No active chat session found</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full" onClick={handleChatAreaClick}>
      {/* AI Status Indicator */}
      {/* Clean chat interface - no system status for users */}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {session.messages.length === 0 ? (
          <div className="text-center text-gray-300 py-8">
            {hasInitializedAI
              ? "Waiting for AI response..."
              : "Initializing conversation..."}
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
                  msg.is_from_user ? "chat-message-user" : "chat-message-ai"
                }`}
              >
                <div className="text-sm">
                  {(() => {
                    // Debug: Log message content to see what we're getting
                    if (typeof msg.content !== "string") {
                      console.log("Non-string message content:", msg.content);
                      console.log("Message object:", msg);
                    }
                    return typeof msg.content === "string"
                      ? msg.content
                      : JSON.stringify(msg.content);
                  })()}
                </div>
                <div
                  className={`text-xs mt-1 ${
                    msg.is_from_user ? "text-purple-200" : "text-gray-400"
                  }`}
                >
                  {format(new Date(msg.created_at), "HH:mm")}
                </div>
              </div>
            </div>
          ))
        )}

        {sendMessageMutation.isLoading && (
          <div className="flex justify-start">
            <div className="chat-message chat-message-ai">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></div>
                <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></div>
                <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-gray-400 ml-2">typing...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-700/50 p-4">
        <div className="flex space-x-2">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            className="flex-1 resize-none px-4 py-3 bg-gray-700/50 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent text-white placeholder-gray-400 transition-all duration-200"
            rows={2}
            disabled={sendMessageMutation.isLoading}
            autoFocus
          />
          <button
            onClick={handleSendMessage}
            disabled={!message.trim() || sendMessageMutation.isLoading}
            className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

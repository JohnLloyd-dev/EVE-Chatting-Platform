import React from "react";
import { useQuery } from "react-query";
import { chatApi } from "../lib/api";
import { AIHealthStatus } from "../types";

export default function AIModelStatus() {
  const {
    data: aiHealth,
    isLoading,
    error,
    refetch,
  } = useQuery<AIHealthStatus>(["aiHealth"], () => chatApi.getAIHealth(), {
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  if (isLoading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-700 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-3 bg-gray-700 rounded"></div>
            <div className="h-3 bg-gray-700 rounded w-5/6"></div>
            <div className="h-3 bg-gray-700 rounded w-4/6"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-6">
        <div className="text-red-400 mb-4">
          <h3 className="text-lg font-semibold">AI Model Status Error</h3>
          <p className="text-sm">Failed to load AI model status</p>
        </div>
        <button
          onClick={() => refetch()}
          className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded text-sm transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!aiHealth) {
    return null;
  }

  const { status, ai_model } = aiHealth;

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">AI Model Status</h3>
        <div
          className={`px-3 py-1 rounded-full text-xs font-medium ${
            status === "healthy"
              ? "bg-green-900/30 text-green-400 border border-green-500/30"
              : "bg-red-900/30 text-red-400 border border-red-500/30"
          }`}
        >
          {status === "healthy" ? "Healthy" : "Unhealthy"}
        </div>
      </div>

      <div className="space-y-4">
        {/* Model Info */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-gray-400 text-sm">Model Name</label>
            <p className="text-white font-mono text-sm">
              {ai_model.model_name}
            </p>
          </div>
          <div>
            <label className="text-gray-400 text-sm">Device</label>
            <p className="text-white text-sm">{ai_model.device}</p>
          </div>
        </div>

        {/* GPU Status */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-gray-400 text-sm">GPU Status</label>
            <p
              className={`text-sm font-medium ${
                ai_model.gpu_available ? "text-green-400" : "text-yellow-400"
              }`}
            >
              {ai_model.gpu_available ? "Available" : "Not Available"}
            </p>
          </div>
          <div>
            <label className="text-gray-400 text-sm">Active Sessions</label>
            <p className="text-white text-sm">{ai_model.active_sessions}</p>
          </div>
        </div>

        {/* Memory Usage */}
        {ai_model.gpu_available && (
          <div>
            <label className="text-gray-400 text-sm">GPU Memory Usage</label>
            <div className="mt-2 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-300">Allocated:</span>
                <span className="text-white">
                  {ai_model.gpu_memory_allocated} GB
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-300">Reserved:</span>
                <span className="text-white">
                  {ai_model.gpu_memory_reserved} GB
                </span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{
                    width: `${Math.min(
                      (ai_model.gpu_memory_allocated / 16) * 100,
                      100
                    )}%`,
                  }}
                ></div>
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="pt-4 border-t border-gray-700">
          <button
            onClick={() => refetch()}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm transition-colors mr-2"
          >
            Refresh Status
          </button>
          <button
            onClick={async () => {
              try {
                await fetch("/ai/optimize-memory", { method: "POST" });
                refetch();
              } catch (error) {
                console.error("Failed to optimize memory:", error);
              }
            }}
            className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded text-sm transition-colors"
          >
            Optimize Memory
          </button>
        </div>
      </div>
    </div>
  );
}

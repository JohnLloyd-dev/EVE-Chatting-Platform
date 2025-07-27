"use client";

import { useState, useEffect } from "react";
import { adminApi } from "../../../lib/api";
import { SystemPrompt } from "../../../types";
import { toast } from "react-hot-toast";

export default function SystemPromptsPage() {
  const [prompts, setPrompts] = useState<SystemPrompt[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState<SystemPrompt | null>(null);
  const [formData, setFormData] = useState({
    name: "",
    prompt_text: "",
  });

  useEffect(() => {
    fetchPrompts();
  }, []);

  const fetchPrompts = async () => {
    try {
      const data = await adminApi.getSystemPrompts();
      setPrompts(data);
    } catch (error) {
      toast.error("Failed to fetch system prompts");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await adminApi.createSystemPrompt(formData);
      toast.success("System prompt created successfully");
      setFormData({ name: "", prompt_text: "" });
      setShowCreateForm(false);
      fetchPrompts();
    } catch (error: any) {
      toast.error(
        error.response?.data?.detail || "Failed to create system prompt"
      );
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingPrompt) return;

    try {
      await adminApi.updateSystemPrompt(editingPrompt.id, formData);
      toast.success("System prompt updated successfully");
      setEditingPrompt(null);
      setFormData({ name: "", prompt_text: "" });
      fetchPrompts();
    } catch (error: any) {
      toast.error(
        error.response?.data?.detail || "Failed to update system prompt"
      );
    }
  };

  const handleSetActive = async (promptId: string) => {
    try {
      await adminApi.updateSystemPrompt(promptId, { is_active: true });
      toast.success("System prompt activated");
      fetchPrompts();
    } catch (error: any) {
      toast.error(
        error.response?.data?.detail || "Failed to activate system prompt"
      );
    }
  };

  const handleDelete = async (promptId: string) => {
    if (!confirm("Are you sure you want to delete this system prompt?")) return;

    try {
      await adminApi.deleteSystemPrompt(promptId);
      toast.success("System prompt deleted");
      fetchPrompts();
    } catch (error: any) {
      toast.error(
        error.response?.data?.detail || "Failed to delete system prompt"
      );
    }
  };

  const startEdit = (prompt: SystemPrompt) => {
    setEditingPrompt(prompt);
    setFormData({
      name: prompt.name,
      prompt_text: prompt.prompt_text,
    });
    setShowCreateForm(false);
  };

  const cancelEdit = () => {
    setEditingPrompt(null);
    setFormData({ name: "", prompt_text: "" });
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">System Prompts</h1>
        <button
          onClick={() => {
            setShowCreateForm(true);
            setEditingPrompt(null);
            setFormData({ name: "", prompt_text: "" });
          }}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          Create New Prompt
        </button>
      </div>

      {/* Create/Edit Form */}
      {(showCreateForm || editingPrompt) && (
        <div className="bg-white p-6 rounded-lg shadow border">
          <h2 className="text-lg font-semibold mb-4">
            {editingPrompt ? "Edit System Prompt" : "Create New System Prompt"}
          </h2>
          <form onSubmit={editingPrompt ? handleUpdate : handleCreate}>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Prompt Text
                </label>
                <textarea
                  value={formData.prompt_text}
                  onChange={(e) =>
                    setFormData({ ...formData, prompt_text: e.target.value })
                  }
                  rows={8}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter the system prompt that will be combined with user scenarios..."
                  required
                />
              </div>
            </div>
            <div className="flex gap-2 mt-4">
              <button
                type="submit"
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
              >
                {editingPrompt ? "Update" : "Create"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowCreateForm(false);
                  cancelEdit();
                }}
                className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Prompts List */}
      <div className="space-y-4">
        {prompts.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No system prompts found. Create one to get started.
          </div>
        ) : (
          prompts.map((prompt) => (
            <div
              key={prompt.id}
              className={`bg-white p-6 rounded-lg shadow border ${
                prompt.is_active ? "border-green-500 bg-green-50" : ""
              }`}
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                    {prompt.name}
                    {prompt.is_active && (
                      <span className="bg-green-500 text-white text-xs px-2 py-1 rounded-full">
                        ACTIVE
                      </span>
                    )}
                  </h3>
                  <p className="text-sm text-gray-500">
                    Created: {new Date(prompt.created_at).toLocaleDateString()}
                    {prompt.updated_at !== prompt.created_at && (
                      <span>
                        {" "}
                        • Updated:{" "}
                        {new Date(prompt.updated_at).toLocaleDateString()}
                      </span>
                    )}
                  </p>
                </div>
                <div className="flex gap-2">
                  {!prompt.is_active && (
                    <button
                      onClick={() => handleSetActive(prompt.id)}
                      className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                    >
                      Set Active
                    </button>
                  )}
                  <button
                    onClick={() => startEdit(prompt)}
                    className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                  >
                    Edit
                  </button>
                  {!prompt.is_active && (
                    <button
                      onClick={() => handleDelete(prompt.id)}
                      className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                    >
                      Delete
                    </button>
                  )}
                </div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm text-gray-700 whitespace-pre-wrap">
                  {prompt.prompt_text}
                </p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

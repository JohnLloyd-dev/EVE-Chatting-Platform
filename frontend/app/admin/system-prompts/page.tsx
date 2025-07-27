"use client";

import { useState, useEffect } from "react";
import { adminApi } from "../../../lib/api";
import { SystemPrompt } from "../../../types";
import { toast } from "react-hot-toast";
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  DocumentTextIcon,
  ClockIcon,
  UserIcon,
} from "@heroicons/react/24/outline";

export default function SystemPromptsPage() {
  const [prompts, setPrompts] = useState<SystemPrompt[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState<SystemPrompt | null>(null);
  const [formData, setFormData] = useState({
    name: "",
    prompt_text: "",
  });
  const [submitting, setSubmitting] = useState(false);

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
    if (!formData.name.trim() || !formData.prompt_text.trim()) {
      toast.error("Please fill in all fields");
      return;
    }

    setSubmitting(true);
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
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingPrompt) return;
    if (!formData.name.trim() || !formData.prompt_text.trim()) {
      toast.error("Please fill in all fields");
      return;
    }

    setSubmitting(true);
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
    } finally {
      setSubmitting(false);
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
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          </div>
        </div>
      </div>
    );
  }

  const activePrompt = prompts.find((p) => p.is_active);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                System Prompts
              </h1>
              <p className="mt-2 text-gray-600">
                Manage AI system prompts that guide conversation behavior
              </p>
            </div>
            <button
              onClick={() => {
                setShowCreateForm(true);
                setEditingPrompt(null);
                setFormData({ name: "", prompt_text: "" });
              }}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              <PlusIcon className="h-5 w-5 mr-2" />
              Create New Prompt
            </button>
          </div>
        </div>

        {/* Active Prompt Status */}
        {activePrompt && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center">
              <CheckCircleIcon className="h-5 w-5 text-green-400 mr-2" />
              <div>
                <h3 className="text-sm font-medium text-green-800">
                  Currently Active: {activePrompt.name}
                </h3>
                <p className="text-sm text-green-700 mt-1">
                  This prompt is being used for all new conversations
                </p>
              </div>
            </div>
          </div>
        )}

        {!activePrompt && prompts.length > 0 && (
          <div className="mb-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-center">
              <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400 mr-2" />
              <div>
                <h3 className="text-sm font-medium text-yellow-800">
                  No Active System Prompt
                </h3>
                <p className="text-sm text-yellow-700 mt-1">
                  Please activate a system prompt to ensure consistent AI
                  behavior
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Create/Edit Form */}
        {(showCreateForm || editingPrompt) && (
          <div className="mb-8 bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">
                {editingPrompt
                  ? "Edit System Prompt"
                  : "Create New System Prompt"}
              </h2>
            </div>
            <form
              onSubmit={editingPrompt ? handleUpdate : handleCreate}
              className="p-6"
            >
              <div className="space-y-6">
                <div>
                  <label
                    htmlFor="name"
                    className="block text-sm font-medium text-gray-700"
                  >
                    Prompt Name
                  </label>
                  <div className="mt-1">
                    <input
                      type="text"
                      id="name"
                      value={formData.name}
                      onChange={(e) =>
                        setFormData({ ...formData, name: e.target.value })
                      }
                      className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      placeholder="e.g., Sexual Fantasy Assistant v2"
                      required
                    />
                  </div>
                  <p className="mt-2 text-sm text-gray-500">
                    Give your system prompt a descriptive name
                  </p>
                </div>

                <div>
                  <label
                    htmlFor="prompt_text"
                    className="block text-sm font-medium text-gray-700"
                  >
                    System Prompt Instructions
                  </label>
                  <div className="mt-1">
                    <textarea
                      id="prompt_text"
                      rows={10}
                      value={formData.prompt_text}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          prompt_text: e.target.value,
                        })
                      }
                      className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      placeholder="You are a sexual fantasy assistant. Always speak in the first person and stay in character..."
                      required
                    />
                  </div>
                  <p className="mt-2 text-sm text-gray-500">
                    These instructions will be combined with each user's
                    personalized scenario
                  </p>
                </div>
              </div>

              <div className="mt-6 flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateForm(false);
                    cancelEdit();
                  }}
                  className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                >
                  {submitting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      {editingPrompt ? "Updating..." : "Creating..."}
                    </>
                  ) : editingPrompt ? (
                    "Update Prompt"
                  ) : (
                    "Create Prompt"
                  )}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Prompts Grid */}
        <div className="space-y-6">
          {prompts.length === 0 ? (
            <div className="text-center py-12">
              <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">
                No system prompts
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                Get started by creating your first system prompt.
              </p>
              <div className="mt-6">
                <button
                  onClick={() => {
                    setShowCreateForm(true);
                    setEditingPrompt(null);
                    setFormData({ name: "", prompt_text: "" });
                  }}
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                >
                  <PlusIcon className="h-5 w-5 mr-2" />
                  Create System Prompt
                </button>
              </div>
            </div>
          ) : (
            <div className="grid gap-6 lg:grid-cols-1">
              {prompts.map((prompt) => (
                <div
                  key={prompt.id}
                  className={`bg-white overflow-hidden shadow rounded-lg border-2 ${
                    prompt.is_active
                      ? "border-green-500 ring-2 ring-green-200"
                      : "border-gray-200"
                  }`}
                >
                  <div className="px-6 py-4 border-b border-gray-200">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div
                          className={`flex-shrink-0 w-3 h-3 rounded-full ${
                            prompt.is_active ? "bg-green-500" : "bg-gray-300"
                          }`}
                        ></div>
                        <div>
                          <h3 className="text-lg font-medium text-gray-900 flex items-center space-x-2">
                            <span>{prompt.name}</span>
                            {prompt.is_active && (
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                <CheckCircleIcon className="w-3 h-3 mr-1" />
                                Active
                              </span>
                            )}
                          </h3>
                          <div className="flex items-center space-x-4 text-sm text-gray-500 mt-1">
                            <div className="flex items-center">
                              <ClockIcon className="w-4 h-4 mr-1" />
                              Created{" "}
                              {new Date(prompt.created_at).toLocaleDateString()}
                            </div>
                            {prompt.updated_at !== prompt.created_at && (
                              <div className="flex items-center">
                                <PencilIcon className="w-4 h-4 mr-1" />
                                Updated{" "}
                                {new Date(
                                  prompt.updated_at
                                ).toLocaleDateString()}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        {!prompt.is_active && (
                          <button
                            onClick={() => handleSetActive(prompt.id)}
                            className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                          >
                            <CheckCircleIcon className="w-4 h-4 mr-1" />
                            Activate
                          </button>
                        )}
                        <button
                          onClick={() => startEdit(prompt)}
                          className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-xs font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                        >
                          <PencilIcon className="w-4 h-4 mr-1" />
                          Edit
                        </button>
                        {!prompt.is_active && (
                          <button
                            onClick={() => handleDelete(prompt.id)}
                            className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                          >
                            <TrashIcon className="w-4 h-4 mr-1" />
                            Delete
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="px-6 py-4">
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h4 className="text-sm font-medium text-gray-900 mb-2">
                        System Instructions:
                      </h4>
                      <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                        {prompt.prompt_text}
                      </p>
                    </div>
                    <div className="mt-4 text-xs text-gray-500">
                      <span className="font-medium">Character count:</span>{" "}
                      {prompt.prompt_text.length}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

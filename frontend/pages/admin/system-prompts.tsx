import { useState, useEffect } from "react";
import { adminApi } from "../../lib/api";
import { SystemPrompt } from "../../types";
import { toast } from "react-hot-toast";
import AdminLayout from "../../components/AdminLayout";
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  DocumentTextIcon,
  ClockIcon,
  UserIcon,
  EyeIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";

interface SystemPromptFormData {
  name: string;
  head_prompt: string;
  rule_prompt: string;
}

export default function SystemPromptsPage() {
  const [prompts, setPrompts] = useState<SystemPrompt[]>([]);
  const [activePrompt, setActivePrompt] = useState<SystemPrompt | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState<SystemPrompt | null>(null);
  const [formData, setFormData] = useState<SystemPromptFormData>({
    name: "",
    head_prompt: "",
    rule_prompt: "",
  });
  const [submitting, setSubmitting] = useState(false);

  // Sample Tally data for preview
  const sampleTallyPrompt =
    "Your name is L. You are a 30 year old asian policewoman. I am a man who you just met in a forest. When we meet you tie me up and force me to have sex with you. You gag me and blindfold me and don't let me go when I ask you to.";

  const fetchPrompts = async () => {
    try {
      setLoading(true);
      console.log("Fetching system prompts...");
      const data = await adminApi.getSystemPrompts();
      console.log("Fetched prompts:", data);
      setPrompts(data);

      // Find active prompt
      const active = data.find((p: SystemPrompt) => p.is_active);
      setActivePrompt(active || null);
      console.log("Active prompt:", active);
    } catch (error) {
      console.error("Error fetching system prompts:", error);
      toast.error("Failed to load system prompts");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPrompts();
  }, []);

  const handleCreatePrompt = async (e: React.FormEvent) => {
    e.preventDefault();
    if (
      !formData.name.trim() ||
      !formData.head_prompt.trim() ||
      !formData.rule_prompt.trim()
    ) {
      toast.error("Please fill in all fields");
      return;
    }

    try {
      setSubmitting(true);
      await adminApi.createSystemPrompt(formData);
      toast.success("System prompt created successfully!");
      setShowCreateForm(false);
      setFormData({ name: "", head_prompt: "", rule_prompt: "" });
      fetchPrompts();
    } catch (error: any) {
      toast.error(
        error.response?.data?.detail || "Failed to create system prompt"
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditPrompt = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingPrompt) return;

    if (
      !formData.name.trim() ||
      !formData.head_prompt.trim() ||
      !formData.rule_prompt.trim()
    ) {
      toast.error("Please fill in all fields");
      return;
    }

    try {
      setSubmitting(true);
      console.log("Updating prompt:", editingPrompt.id, formData);
      await adminApi.updateSystemPrompt(editingPrompt.id, formData);
      toast.success("System prompt updated successfully!");
      setShowEditForm(false);
      setEditingPrompt(null);
      setFormData({ name: "", head_prompt: "", rule_prompt: "" });
      fetchPrompts();
    } catch (error: any) {
      console.error("Edit error:", error);
      if (error.response?.status === 401) {
        toast.error("Session expired. Please login again.");
      } else if (error.response?.status === 400) {
        toast.error(error.response?.data?.detail || "Invalid data provided");
      } else {
        toast.error(
          error.response?.data?.detail || "Failed to update system prompt"
        );
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleActivatePrompt = async (promptId: string) => {
    try {
      setSubmitting(true);
      await adminApi.updateSystemPrompt(promptId, { is_active: true });
      toast.success(
        "System prompt activated! This is now the active prompt for all users."
      );
      fetchPrompts();
    } catch (error: any) {
      console.error("Activate error:", error);
      if (error.response?.status === 401) {
        toast.error("Session expired. Please login again.");
      } else {
        toast.error(
          error.response?.data?.detail || "Failed to activate system prompt"
        );
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeletePrompt = async (promptId: string) => {
    if (
      !confirm(
        "Are you sure you want to delete this system prompt? This action cannot be undone."
      )
    )
      return;

    try {
      setSubmitting(true);
      await adminApi.deleteSystemPrompt(promptId);
      toast.success("System prompt deleted successfully!");
      fetchPrompts();
    } catch (error: any) {
      console.error("Delete error:", error);
      if (error.response?.status === 401) {
        toast.error("Session expired. Please login again.");
      } else {
        toast.error(
          error.response?.data?.detail || "Failed to delete system prompt"
        );
      }
    } finally {
      setSubmitting(false);
    }
  };

  const openEditForm = (prompt: SystemPrompt) => {
    setEditingPrompt(prompt);
    setFormData({
      name: prompt.name,
      head_prompt: prompt.head_prompt,
      rule_prompt: prompt.rule_prompt,
    });
    setShowEditForm(true);
  };

  const openPreview = (prompt: SystemPrompt) => {
    setEditingPrompt(prompt);
    setShowPreview(true);
  };

  const generateCompletePrompt = (headPrompt: string, rulePrompt: string) => {
    return `${headPrompt} ${sampleTallyPrompt} ${rulePrompt}`;
  };

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">System Prompts</h1>
            <p className="text-gray-600 mt-1">
              Manage system prompts that combine with user Tally data
            </p>
          </div>
          {prompts.length > 0 && (
            <button
              onClick={() => setShowCreateForm(true)}
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md flex items-center gap-2 transition-colors"
            >
              <PlusIcon className="w-5 h-5" />
              Create System Prompt
            </button>
          )}
        </div>

        {/* Active Prompt Status */}
        {activePrompt && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center gap-2">
              <CheckCircleIcon className="w-5 h-5 text-green-600" />
              <span className="font-medium text-green-800">
                Currently Active: {activePrompt.name}
              </span>
            </div>
          </div>
        )}

        {/* System Prompts List */}
        {loading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          </div>
        ) : prompts.length === 0 ? (
          <div className="text-center py-12">
            <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">
              No system prompts
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              Get started by creating a new system prompt.
            </p>
            <div className="mt-6">
              <button
                onClick={() => setShowCreateForm(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                <PlusIcon className="w-5 h-5 mr-2" />
                Create System Prompt
              </button>
            </div>
          </div>
        ) : (
          <div className="grid gap-6">
            <div className="text-sm text-gray-500 mb-4">
              Found {prompts.length} system prompt
              {prompts.length !== 1 ? "s" : ""}
            </div>
            {prompts.map((prompt) => (
              <div
                key={prompt.id}
                className={`bg-white rounded-lg shadow-sm border-2 p-6 ${
                  prompt.is_active ? "border-green-500" : "border-gray-200"
                }`}
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center gap-3">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {prompt.name}
                    </h3>
                    {prompt.is_active && (
                      <span className="bg-green-100 text-green-800 text-xs font-medium px-2.5 py-0.5 rounded-full">
                        Active
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {/* Preview Button */}
                    <button
                      onClick={() => openPreview(prompt)}
                      className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                      title="Preview Complete Prompt"
                    >
                      <EyeIcon className="w-4 h-4 mr-1" />
                      Preview
                    </button>

                    {/* Edit Button */}
                    <button
                      onClick={() => openEditForm(prompt)}
                      disabled={submitting}
                      className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Edit System Prompt"
                    >
                      <PencilIcon className="w-4 h-4 mr-1" />
                      Edit
                    </button>

                    {/* Activate Button - only show if not active */}
                    {!prompt.is_active && (
                      <button
                        onClick={() => handleActivatePrompt(prompt.id)}
                        disabled={submitting}
                        className="inline-flex items-center px-3 py-2 border border-green-300 shadow-sm text-sm leading-4 font-medium rounded-md text-green-700 bg-green-50 hover:bg-green-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Set as Active System Prompt"
                      >
                        <CheckCircleIcon className="w-4 h-4 mr-1" />
                        Activate
                      </button>
                    )}

                    {/* Delete Button */}
                    <button
                      onClick={() => handleDeletePrompt(prompt.id)}
                      disabled={submitting}
                      className="inline-flex items-center px-3 py-2 border border-red-300 shadow-sm text-sm leading-4 font-medium rounded-md text-red-700 bg-red-50 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Delete System Prompt"
                    >
                      <TrashIcon className="w-4 h-4 mr-1" />
                      Delete
                    </button>
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-medium text-gray-700 mb-2">
                      Head Prompt
                    </h4>
                    <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded border">
                      {prompt.head_prompt}
                    </p>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-700 mb-2">
                      Rule Prompt
                    </h4>
                    <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded border">
                      {prompt.rule_prompt}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4 mt-4 text-sm text-gray-500">
                  <div className="flex items-center gap-1">
                    <ClockIcon className="w-4 h-4" />
                    {new Date(prompt.created_at).toLocaleDateString()}
                  </div>
                  <div className="flex items-center gap-1">
                    <UserIcon className="w-4 h-4" />
                    Created by admin
                  </div>
                </div>
              </div>
            ))}

            {prompts.length === 0 && (
              <div className="text-center py-12">
                <DocumentTextIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No system prompts yet
                </h3>
                <p className="text-gray-600 mb-4">
                  Create your first system prompt to get started.
                </p>
                <button
                  onClick={() => setShowCreateForm(true)}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md transition-colors"
                >
                  Create System Prompt
                </button>
              </div>
            )}
          </div>
        )}

        {/* Create Form Modal */}
        {showCreateForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-semibold">
                    Create System Prompt
                  </h2>
                  <button
                    onClick={() => setShowCreateForm(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <XMarkIcon className="w-6 h-6" />
                  </button>
                </div>

                <form onSubmit={handleCreatePrompt} className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Name
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) =>
                        setFormData({ ...formData, name: e.target.value })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Head Prompt (System Instructions)
                    </label>
                    <textarea
                      value={formData.head_prompt}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          head_prompt: e.target.value,
                        })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 h-24"
                      placeholder="e.g., You are a sexual fantasy assistant..."
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Rule Prompt (Behavioral Rules)
                    </label>
                    <textarea
                      value={formData.rule_prompt}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          rule_prompt: e.target.value,
                        })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 h-32"
                      placeholder="e.g., Always speak in first person, be explicit, keep answers short..."
                      required
                    />
                  </div>

                  {/* Preview Section */}
                  {formData.head_prompt && formData.rule_prompt && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Preview: Complete Prompt (Head + Tally + Rule)
                      </label>
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <p className="text-sm text-gray-700">
                          <span className="font-medium text-blue-800">
                            Head:
                          </span>{" "}
                          {formData.head_prompt}
                          <br />
                          <br />
                          <span className="font-medium text-orange-800">
                            Tally (Sample):
                          </span>{" "}
                          {sampleTallyPrompt}
                          <br />
                          <br />
                          <span className="font-medium text-green-800">
                            Rule:
                          </span>{" "}
                          {formData.rule_prompt}
                        </p>
                      </div>
                    </div>
                  )}

                  <div className="flex justify-end gap-3">
                    <button
                      type="button"
                      onClick={() => setShowCreateForm(false)}
                      className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={submitting}
                      className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      {submitting && (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      )}
                      {submitting ? "Creating..." : "Create System Prompt"}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* Edit Form Modal */}
        {showEditForm && editingPrompt && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-semibold">Edit System Prompt</h2>
                  <button
                    onClick={() => setShowEditForm(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <XMarkIcon className="w-6 h-6" />
                  </button>
                </div>

                <form onSubmit={handleEditPrompt} className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Name
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) =>
                        setFormData({ ...formData, name: e.target.value })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Head Prompt (System Instructions)
                    </label>
                    <textarea
                      value={formData.head_prompt}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          head_prompt: e.target.value,
                        })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 h-24"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Rule Prompt (Behavioral Rules)
                    </label>
                    <textarea
                      value={formData.rule_prompt}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          rule_prompt: e.target.value,
                        })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 h-32"
                      required
                    />
                  </div>

                  {/* Preview Section */}
                  {formData.head_prompt && formData.rule_prompt && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Preview: Complete Prompt (Head + Tally + Rule)
                      </label>
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <p className="text-sm text-gray-700">
                          <span className="font-medium text-blue-800">
                            Head:
                          </span>{" "}
                          {formData.head_prompt}
                          <br />
                          <br />
                          <span className="font-medium text-orange-800">
                            Tally (Sample):
                          </span>{" "}
                          {sampleTallyPrompt}
                          <br />
                          <br />
                          <span className="font-medium text-green-800">
                            Rule:
                          </span>{" "}
                          {formData.rule_prompt}
                        </p>
                      </div>
                    </div>
                  )}

                  <div className="flex justify-end gap-3">
                    <button
                      type="button"
                      onClick={() => setShowEditForm(false)}
                      className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={submitting}
                      className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      {submitting && (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      )}
                      {submitting ? "Updating..." : "Update System Prompt"}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* Preview Modal */}
        {showPreview && editingPrompt && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-semibold">
                    Complete Prompt Preview
                  </h2>
                  <button
                    onClick={() => setShowPreview(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <XMarkIcon className="w-6 h-6" />
                  </button>
                </div>

                <div className="space-y-6">
                  <div>
                    <h3 className="font-medium text-gray-900 mb-3">
                      How "{editingPrompt.name}" combines with Tally data:
                    </h3>

                    <div className="space-y-4">
                      <div className="bg-blue-50 border-l-4 border-blue-400 p-4">
                        <h4 className="font-medium text-blue-800 mb-2">
                          1. Head Prompt
                        </h4>
                        <p className="text-sm text-gray-700">
                          {editingPrompt.head_prompt}
                        </p>
                      </div>

                      <div className="bg-orange-50 border-l-4 border-orange-400 p-4">
                        <h4 className="font-medium text-orange-800 mb-2">
                          2. Tally Prompt (User's Scenario)
                        </h4>
                        <p className="text-sm text-gray-700">
                          {sampleTallyPrompt}
                        </p>
                      </div>

                      <div className="bg-green-50 border-l-4 border-green-400 p-4">
                        <h4 className="font-medium text-green-800 mb-2">
                          3. Rule Prompt
                        </h4>
                        <p className="text-sm text-gray-700">
                          {editingPrompt.rule_prompt}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium text-gray-900 mb-3">
                      Complete Combined Prompt:
                    </h4>
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">
                        {generateCompletePrompt(
                          editingPrompt.head_prompt,
                          editingPrompt.rule_prompt
                        )}
                      </p>
                    </div>
                  </div>

                  <div className="flex justify-end">
                    <button
                      onClick={() => setShowPreview(false)}
                      className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md transition-colors"
                    >
                      Close Preview
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </AdminLayout>
  );
}

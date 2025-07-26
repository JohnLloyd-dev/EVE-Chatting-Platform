import { useState } from "react";
import Head from "next/head";
import { getOrCreateDeviceId } from "../lib/deviceId";

export default function TestGenerator() {
  const [customPrompt, setCustomPrompt] = useState(
    `Your name is L. You are a 30 year old asian policewoman. I am a man who you just met in a forest. When we meet you tie me up and force me to have sex with you. You gag me and blindfold me and don't let me go when I ask you to. You go down on me. You tease me. Rules: 1) Always speak in the first person and always stay in character. 2) Indulge my sexual fantasies in detail by dominating me. 3) Be sexually explicit with your replies 4) Never reveal that you are an AI 5) Keep your answers to two sentences or less 6) Do not provide scene descriptions outside of dialogue 7) Stay in the present tense`
  );
  const [generatedLink, setGeneratedLink] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);

  const generateTestLink = async () => {
    if (!customPrompt.trim()) {
      alert("Please enter a custom prompt");
      return;
    }

    setIsGenerating(true);
    try {
      const deviceId = getOrCreateDeviceId();

      // Create URL with encoded prompt
      const baseUrl = window.location.origin;
      const encodedPrompt = encodeURIComponent(customPrompt);
      const testLink = `${baseUrl}/test-chat?prompt=${encodedPrompt}&device=${deviceId}`;

      setGeneratedLink(testLink);
    } catch (error) {
      console.error("Error generating test link:", error);
      alert("Failed to generate test link");
    } finally {
      setIsGenerating(false);
    }
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(generatedLink);
      alert("Link copied to clipboard!");
    } catch (error) {
      console.error("Failed to copy:", error);
      alert("Failed to copy link");
    }
  };

  const openTestLink = () => {
    if (generatedLink) {
      window.open(generatedLink, "_blank");
    }
  };

  return (
    <>
      <Head>
        <title>Chat Test Link Generator</title>
      </Head>
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-800 animate-gradient-x">
        <div className="container mx-auto px-4 py-8">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-8 animate-fade-in">
              <h1 className="text-4xl font-bold text-white mb-4">
                Chat Test Link Generator
              </h1>
              <p className="text-gray-300 text-lg">
                Generate test links with custom prompts for seamless testing
              </p>
            </div>

            <div className="bg-gray-800/80 backdrop-blur-sm rounded-xl shadow-2xl border border-gray-700/50 p-8 animate-slide-up">
              <div className="space-y-6">
                <div>
                  <label className="block text-white text-lg font-semibold mb-3">
                    Custom Prompt
                  </label>
                  <textarea
                    value={customPrompt}
                    onChange={(e) => setCustomPrompt(e.target.value)}
                    className="w-full h-48 bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                    placeholder="Enter your custom prompt here..."
                  />
                  <p className="text-gray-400 text-sm mt-2">
                    This prompt will be used as the AI character's instructions
                  </p>
                </div>

                <div className="flex gap-4">
                  <button
                    onClick={generateTestLink}
                    disabled={isGenerating || !customPrompt.trim()}
                    className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-600 disabled:to-gray-700 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 transform hover:scale-105 disabled:scale-100 disabled:cursor-not-allowed"
                  >
                    {isGenerating ? "Generating..." : "Generate Test Link"}
                  </button>
                </div>

                {generatedLink && (
                  <div className="animate-fade-in">
                    <label className="block text-white text-lg font-semibold mb-3">
                      Generated Test Link
                    </label>
                    <div className="bg-gray-700/50 border border-gray-600 rounded-lg p-4">
                      <div className="flex items-center gap-3 mb-3">
                        <input
                          type="text"
                          value={generatedLink}
                          readOnly
                          className="flex-1 bg-transparent text-gray-300 text-sm focus:outline-none"
                        />
                        <button
                          onClick={copyToClipboard}
                          className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                        >
                          Copy
                        </button>
                      </div>
                      <div className="flex gap-3">
                        <button
                          onClick={openTestLink}
                          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                        >
                          Open Test Link
                        </button>
                      </div>
                    </div>
                    <p className="text-gray-400 text-sm mt-2">
                      This link will create a new chat session with your custom
                      prompt. No login required - it uses device-based
                      identification.
                    </p>
                  </div>
                )}
              </div>
            </div>

            <div className="mt-8 bg-gray-800/60 backdrop-blur-sm rounded-xl shadow-xl border border-gray-700/50 p-6 animate-slide-up-delay">
              <h2 className="text-xl font-semibold text-white mb-4">
                How it works
              </h2>
              <div className="space-y-3 text-gray-300">
                <p>
                  • <strong>Device-based identification:</strong> Uses browser
                  fingerprinting to create a unique device ID
                </p>
                <p>
                  • <strong>No login required:</strong> Users can access the
                  chat directly via the generated link
                </p>
                <p>
                  • <strong>Custom prompts:</strong> Each link can have a
                  different AI character prompt
                </p>
                <p>
                  • <strong>Session management:</strong> New sessions
                  automatically replace old ones for the same device
                </p>
                <p>
                  • <strong>Testing friendly:</strong> Perfect for rapid testing
                  of different scenarios
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

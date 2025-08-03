import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Head from "next/head";

export default function DebugStart() {
  const router = useRouter();
  const [urlParams, setUrlParams] = useState<Record<string, string>>({});

  useEffect(() => {
    // Get all URL parameters
    const params = new URLSearchParams(window.location.search);
    const paramObj: Record<string, string> = {};

    params.forEach((value, key) => {
      paramObj[key] = value;
    });

    setUrlParams(paramObj);
    console.log("All URL parameters:", paramObj);
  }, []);

  return (
    <>
      <Head>
        <title>Debug Tally Redirect Parameters</title>
      </Head>
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-800 p-8 animate-gradient-x">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold text-white mb-8">
            Debug Tally Redirect Parameters
          </h1>

          <div className="bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 mb-6 border border-gray-700/50 animate-fade-in">
            <h2 className="text-xl font-semibold text-white mb-4">
              Current URL:
            </h2>
            <p className="text-gray-300 break-all">
              {typeof window !== "undefined"
                ? window.location.href
                : "Loading..."}
            </p>
          </div>

          <div className="bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 mb-6 border border-gray-700/50 animate-fade-in-delay">
            <h2 className="text-xl font-semibold text-white mb-4">
              URL Parameters:
            </h2>
            {Object.keys(urlParams).length === 0 ? (
              <p className="text-gray-300">No parameters found</p>
            ) : (
              <div className="space-y-2">
                {Object.entries(urlParams).map(([key, value]) => (
                  <div key={key} className="flex">
                    <span className="text-purple-300 font-mono w-32">
                      {key}:
                    </span>
                    <span className="text-gray-300 font-mono break-all">
                      {value}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50 animate-fade-in-delay-2">
            <h2 className="text-xl font-semibold text-white mb-4">
              Expected Tally Parameters:
            </h2>
            <div className="text-gray-300 space-y-2">
              <p>
                • <span className="text-purple-300">responseId</span> or{" "}
                <span className="text-purple-300">response_id</span>: The unique
                response ID from Tally
              </p>
              <p>
                • <span className="text-purple-300">respondentId</span> or{" "}
                <span className="text-purple-300">respondent_id</span>: The
                respondent ID from Tally
              </p>
            </div>
          </div>

          <div className="mt-8 space-x-4 animate-slide-up">
            <button
              onClick={() => router.push("/start")}
              className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 transform hover:scale-105"
            >
              Try /start with current parameters
            </button>
            <button
              onClick={() => router.push("/")}
              className="bg-gradient-to-r from-gray-600 to-gray-700 hover:from-gray-700 hover:to-gray-800 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 transform hover:scale-105"
            >
              Go to Home
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

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

    for (const [key, value] of params.entries()) {
      paramObj[key] = value;
    }

    setUrlParams(paramObj);
    console.log("All URL parameters:", paramObj);
  }, []);

  return (
    <>
      <Head>
        <title>Debug Tally Redirect Parameters</title>
      </Head>
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold text-white mb-8">
            Debug Tally Redirect Parameters
          </h1>

          <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold text-white mb-4">
              Current URL:
            </h2>
            <p className="text-gray-300 break-all">
              {typeof window !== "undefined"
                ? window.location.href
                : "Loading..."}
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold text-white mb-4">
              URL Parameters:
            </h2>
            {Object.keys(urlParams).length === 0 ? (
              <p className="text-gray-300">No parameters found</p>
            ) : (
              <div className="space-y-2">
                {Object.entries(urlParams).map(([key, value]) => (
                  <div key={key} className="flex">
                    <span className="text-blue-300 font-mono w-32">{key}:</span>
                    <span className="text-gray-300 font-mono break-all">
                      {value}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6">
            <h2 className="text-xl font-semibold text-white mb-4">
              Expected Tally Parameters:
            </h2>
            <div className="text-gray-300 space-y-2">
              <p>
                • <span className="text-blue-300">responseId</span> or{" "}
                <span className="text-blue-300">response_id</span>: The unique
                response ID from Tally
              </p>
              <p>
                • <span className="text-blue-300">respondentId</span> or{" "}
                <span className="text-blue-300">respondent_id</span>: The
                respondent ID from Tally
              </p>
            </div>
          </div>

          <div className="mt-8 space-x-4">
            <button
              onClick={() => router.push("/start")}
              className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded transition duration-200"
            >
              Try /start with current parameters
            </button>
            <button
              onClick={() => router.push("/")}
              className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded transition duration-200"
            >
              Go to Home
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

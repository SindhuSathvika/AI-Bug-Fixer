"use client";  // Add this line

import { useState } from "react";

export default function Home() {
  const [code, setCode] = useState("");
  const [response, setResponse] = useState("");

  const analyzeCode = async () => {
    const res = await fetch("http://127.0.0.1:8000/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code }),
    });
    const data = await res.json();
    setResponse(data.message);
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-900 text-white p-4">
      <h1 className="text-3xl font-bold mb-4">AI Bug Fixer</h1>
      <textarea
        className="w-96 h-40 p-2 bg-gray-800 border border-gray-600 rounded-lg"
        placeholder="Paste your code here..."
        value={code}
        onChange={(e) => setCode(e.target.value)}
      />
      <button
        className="mt-4 px-4 py-2 bg-blue-500 rounded-lg hover:bg-blue-600"
        onClick={analyzeCode}
      >
        Analyze Code
      </button>
      {response && <p className="mt-4 bg-gray-700 p-2 rounded-lg">{response}</p>}
    </div>
  );
}

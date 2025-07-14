// app/page.tsx
'use client';

import { useState } from 'react';

export default function Home() {
  const [prompt, setPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isLoading) return;

    setIsLoading(true);
    setResult('');
    setError('');

    try {
      const response = await fetch('/api/kramer', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt }),
      });

      const data = await response.json();

      if (!response.ok) {
        // Use the error message from the backend if available
        throw new Error(data.error || 'An unknown error occurred.');
      }

      setResult(data.answer);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-6 sm:p-12 bg-gray-900 text-white">
      <div className="z-10 w-full max-w-3xl items-center justify-between font-mono text-sm">
        <h1 className="text-4xl sm:text-5xl font-bold text-center text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500 mb-2">
          KRAMER
        </h1>
        <p className="text-center text-gray-400 mb-8">
          Knowledge-driven Recursive Analysis for Modular Evaluation and Response
        </p>

        <form onSubmit={handleSubmit}>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter a complex question... for example, 'Compare the economic impacts of the 2008 financial crisis and the COVID-19 pandemic on the US housing market.'"
            className="w-full p-4 border border-gray-600 bg-gray-800 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition text-white placeholder-gray-500"
            rows={5}
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !prompt.trim()}
            className="mt-4 w-full bg-blue-600 text-white font-semibold py-3 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-500 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? 'Processing...' : 'Submit'}
          </button>
        </form>

        {(result || error || isLoading) && (
          <div className="mt-8 w-full p-6 border border-gray-700 rounded-lg bg-gray-800 shadow-lg">
            {isLoading && (
                <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
                    <p className="ml-4 text-gray-300">Processing your request... This may take a moment.</p>
                </div>
            )}
            {error && (
              <div className="text-red-400">
                <p className='font-bold text-lg mb-2'>Error:</p>
                <p className="whitespace-pre-wrap">{error}</p>
              </div>
            )}
            {result && (
              <div className="text-gray-200">
                <p className='font-bold text-lg mb-2 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500'>Answer:</p>
                <p className="whitespace-pre-wrap leading-relaxed">{result}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
// app/page.tsx
'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';

export default function Home() {
  const [query, setQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [result, setResult] = useState<string>('');
  const [finalReport, setFinalReport] = useState<string>('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;

    setIsLoading(true);
    setResult('');
    setFinalReport('');

    try {
      const response = await fetch('/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Failed to get response reader');
      }

      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        if (chunk.startsWith('SYNTHESIS_CHUNK:')) {
            setFinalReport(prev => prev + chunk.replace('SYNTHESIS_CHUNK:', ''));
        } else {
            setResult(prev => prev + chunk);
        }
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'An unknown error occurred';
      setResult(prev => `${prev}\n\n**Error:** ${message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center bg-gray-900 text-white p-4 sm:p-12 md:p-24">
      <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm lg:flex">
        <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
          K.R.A.M.E.R
        </h1>
      </div>

      <div className="w-full max-w-5xl mt-12">
        <form onSubmit={handleSubmit}>
          <textarea
            className="w-full p-4 bg-gray-800 border border-gray-600 rounded-lg focus:ring-2 focus:ring-cyan-400 focus:outline-none transition-all"
            rows={4}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your complex query here..."
          />
          <button
            type="submit"
            disabled={isLoading}
            className="mt-4 w-full px-6 py-3 bg-cyan-600 text-white font-semibold rounded-lg hover:bg-cyan-700 disabled:bg-gray-700 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? 'Processing...' : 'Run KRAMER'}
          </button>
        </form>

        {(isLoading || result || finalReport) && (
          <div className="mt-8 w-full p-6 bg-gray-800 border border-gray-700 rounded-lg">
            {result && (
              <div>
                <h2 className="text-2xl font-semibold mb-4 text-gray-300">Execution Log</h2>
                <pre className="whitespace-pre-wrap bg-black p-4 rounded-md text-sm text-gray-400">{result}</pre>
              </div>
            )}
            {finalReport && (
                <div className="mt-6">
                    <h2 className="text-2xl font-semibold mb-4 text-cyan-400">Final Report</h2>
                    <article className="prose prose-invert max-w-none">
                        <ReactMarkdown>{finalReport}</ReactMarkdown>
                    </article>
                </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}

"use client";

import { useState, useRef, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { streamInvestigation, type AgentStep, type AgentAnswer } from "@/lib/api";

const PRESET_QUERIES = [
  "Why is Tower A delayed?",
  "Why is Building B delayed?",
  "Which vendors are high risk?",
];

function ToolIcon({ tool }: { tool: string }) {
  const icons: Record<string, string> = {
    get_project_status: "📋",
    get_material_shortages: "📦",
    get_delayed_shipments: "🚚",
    get_vendor_history: "🏭",
    get_inspection_issues: "🔍",
    get_graph_relationships: "🕸️",
    final_answer: "✅",
  };
  return <span>{icons[tool] ?? "⚙️"}</span>;
}

function StepCard({ step }: { step: AgentStep }) {
  const [expanded, setExpanded] = useState(false);
  const toolLabel = step.tool.replace(/^get_/, "").replace(/_/g, " ");

  return (
    <div className="border border-gray-800 rounded-lg overflow-hidden">
      <button
        className="w-full flex items-center gap-3 px-4 py-3 bg-gray-900 hover:bg-gray-800 transition-colors text-left"
        onClick={() => setExpanded(!expanded)}
      >
        <span className="text-gray-500 font-mono text-xs w-6">{step.step}</span>
        <ToolIcon tool={step.tool} />
        <span className="text-sm font-medium text-gray-200 flex-1 capitalize">{toolLabel}</span>
        {step.type === "tool_end" && (
          <span className="text-xs text-green-400">done</span>
        )}
        {step.type === "tool_start" && (
          <span className="text-xs text-yellow-400 animate-pulse">running…</span>
        )}
        <span className="text-gray-600 text-xs">{expanded ? "▲" : "▼"}</span>
      </button>
      {expanded && step.result !== undefined && (
        <div className="px-4 py-3 bg-gray-950 border-t border-gray-800">
          <pre className="text-xs text-gray-400 whitespace-pre-wrap overflow-auto max-h-48">
            {typeof step.result === "string"
              ? step.result
              : JSON.stringify(step.result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

function AnswerCard({ answer }: { answer: AgentAnswer }) {
  const confidence = Math.round(answer.confidence * 100);
  return (
    <div className="border border-orange-800 rounded-lg bg-orange-950/20 overflow-hidden">
      <div className="px-5 py-4 border-b border-orange-900">
        <div className="flex items-center justify-between">
          <span className="text-orange-400 text-sm font-semibold uppercase tracking-wide">Root Cause Analysis</span>
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-500">Impact: <span className="text-red-400 font-mono">{answer.impact_days}d</span></span>
            <span className="text-xs text-gray-500">Confidence: <span className="text-green-400 font-mono">{confidence}%</span></span>
          </div>
        </div>
      </div>
      <div className="p-5 space-y-4">
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Primary Cause</p>
          <p className="text-white text-sm leading-relaxed">{answer.primary_cause}</p>
        </div>
        {answer.secondary_cause && (
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Secondary Cause</p>
            <p className="text-gray-300 text-sm leading-relaxed">{answer.secondary_cause}</p>
          </div>
        )}
        {answer.evidence?.length > 0 && (
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">Evidence</p>
            <div className="space-y-1">
              {answer.evidence.map((e, i) => (
                <div key={i} className="text-xs text-gray-400 bg-gray-900 rounded px-3 py-2 border border-gray-800">
                  {e.description ?? e.data_point ?? JSON.stringify(e)}
                </div>
              ))}
            </div>
          </div>
        )}
        {answer.recommendation && (
          <div className="bg-orange-900/30 border border-orange-800 rounded px-4 py-3">
            <p className="text-xs text-orange-400 uppercase tracking-wide mb-1">Recommended Action</p>
            <p className="text-orange-200 text-sm">{answer.recommendation}</p>
          </div>
        )}
      </div>
    </div>
  );
}

function AgentChat() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q") ?? "";
  const [query, setQuery] = useState(initialQuery);
  const [steps, setSteps] = useState<AgentStep[]>([]);
  const [answer, setAnswer] = useState<AgentAnswer | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const cancelRef = useRef<(() => void) | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (initialQuery) {
      handleSubmit(initialQuery);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [steps, answer]);

  function handleSubmit(q?: string) {
    const text = (q ?? query).trim();
    if (!text || running) return;
    setSteps([]);
    setAnswer(null);
    setError(null);
    setRunning(true);

    cancelRef.current = streamInvestigation(
      text,
      (step) => {
        setSteps((prev) => {
          const existing = prev.findIndex((s) => s.step === step.step && s.type === "tool_start");
          if (step.type === "tool_end" && existing >= 0) {
            return prev.map((s, i) => i === existing ? { ...s, ...step } : s);
          }
          return [...prev.filter((s) => !(s.step === step.step && s.type === "tool_start")), step];
        });
      },
      (ans) => {
        setAnswer(ans);
        setRunning(false);
      },
      (err) => {
        setError(err);
        setRunning(false);
      }
    );
  }

  function handleStop() {
    cancelRef.current?.();
    setRunning(false);
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] gap-4">
      <div>
        <h1 className="text-2xl font-bold text-white">AI Investigation Agent</h1>
        <p className="text-gray-400 text-sm mt-1">
          Ask about any project. The agent queries PostgreSQL, Neo4j, and Qdrant to find the root cause.
        </p>
      </div>

      {/* Preset queries */}
      <div className="flex gap-2 flex-wrap">
        {PRESET_QUERIES.map((q) => (
          <button
            key={q}
            onClick={() => { setQuery(q); handleSubmit(q); }}
            disabled={running}
            className="text-xs px-3 py-1.5 rounded-full border border-gray-700 text-gray-400 hover:border-orange-500 hover:text-orange-400 disabled:opacity-40 transition-colors"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Trace area */}
      <div className="flex-1 overflow-y-auto space-y-2 min-h-0">
        {steps.length === 0 && !running && !error && (
          <div className="flex items-center justify-center h-full text-gray-600">
            <p className="text-sm">Ask a question to start the investigation</p>
          </div>
        )}
        {steps.map((step, i) => (
          <StepCard key={i} step={step} />
        ))}
        {running && steps.length > 0 && (
          <div className="flex items-center gap-2 px-4 py-3 text-yellow-400 text-sm">
            <span className="animate-spin">⚙</span>
            <span>Investigating…</span>
          </div>
        )}
        {error && (
          <div className="border border-red-800 rounded-lg bg-red-950/20 px-4 py-3 text-red-400 text-sm">
            Error: {error}
          </div>
        )}
        {answer && <AnswerCard answer={answer} />}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          placeholder='e.g. "Why is Tower A delayed?"'
          disabled={running}
          className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-orange-500 disabled:opacity-60"
        />
        {running ? (
          <button
            onClick={handleStop}
            className="px-5 py-3 rounded-lg bg-gray-800 hover:bg-gray-700 text-white text-sm transition-colors"
          >
            Stop
          </button>
        ) : (
          <button
            onClick={() => handleSubmit()}
            disabled={!query.trim()}
            className="px-5 py-3 rounded-lg bg-orange-500 hover:bg-orange-400 disabled:opacity-40 text-white text-sm font-medium transition-colors"
          >
            Investigate
          </button>
        )}
      </div>
    </div>
  );
}

export default function AgentPage() {
  return (
    <Suspense fallback={<div className="text-gray-500 py-20 text-center">Loading…</div>}>
      <AgentChat />
    </Suspense>
  );
}

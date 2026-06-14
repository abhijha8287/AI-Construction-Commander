const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchDashboard() {
  const res = await fetch(`${API}/api/dashboard`);
  if (!res.ok) throw new Error("Failed to fetch dashboard");
  return res.json();
}

export async function fetchProjects() {
  const res = await fetch(`${API}/api/projects`);
  if (!res.ok) throw new Error("Failed to fetch projects");
  return res.json();
}

export async function fetchProject(id: string) {
  const res = await fetch(`${API}/api/projects/${id}`);
  if (!res.ok) throw new Error("Failed to fetch project");
  return res.json();
}

export async function fetchVendors() {
  const res = await fetch(`${API}/api/vendors`);
  if (!res.ok) throw new Error("Failed to fetch vendors");
  return res.json();
}

export function streamInvestigation(
  query: string,
  onStep: (step: AgentStep) => void,
  onDone: (answer: AgentAnswer) => void,
  onError: (err: string) => void
): () => void {
  const controller = new AbortController();

  fetch(`${API}/api/agent/investigate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
    signal: controller.signal,
  }).then(async (res) => {
    if (!res.ok) {
      onError(`HTTP ${res.status}`);
      return;
    }
    const reader = res.body?.getReader();
    if (!reader) { onError("No response body"); return; }
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        try {
          const data = JSON.parse(line.slice(6));
          if (data.done && data.answer) {
            onDone(data.answer);
          } else if (!data.done) {
            onStep(data);
          }
        } catch { /* ignore malformed */ }
      }
    }
  }).catch((err) => {
    if (err.name !== "AbortError") onError(String(err));
  });

  return () => controller.abort();
}

export interface AgentStep {
  step: number;
  type: "tool_start" | "tool_end" | "error";
  tool: string;
  input?: Record<string, unknown>;
  result?: unknown;
  done: boolean;
}

export interface AgentAnswer {
  primary_cause: string;
  secondary_cause: string | null;
  evidence: Array<{ type?: string; description?: string; data_point?: string }>;
  impact_days: number;
  confidence: number;
  recommendation: string;
}

import Link from "next/link";
import { fetchDashboard, fetchProjects } from "@/lib/api";

function RiskBadge({ score }: { score: number }) {
  const color =
    score >= 70 ? "bg-red-900 text-red-300 border-red-700" :
    score >= 40 ? "bg-yellow-900 text-yellow-300 border-yellow-700" :
    "bg-green-900 text-green-300 border-green-700";
  return (
    <span className={`text-xs font-mono px-2 py-0.5 rounded border ${color}`}>
      {score.toFixed(0)}
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  const color =
    status === "delayed" ? "bg-red-900 text-red-300" :
    status === "active" ? "bg-blue-900 text-blue-300" :
    "bg-gray-800 text-gray-300";
  return (
    <span className={`text-xs px-2 py-0.5 rounded capitalize ${color}`}>{status}</span>
  );
}

export default async function DashboardPage() {
  let dashboard: Awaited<ReturnType<typeof fetchDashboard>>;
  let projects: Awaited<ReturnType<typeof fetchProjects>>;

  try {
    [dashboard, projects] = await Promise.all([fetchDashboard(), fetchProjects()]);
  } catch {
    return (
      <div className="text-center py-20 text-gray-500">
        <p className="text-lg">Cannot connect to API</p>
        <p className="text-sm mt-2">Make sure <code className="text-orange-400">docker-compose up</code> is running</p>
      </div>
    );
  }

  const s = dashboard.summary;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Command Center</h1>
        <p className="text-gray-400 text-sm mt-1">Real-time project intelligence</p>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Total Projects", value: s.total_projects, sub: "all time" },
          { label: "Delayed", value: s.delayed_projects, sub: "need attention", alert: s.delayed_projects > 0 },
          { label: "Delayed Shipments", value: s.delayed_shipments, sub: "in transit", alert: s.delayed_shipments > 0 },
          { label: "Pending POs", value: s.pending_pos, sub: "awaiting approval", alert: s.pending_pos > 0 },
        ].map((m) => (
          <div
            key={m.label}
            className={`rounded-lg border p-4 ${m.alert ? "border-red-800 bg-red-950/30" : "border-gray-800 bg-gray-900"}`}
          >
            <p className="text-xs text-gray-500 uppercase tracking-wide">{m.label}</p>
            <p className={`text-3xl font-bold mt-1 ${m.alert ? "text-red-400" : "text-white"}`}>{m.value}</p>
            <p className="text-xs text-gray-600 mt-1">{m.sub}</p>
          </div>
        ))}
      </div>

      {/* Projects Table */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Projects</h2>
          <Link
            href="/agent"
            className="text-sm bg-orange-500 hover:bg-orange-400 text-white px-4 py-2 rounded-lg transition-colors"
          >
            Investigate with AI →
          </Link>
        </div>
        <div className="rounded-lg border border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-900 border-b border-gray-800">
              <tr>
                {["Project", "Status", "Location", "Shipments", "Pending POs", "Risk"].map((h) => (
                  <th key={h} className="text-left px-4 py-3 text-xs text-gray-500 uppercase tracking-wide font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {projects.map((p: {
                id: string; name: string; status: string; location: string;
                delayed_shipments: number; total_shipments: number;
                pending_pos: number; total_pos: number; risk_score: number;
              }) => (
                <tr key={p.id} className="hover:bg-gray-900/50 transition-colors">
                  <td className="px-4 py-3">
                    <Link href={`/projects/${p.id}`} className="text-orange-400 hover:text-orange-300 font-medium">
                      {p.name}
                    </Link>
                  </td>
                  <td className="px-4 py-3"><StatusBadge status={p.status} /></td>
                  <td className="px-4 py-3 text-gray-400">{p.location}</td>
                  <td className="px-4 py-3 text-gray-300">
                    {p.delayed_shipments > 0
                      ? <span className="text-red-400">{p.delayed_shipments} delayed / {p.total_shipments}</span>
                      : <span className="text-gray-500">{p.total_shipments} on track</span>
                    }
                  </td>
                  <td className="px-4 py-3 text-gray-300">
                    {p.pending_pos > 0
                      ? <span className="text-yellow-400">{p.pending_pos} pending</span>
                      : <span className="text-gray-500">—</span>
                    }
                  </td>
                  <td className="px-4 py-3"><RiskBadge score={p.risk_score} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

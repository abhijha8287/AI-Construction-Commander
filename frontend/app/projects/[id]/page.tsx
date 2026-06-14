import Link from "next/link";
import { fetchProject } from "@/lib/api";
import { notFound } from "next/navigation";

function StatusBadge({ status }: { status: string }) {
  const color =
    status === "delayed" ? "bg-red-900 text-red-300" :
    status === "delivered" ? "bg-green-900 text-green-300" :
    status === "pending" ? "bg-yellow-900 text-yellow-300" :
    status === "approved" ? "bg-green-900 text-green-300" :
    status === "rejected" ? "bg-red-900 text-red-300" :
    "bg-gray-800 text-gray-300";
  return <span className={`text-xs px-2 py-0.5 rounded capitalize ${color}`}>{status}</span>;
}

export default async function ProjectPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let project: Awaited<ReturnType<typeof fetchProject>>;
  try {
    project = await fetchProject(id);
  } catch {
    notFound();
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <Link href="/" className="text-gray-500 hover:text-gray-300 text-sm">← Dashboard</Link>
          </div>
          <h1 className="text-2xl font-bold text-white">{project.name}</h1>
          <p className="text-gray-400 text-sm mt-1">{project.location} · {project.description}</p>
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge status={project.status} />
          <Link
            href={`/agent?q=${encodeURIComponent(`Why is ${project.name} delayed?`)}`}
            className="bg-orange-500 hover:bg-orange-400 text-white text-sm px-4 py-2 rounded-lg transition-colors"
          >
            Investigate with AI →
          </Link>
        </div>
      </div>

      {/* Timeline */}
      <div className="rounded-lg border border-gray-800 bg-gray-900 p-6">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-4">Timeline</h2>
        <div className="grid grid-cols-3 gap-6 text-sm">
          <div>
            <p className="text-gray-500">Planned Start</p>
            <p className="text-white font-mono mt-1">{project.planned_start_date ?? "—"}</p>
          </div>
          <div>
            <p className="text-gray-500">Planned End</p>
            <p className="text-white font-mono mt-1">{project.planned_end_date ?? "—"}</p>
          </div>
          <div>
            <p className="text-gray-500">Budget</p>
            <p className="text-white font-mono mt-1">₹{(project.budget / 1_000_000).toFixed(1)}M</p>
          </div>
        </div>
      </div>

      {/* Materials */}
      {project.materials?.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-white mb-3">Materials</h2>
          <div className="rounded-lg border border-gray-800 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-900 border-b border-gray-800">
                <tr>
                  {["Material", "Category", "Unit", "Planned", "Actual", "Gap"].map(h => (
                    <th key={h} className="text-left px-4 py-3 text-xs text-gray-500 uppercase">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {project.materials.map((m: {
                  name: string; category: string; unit: string;
                  planned_quantity: number; actual_quantity: number;
                }) => {
                  const gap = m.planned_quantity - m.actual_quantity;
                  return (
                    <tr key={m.name} className="hover:bg-gray-900/50">
                      <td className="px-4 py-3 font-medium text-white">{m.name}</td>
                      <td className="px-4 py-3 text-gray-400 capitalize">{m.category}</td>
                      <td className="px-4 py-3 text-gray-400">{m.unit}</td>
                      <td className="px-4 py-3 text-gray-300">{m.planned_quantity}</td>
                      <td className="px-4 py-3 text-gray-300">{m.actual_quantity}</td>
                      <td className="px-4 py-3">
                        {gap > 0
                          ? <span className="text-red-400 font-mono">−{gap} {m.unit}</span>
                          : <span className="text-green-400">✓</span>
                        }
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Shipments */}
      {project.shipments?.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-white mb-3">Shipments</h2>
          <div className="rounded-lg border border-gray-800 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-900 border-b border-gray-800">
                <tr>
                  {["Shipment", "Vendor", "Material", "Status", "Planned", "Actual", "Delay"].map(h => (
                    <th key={h} className="text-left px-4 py-3 text-xs text-gray-500 uppercase">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {project.shipments.map((s: {
                  shipment_number: string; vendor: string; material: string; status: string;
                  planned_delivery: string; actual_delivery: string; delay_days: number;
                }) => (
                  <tr key={s.shipment_number} className="hover:bg-gray-900/50">
                    <td className="px-4 py-3 font-mono text-orange-400">{s.shipment_number}</td>
                    <td className="px-4 py-3 text-gray-300">{s.vendor}</td>
                    <td className="px-4 py-3 text-gray-300">{s.material}</td>
                    <td className="px-4 py-3"><StatusBadge status={s.status} /></td>
                    <td className="px-4 py-3 font-mono text-gray-400 text-xs">{s.planned_delivery}</td>
                    <td className="px-4 py-3 font-mono text-gray-400 text-xs">{s.actual_delivery ?? "—"}</td>
                    <td className="px-4 py-3">
                      {s.delay_days > 0
                        ? <span className="text-red-400 font-mono">+{s.delay_days}d</span>
                        : <span className="text-green-400">—</span>
                      }
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Purchase Orders */}
      {project.purchase_orders?.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-white mb-3">Purchase Orders</h2>
          <div className="rounded-lg border border-gray-800 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-900 border-b border-gray-800">
                <tr>
                  {["PO Number", "Vendor", "Material", "Value", "Expected", "Status"].map(h => (
                    <th key={h} className="text-left px-4 py-3 text-xs text-gray-500 uppercase">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {project.purchase_orders.map((po: {
                  po_number: string; vendor: string; material: string;
                  total_price: number; expected_delivery: string; approval_status: string;
                }) => (
                  <tr key={po.po_number} className="hover:bg-gray-900/50">
                    <td className="px-4 py-3 font-mono text-gray-300">{po.po_number}</td>
                    <td className="px-4 py-3 text-gray-300">{po.vendor}</td>
                    <td className="px-4 py-3 text-gray-300">{po.material}</td>
                    <td className="px-4 py-3 text-gray-400 font-mono">₹{(po.total_price / 1000).toFixed(0)}K</td>
                    <td className="px-4 py-3 font-mono text-gray-400 text-xs">{po.expected_delivery}</td>
                    <td className="px-4 py-3"><StatusBadge status={po.approval_status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* AI Analyses */}
      {project.ai_analyses?.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-white mb-3">AI Analyses</h2>
          <div className="space-y-3">
            {project.ai_analyses.map((a: {
              analysis_type: string; risk_score: number; summary: string; recommendation: string;
            }, i: number) => (
              <div key={i} className="rounded-lg border border-gray-800 bg-gray-900 p-5">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">
                    {a.analysis_type.replace(/_/g, " ")}
                  </span>
                  <span className={`text-sm font-mono font-bold ${a.risk_score >= 80 ? "text-red-400" : a.risk_score >= 50 ? "text-yellow-400" : "text-green-400"}`}>
                    Risk {a.risk_score.toFixed(0)}
                  </span>
                </div>
                <p className="text-sm text-gray-200 mb-2">{a.summary}</p>
                {a.recommendation && (
                  <p className="text-xs text-orange-300 bg-orange-950/30 border border-orange-900 rounded px-3 py-2">
                    → {a.recommendation}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

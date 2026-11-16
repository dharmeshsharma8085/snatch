
import {
  Shield,
  LayoutDashboard,
  Smartphone,
  Activity,
  MapPin,
  FileText,
  Settings,
  Bell,
  Search,
  Battery,
  Wifi,
  ShieldCheck,
  AlertTriangle,
  ArrowUpRight,
  CircleDot,
} from "lucide-react";

const agents = [
  { name: "Risk Intelligence", detail: "Analyzing device signals", status: "Active", icon: Activity },
  { name: "Battery Guardian", detail: "Monitoring battery health", status: "Ready", icon: Battery },
  { name: "Location Intelligence", detail: "Location services", status: "Ready", icon: MapPin },
  { name: "Evidence Manager", detail: "Evidence storage", status: "Ready", icon: FileText },
];

function App() {
  return (
    <div className="min-h-screen bg-[#080b12] text-slate-100">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-white/10 bg-[#0c111b] p-6 lg:block">
        <div className="mb-12 flex items-center gap-3">
          <div className="rounded-xl bg-blue-500/15 p-2 text-blue-400">
            <Shield size={25} />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-widest">SNATCH</h1>
            <p className="text-[10px] tracking-[3px] text-slate-500">DEVICE SECURITY</p>
          </div>
        </div>

        <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-slate-500">Workspace</p>

        <nav className="space-y-2">
          {[
            [LayoutDashboard, "Dashboard", true],
            [Smartphone, "My Devices"],
            [Activity, "Incidents"],
            [MapPin, "Location"],
            [FileText, "Evidence"],
          ].map(([Icon, label, active]) => (
            <div key={label} className={`flex items-center gap-3 rounded-xl px-4 py-3 text-sm ${active ? "bg-blue-500/15 text-blue-400" : "text-slate-400 hover:bg-white/5"}`}>
              <Icon size={18} />
              {label}
            </div>
          ))}
        </nav>

        <div className="absolute bottom-6 left-6 right-6">
          <div className="rounded-xl border border-white/10 p-4">
            <Settings size={18} className="mb-3 text-slate-400" />
            <p className="text-sm font-medium">System Settings</p>
            <p className="mt-1 text-xs text-slate-500">Manage your protection</p>
          </div>
        </div>
      </aside>

      <main className="lg:ml-64">
        <header className="flex items-center justify-between border-b border-white/10 px-5 py-5 md:px-10">
          <div>
            <p className="text-sm text-slate-500">Workspace / Overview</p>
            <h2 className="mt-1 text-2xl font-bold">Security Dashboard</h2>
          </div>
          <div className="flex items-center gap-4">
            <button className="rounded-xl border border-white/10 p-3 text-slate-400">
              <Bell size={19} />
            </button>
            <div className="hidden items-center gap-3 sm:flex">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-500/20 font-bold text-blue-400">D</div>
              <div>
                <p className="text-sm font-medium">Device Owner</p>
                <p className="text-xs text-slate-500">Personal account</p>
              </div>
            </div>
          </div>
        </header>

        <section className="space-y-8 p-5 md:p-10">
          <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
            <div>
              <h3 className="text-lg font-semibold">Welcome back</h3>
              <p className="mt-1 text-sm text-slate-500">Here's your device security overview.</p>
            </div>
            <div className="flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-4 py-2 text-xs text-emerald-400">
              <CircleDot size={13} /> Dashboard preview
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {[
              { label: "Device Status", value: "Protected", note: "Preview data", icon: Smartphone, color: "text-emerald-400" },
              { label: "Risk Score", value: "12 / 100", note: "Illustrative score", icon: ShieldCheck, color: "text-blue-400" },
              { label: "Active Incidents", value: "00", note: "Preview data", icon: AlertTriangle, color: "text-amber-400" },
              { label: "Connectivity", value: "Online", note: "Illustrative status", icon: Wifi, color: "text-violet-400" },
            ].map((item) => (
              <div key={item.label} className="rounded-2xl border border-white/10 bg-[#101722] p-5">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-slate-400">{item.label}</p>
                  <item.icon size={19} className={item.color} />
                </div>
                <h3 className="mt-5 text-2xl font-bold">{item.value}</h3>
                <p className="mt-2 text-xs text-slate-500">{item.note}</p>
              </div>
            ))}
          </div>

          <div className="grid gap-6 xl:grid-cols-3">
            <div className="rounded-2xl border border-white/10 bg-[#101722] p-6 xl:col-span-2">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold">AI Agent Activity</h3>
                  <p className="mt-1 text-xs text-slate-500">SNATCH multi-agent workflow overview</p>
                </div>
                <Activity className="text-blue-400" size={20} />
              </div>

              <div className="mt-6 space-y-3">
                {agents.map((agent) => (
                  <div key={agent.name} className="flex items-center justify-between rounded-xl border border-white/5 bg-white/[0.02] p-4">
                    <div className="flex items-center gap-3">
                      <div className="rounded-lg bg-blue-500/10 p-2 text-blue-400">
                        <agent.icon size={19} />
                      </div>
                      <div>
                        <p className="text-sm font-medium">{agent.name}</p>
                        <p className="mt-1 text-xs text-slate-500">{agent.detail}</p>
                      </div>
                    </div>
                    <span className="text-xs text-emerald-400">{agent.status}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-2xl border border-white/10 bg-[#101722] p-6">
              <h3 className="font-semibold">Security Overview</h3>
              <p className="mt-1 text-xs text-slate-500">Illustrative risk assessment</p>
              <div className="my-8 flex flex-col items-center">
                <div className="flex h-36 w-36 flex-col items-center justify-center rounded-full border-[10px] border-emerald-500/30">
                  <span className="text-4xl font-bold">12</span>
                  <span className="text-xs text-slate-500">out of 100</span>
                </div>
                <span className="mt-4 rounded-full bg-emerald-500/10 px-4 py-2 text-xs text-emerald-400">Normal · Demo only</span>
              </div>
              <div className="rounded-xl bg-white/[0.03] p-4">
                <p className="text-sm font-medium">Recommended action</p>
                <p className="mt-2 text-xs leading-5 text-slate-400">Continue monitoring device signals. This is sample dashboard data, not a live assessment.</p>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-[#101722] p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold">Recent Activity</h3>
                <p className="mt-1 text-xs text-slate-500">Your latest security events</p>
              </div>
              <Search size={19} className="text-slate-500" />
            </div>
            <div className="mt-8 py-8 text-center">
              <div className="mx-auto mb-3 w-fit rounded-full bg-white/5 p-4 text-slate-500">
                <Activity size={24} />
              </div>
              <p className="text-sm font-medium">No activity to display</p>
              <p className="mt-2 text-xs text-slate-500">Connect the backend to load real events.</p>
            </div>
          </div>

          <footer className="flex flex-col justify-between gap-2 border-t border-white/10 pt-6 text-xs text-slate-600 sm:flex-row">
            <span>SNATCH · Smartphone Protection Platform</span>
            <span>Dashboard UI Preview</span>
          </footer>
        </section>
      </main>
    </div>
  );
}

export default App;

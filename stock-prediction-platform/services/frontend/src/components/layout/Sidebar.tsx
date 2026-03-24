import { NavLink } from "react-router-dom";
import { useHealthCheck } from "@/api";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: "📊" },
  { to: "/models", label: "Models", icon: "🧠" },
  { to: "/forecasts", label: "Forecasts", icon: "📈" },
  { to: "/drift", label: "Drift", icon: "⚡" },
  { to: "/backtest", label: "Backtest", icon: "🔬" },
];

interface SidebarProps {
  onClose: () => void;
}

export default function Sidebar({ onClose }: SidebarProps) {
  const { data: health } = useHealthCheck();
  const apiOnline = health?.status === "healthy";

  return (
    <div className="flex h-full flex-col">
      {/* Brand */}
      <div className="flex h-14 items-center border-b border-border px-4">
        <span className="text-lg font-bold text-accent">◆</span>
        <span className="ml-2 text-lg font-semibold text-text-primary">
          Stock Prediction
        </span>
        {/* Mobile close */}
        <button
          onClick={onClose}
          className="ml-auto text-text-secondary hover:text-text-primary lg:hidden"
          aria-label="Close sidebar"
        >
          ✕
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            onClick={onClose}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                isActive
                  ? "border-l-2 border-accent bg-bg-card text-accent"
                  : "text-text-secondary hover:bg-bg-card/50 hover:text-text-primary"
              }`
            }
          >
            <span className="text-base">{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>

      {/* API status */}
      <div className="border-t border-border px-4 py-3">
        <div className="flex items-center gap-2 text-xs text-text-secondary">
          <span
            className={`inline-block h-2 w-2 rounded-full ${
              apiOnline ? "bg-profit" : "bg-loss"
            }`}
          />
          API {apiOnline ? "Connected" : "Offline"}
        </div>
      </div>
    </div>
  );
}

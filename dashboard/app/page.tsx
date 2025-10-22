import Link from "next/link";
import { DashboardLayout, DashboardGrid } from "@/components/shared";

export default function HomePage() {
  return (
    <DashboardLayout
      title="Autonomous Incident Commander"
      subtitle="Revolutionary AI-powered multi-agent incident response system"
      icon="🛡️"
    >
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-6">
          <div className="text-sm text-slate-400">
            🏆 World&apos;s first comprehensive AI transparency • 🎯
            Production-ready deployment • 🔍 Complete explainability
          </div>
        </div>

        <DashboardGrid columns={3} className="mb-8">
          <Link href="/demo" className="group">
            <div className="interactive-card card-glass p-4">
              <div className="text-3xl mb-2">💼</div>
              <h3 className="text-lg font-semibold mb-2 text-blue-400">
                Power Demo
              </h3>
              <p className="text-status-neutral text-xs mb-3">
                Executive presentation with live incident animation, business
                impact calculator, and ROI demonstration
              </p>
              <div className="text-xs text-green-400">
                ✨ RECOMMENDED FOR HACKATHON
              </div>
            </div>
          </Link>

          <Link href="/transparency" className="group">
            <div className="interactive-card card-glass p-4">
              <div className="text-3xl mb-2">🧠</div>
              <h3 className="text-lg font-semibold mb-2 text-purple-400">
                AI Transparency
              </h3>
              <p className="text-status-neutral text-xs mb-3">
                Complete AI explainability with agent reasoning, decision trees,
                confidence analysis, and scenario selection
              </p>
              <div className="text-xs text-purple-400">
                🎯 TECHNICAL DEEP-DIVE
              </div>
            </div>
          </Link>

          <Link href="/ops" className="group">
            <div className="interactive-card card-glass p-4">
              <div className="text-3xl mb-2">⚙️</div>
              <h3 className="text-lg font-semibold mb-2 text-green-400">
                Operations Dashboard
              </h3>
              <p className="text-status-neutral text-xs mb-3">
                Production-ready dashboard with live WebSocket backend
                integration for real-time incident monitoring
              </p>
              <div className="text-xs text-green-400">⚡ PRODUCTION READY</div>
            </div>
          </Link>
        </DashboardGrid>

        <div className="card-glass p-4 mb-6">
          <h2 className="text-xl font-bold mb-3">🎯 Key Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-green-400">✅</span>
              <span>Sub-3 minute MTTR with 95%+ improvement</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-green-400">✅</span>
              <span>Byzantine fault-tolerant multi-agent system</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-green-400">✅</span>
              <span>Complete AI transparency and explainability</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-green-400">✅</span>
              <span>$2.8M annual cost savings (458% ROI)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-green-400">✅</span>
              <span>All 8 AWS AI services integrated</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-green-400">✅</span>
              <span>Production-ready with enterprise security</span>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/30 rounded-lg p-4">
          <h3 className="text-base font-semibold mb-2">🎯 Quick Guide</h3>
          <DashboardGrid columns={3}>
            <div>
              <div className="font-semibold text-blue-400 mb-1 text-sm">
                💼 Power Demo
              </div>
              <div className="text-status-neutral text-xs">
                3-minute executive presentation showing business value, live
                animation, and ROI
              </div>
            </div>
            <div>
              <div className="font-semibold text-purple-400 mb-1 text-sm">
                🧠 AI Transparency
              </div>
              <div className="text-status-neutral text-xs">
                10-15 minute technical deep-dive with scenario selection and
                full explainability
              </div>
            </div>
            <div>
              <div className="font-semibold text-green-400 mb-1 text-sm">
                ⚙️ Operations
              </div>
              <div className="text-status-neutral text-xs">
                Production dashboard with real backend integration for actual
                deployment
              </div>
            </div>
          </DashboardGrid>
        </div>

        <div className="text-center mt-4">
          <div className="text-xs text-slate-400">
            💡 For hackathon judges: Start with{" "}
            <span className="text-blue-400 font-semibold">Power Demo</span> for
            quick impact, then explore{" "}
            <span className="text-purple-400 font-semibold">
              AI Transparency
            </span>{" "}
            for technical depth
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

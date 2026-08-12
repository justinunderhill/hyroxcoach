import { CoachInsightData, CoachStatus } from "@/lib/coach";

const STATUS_LABELS: Record<CoachStatus, string> = {
  on_track: "On track",
  mixed: "Mixed",
  needs_attention: "Needs attention",
  insufficient_data: "Not enough data yet",
};

const STATUS_STYLES: Record<CoachStatus, string> = {
  on_track: "bg-[#f8ffe4] text-[#567118]",
  mixed: "bg-amber-50 text-amber-800",
  needs_attention: "bg-rose-50 text-rose-800",
  insufficient_data: "bg-stone-100 text-stone-500",
};

const PRIORITY_LABELS: Record<string, string> = { low: "Low", medium: "Medium", high: "High" };
const HORIZON_LABELS: Record<string, string> = {
  next_session: "Next session",
  this_week: "This week",
  next_2_weeks: "Next 2 weeks",
};

export function CoachInsightCard({ insight }: { insight: CoachInsightData }) {
  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm leading-6 text-stone-700">{insight.summary}</p>
        <span
          className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ${STATUS_STYLES[insight.status]}`}
        >
          {STATUS_LABELS[insight.status]}
        </span>
      </div>

      {insight.wins.length > 0 ? (
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-stone-400">Wins</p>
          <ul className="mt-2 space-y-2">
            {insight.wins.map((win) => (
              <li className="rounded-xl bg-[#f8ffe4] px-3 py-2 text-sm text-[#263711]" key={win.title}>
                <p className="font-semibold">{win.title}</p>
                <p className="mt-0.5 text-xs text-[#567118]">{win.evidence}</p>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {insight.gaps.length > 0 ? (
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-stone-400">Gaps</p>
          <ul className="mt-2 space-y-2">
            {insight.gaps.map((gap) => (
              <li className="rounded-xl bg-amber-50 px-3 py-2 text-sm text-amber-900" key={gap.title}>
                <div className="flex items-center justify-between gap-2">
                  <p className="font-semibold">{gap.title}</p>
                  <span className="text-[10px] font-semibold uppercase tracking-wide text-amber-700">
                    {PRIORITY_LABELS[gap.priority] ?? gap.priority}
                  </span>
                </div>
                <p className="mt-0.5 text-xs text-amber-800">{gap.evidence}</p>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {insight.recommendations.length > 0 ? (
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-stone-400">Next up</p>
          <ul className="mt-2 space-y-2">
            {insight.recommendations.map((rec) => (
              <li className="rounded-xl border border-stone-200 bg-white px-3 py-2 text-sm text-stone-700" key={rec.action}>
                <div className="flex items-center justify-between gap-2">
                  <p className="font-semibold">{rec.action}</p>
                  <span className="text-[10px] font-semibold uppercase tracking-wide text-stone-400">
                    {HORIZON_LABELS[rec.time_horizon] ?? rec.time_horizon}
                  </span>
                </div>
                <p className="mt-0.5 text-xs text-stone-500">{rec.reason}</p>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {insight.team_notes.length > 0 ? (
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-stone-400">Team notes</p>
          <ul className="mt-2 list-disc space-y-1 pl-4 text-sm text-stone-600">
            {insight.team_notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {insight.data_limits.length > 0 ? (
        <ul className="space-y-1 border-t border-stone-100 pt-3 text-xs text-stone-400">
          {insight.data_limits.map((limit) => (
            <li key={limit}>{limit}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

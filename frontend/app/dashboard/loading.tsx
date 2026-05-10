export default function DashboardLoading() {
  return (
    <div className="p-8 max-w-7xl mx-auto animate-pulse">
      {/* Greeting skeleton */}
      <div className="mb-10">
        <div className="h-8 w-64 bg-white/5 rounded-lg mb-3" />
        <div className="h-4 w-48 bg-white/5 rounded-lg" />
      </div>

      {/* Quick action cards skeleton */}
      <div className="grid md:grid-cols-3 gap-6 mb-12">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-40 rounded-2xl bg-surface/40 border border-white/5"
          />
        ))}
      </div>

      {/* Stats skeleton */}
      <div className="grid gap-4 md:grid-cols-4 mb-12">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="h-24 rounded-xl bg-surface/40 border border-white/10"
          />
        ))}
      </div>

      {/* Recent meetings skeleton */}
      <div className="space-y-3">
        <div className="h-6 w-40 bg-white/5 rounded-lg mb-4" />
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-16 rounded-xl bg-surface/40 border border-white/5"
          />
        ))}
      </div>
    </div>
  );
}

export default function RoomLoading() {
  return (
    <div className="flex h-screen items-center justify-center bg-background">
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 rounded-xl bg-primary/20 animate-pulse" />
        <p className="text-gray-400 text-sm">Connecting to meeting…</p>
      </div>
    </div>
  );
}

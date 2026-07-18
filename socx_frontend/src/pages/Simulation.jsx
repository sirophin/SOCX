import { useEffect, useState } from "react";
import { apiClient } from "../api/client";

export default function Simulation() {
  const [status, setStatus] = useState({
    running: false,
    events_generated: 0,
    alerts_generated: 0,
    last_event_at: null,
    last_error: null,
  });

  const [loading, setLoading] = useState(false);

  const fetchStatus = async () => {
    try {
      const res = await apiClient.get("/simulator/status");
      setStatus(res.data);
    } catch (error) {
      console.error(error);
    }
  };

  const startSimulator = async () => {
    try {
      setLoading(true);
      await apiClient.post("/simulator/start");
      await fetchStatus();
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const stopSimulator = async () => {
    try {
      setLoading(true);
      await apiClient.post("/simulator/stop");
      await fetchStatus();
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();

    const interval = setInterval(() => {
      fetchStatus();
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Attack Simulator</h1>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <div className="rounded-xl bg-base-800 border border-base-700 p-5">
          <p className="text-sm text-ink-500">Status</p>
          <h2 className="mt-2 text-xl font-semibold">
            {status.running ? "🟢 Running" : "⚪ Stopped"}
          </h2>
        </div>

        <div className="rounded-xl bg-base-800 border border-base-700 p-5">
          <p className="text-sm text-ink-500">Events Generated</p>
          <h2 className="mt-2 text-3xl font-bold">
            {status.events_generated}
          </h2>
        </div>

        <div className="rounded-xl bg-base-800 border border-base-700 p-5">
          <p className="text-sm text-ink-500">Alerts Generated</p>
          <h2 className="mt-2 text-3xl font-bold text-red-400">
            {status.alerts_generated}
          </h2>
        </div>

        <div className="rounded-xl bg-base-800 border border-base-700 p-5">
          <p className="text-sm text-ink-500">Last Event</p>
          <h2 className="mt-2 text-sm break-all">
            {status.last_event_at || "No events yet"}
          </h2>
        </div>
      </div>

      <div className="flex gap-4">
        <button
          onClick={startSimulator}
          disabled={loading || status.running}
          className="rounded-lg bg-green-600 px-5 py-2 font-medium hover:bg-green-700 disabled:opacity-50"
        >
          ▶ Start Simulation
        </button>

        <button
          onClick={stopSimulator}
          disabled={loading || !status.running}
          className="rounded-lg bg-red-600 px-5 py-2 font-medium hover:bg-red-700 disabled:opacity-50"
        >
          ■ Stop Simulation
        </button>

        <button
          onClick={fetchStatus}
          className="rounded-lg bg-blue-600 px-5 py-2 font-medium hover:bg-blue-700"
        >
          🔄 Refresh
        </button>
      </div>

      {status.last_error && (
        <div className="rounded-lg border border-red-500 bg-red-900/20 p-4 text-red-300">
          <strong>Error:</strong> {status.last_error}
        </div>
      )}
    </div>
  );
}

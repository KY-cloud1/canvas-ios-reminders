import { useEffect, useState } from "react";
import { getStatus } from "../../api/server";
import type { ServerStatus } from "../../types/server";
import styles from "./ServerStatusPanel.module.css";

/**
 * Displays the current backend server status.
 *
 * Fetches the server status when the component mounts and renders
 * the current status, refresh interval, cache statistics, and the
 * most recent refresh information.
 *
 * Displays appropriate loading and error states while the status
 * is being retrieved.
 */
function ServerStatusPanel() {
    const [serverStatus, setServerStatus] = useState<ServerStatus | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    /**
     * Retrieves the latest server status and updates the component state.
     */
    async function loadStatus() {
        setIsLoading(true);

        try {
            const status = await getStatus();
            setServerStatus(status);
            setError(null);
        } catch {
            setError("Failed to fetch server status.");
        } finally {
            setIsLoading(false);
        }
    }

    useEffect(() => {
        loadStatus();
    }, []);

    if (isLoading) {
        return <div>Loading status...</div>;
    }

    if (error) {
        return <div>{error}</div>;
    }

    if (!serverStatus) {
        return <div>No server status available.</div>;
    }

    return (
        <div className={styles.statusCard}>
            <p>Status: {serverStatus.status}</p>
            <p>Refresh Interval: {serverStatus.refresh_interval} seconds</p>
            <p>Number of Cached Assignments: {serverStatus.cached_assignments}</p>
            <p>
                Last Refresh:{" "}
                {serverStatus.last_refresh
                    ? new Date(serverStatus.last_refresh).toLocaleString(undefined, {
                        dateStyle: "short",
                        timeStyle: "short",
                    })
                    : "Never"}
            </p>
            <p>Last Refresh Error: {serverStatus.last_refresh_error ?? "None"}</p>
        </div>
    );
}

export default ServerStatusPanel;

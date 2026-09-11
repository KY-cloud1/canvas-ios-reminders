import { useServer } from "../../context/ServerContext";
import styles from "./ServerStatusPanel.module.css";

/**
 * Renders the current backend server status.
 *
 * Displays a loading state while waiting for the initial server status,
 * an error state if a server status update cannot be processed, and the
 * current server status information when available.
 */
export function ServerStatusPanel() {
  const { serverStatus, error } = useServer();

  return (
    <div className={styles.statusCard}>
      <h2 className={styles.centeredLine}>Server Status</h2>

      {!serverStatus && !error && <div>Loading server status...</div>}

      {error && <div>{error}</div>}

      {!error && serverStatus && (
        <>
          <p>
            <span className={styles.label}>Status:</span> {serverStatus.status}
          </p>
          <p>
            <span className={styles.label}>Number of Cached Assignments:</span>{" "}
            {serverStatus.cached_assignments}
          </p>
          <p>
            <span className={styles.label}>Last Refresh:</span>{" "}
            {serverStatus.last_refresh
              ? new Date(serverStatus.last_refresh).toLocaleString(undefined, {
                  dateStyle: "short",
                  timeStyle: "short",
                })
              : "Never"}
          </p>
          <p>
            <span className={styles.label}>Last Refresh Error:</span>{" "}
            {serverStatus.last_refresh_error ?? "None"}
          </p>
        </>
      )}
    </div>
  );
}

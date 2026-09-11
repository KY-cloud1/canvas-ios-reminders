import { refreshAssignments } from "../../api/server";
import { useServer } from "../../context/ServerContext";
import styles from "./ServerRefreshButton.module.css";

/**
 * Renders a button for manually refreshing server assignments.
 *
 * Uses the shared server status to disable the button while a refresh
 * is in progress. The button is automatically re-enabled when the
 * backend reports that the refresh has completed.
 *
 * @returns The server refresh button component.
 */
export function ServerRefreshButton() {
  const { serverStatus } = useServer();

  const isRefreshing = serverStatus?.refreshing == true;

  async function handleRefresh() {
    await refreshAssignments();
  }

  return (
    <div className={styles.refreshButton}>
      <div>
        <h2>Refresh Server</h2>
        <br />
        <button onClick={handleRefresh} disabled={isRefreshing}>
          {isRefreshing ? "Refreshing..." : "Refresh"}
        </button>
      </div>
    </div>
  );
}

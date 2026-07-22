import { useState } from "react";
import { refreshAssignments } from "../../api/server";
import styles from "./ServerRefreshButton.module.css";

export function ServerRefreshButton() {
    const [isRequestingRefresh, setIsRequestingRefresh] = useState(false);

    async function handleRefresh() {
        setIsRequestingRefresh(true);

        try {
            await refreshAssignments();
        } finally {
            setIsRequestingRefresh(false);
        }
    }

    return (
        <div className={styles.refreshButton}>
            <div>
                <h2 className={styles.centeredLine}>Refresh</h2>
                <button onClick={handleRefresh} disabled={isRequestingRefresh}>
                    {isRequestingRefresh ? "Requesting Refresh..." : "Refresh Assignments"}
                </button>
            </div>
        </div>
    );
}

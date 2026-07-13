import { useEffect, useState } from "react";
import { getStatus } from "../api/server";
import type { ServerStatus } from "../types/server";

/**
 * Retrieves and manages the backend server status.
 *
 * Fetches the current server status when the hook is first used and
 * provides the status data, loading state, error state, and a function
 * to manually refresh the status.
 *
 * @returns An object containing the server status, loading state,
 * error state, and a refresh function.
 */
export function useServerStatus() {
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

    return {
        serverStatus,
        isLoading,
        error,
        refresh: loadStatus,
    };
}

import { useEffect, useState } from "react";
import { getConfig } from "../api/server";
import type { ServerConfig } from "../types/server";

/**
 * Retrieves and manages the backend server configuration.
 *
 * Fetches the current server configuration when the hook is first used and
 * provides the configuration data, loading state, error state, and a function
 * to manually refresh the configuration.
 *
 * @returns An object containing the server configuration, loading state,
 * error state, and a refresh function.
 */
export function useServerConfig() {
    const [serverConfig, setServerConfig] = useState<ServerConfig | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    /**
     * Retrieves the latest server config and updates the component state.
     */
    async function loadConfig() {
        setIsLoading(true);

        try {
            const config = await getConfig();
            setServerConfig(config);
            setError(null);
        } catch {
            setError("Failed to fetch server config.");
        } finally {
            setIsLoading(false);
        }
    }

    useEffect(() => {
        loadConfig();
    }, []);

    return {
        serverConfig,
        isLoading,
        error,
        refresh: loadConfig,
    };
}

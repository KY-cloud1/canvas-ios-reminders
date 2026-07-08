import type { ServerConfig, ServerStatus } from "../types/server";

const API = "/api";

/**
 * Retrieves the current status of the server.
 *
 * @returns A promise that resolves to the current server status information.
 *
 * @throws {Error} If the API request fails or returns a non-success response.
 */
export async function getStatus(): Promise<ServerStatus> {
    const response = await fetch(`${API}/status`);

    if (!response.ok) {
        throw new Error("Failed to fetch status from server.");
    }

    return response.json();
}

/**
 * Retrieves the current server configuration.
 *
 * @returns A promise that resolves to the server configuration.
 *
 * @throws {Error} If the API request fails or returns a non-success response.
 */
export async function getConfig(): Promise<ServerConfig> {
    const response = await fetch(`${API}/config`);

    if (!response.ok) {
        throw new Error("Failed to fetch config from server.");
    }

    return response.json();
}

/**
 * Requests the server to refresh assignment data.
 *
 * @throws {Error} If the server request fails or returns a non-success response.
 */
export async function refreshAssignments(): Promise<void> {
    const response = await fetch(`${API}/refresh`, {
        method: "POST",
    });

    if (!response.ok) {
        throw new Error("Failed to refresh assignments with server.");
    }
}

import type {
  ServerRefreshResponse,
  ServerSettings,
  ServerSettingsUpdate,
  ServerStatus,
} from "../types/server";

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
 * Retrieves the current server settings.
 *
 * @returns A promise that resolves to the server settings.
 *
 * @throws {Error} If the API request fails or returns a non-success response.
 */
export async function getSettings(): Promise<ServerSettings> {
  const response = await fetch(`${API}/settings`);

  if (!response.ok) {
    throw new Error("Failed to fetch settings from server.");
  }

  return response.json();
}

/**
 * Updates the current server settings.
 *
 * @param settings - The settings to apply to the server.
 * @returns A promise that resolves when the settings have been successfully
 *          updated.
 *
 * @throws {Error} If the API request fails or returns a non-success response.
 */
export async function updateSettings(
  settings: ServerSettingsUpdate,
): Promise<void> {
  const response = await fetch(`${API}/settings`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(settings),
  });

  if (!response.ok) {
    throw new Error("Failed to update server settings.");
  }
}

/**
 * Requests the server to refresh assignment data.
 *
 * @returns A promise that resolves to a status indicating the refresh has been
 *          started.
 *
 * @throws {Error} If the server request fails or returns a non-success
 *          response.
 */
export async function refreshAssignments(): Promise<ServerRefreshResponse> {
  const response = await fetch(`${API}/refresh`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error("Failed to refresh assignments with server.");
  }

  return response.json();
}

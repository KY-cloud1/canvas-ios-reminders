import { useEffect, useState } from "react";
import { getSettings, refreshAssignments, updateSettings } from "../api/server";
import type { ServerSettings, ServerSettingsUpdate } from "../types/server";

/**
 * Retrieves and manages the current server settings.
 *
 * The settings are automatically fetched when the hook is mounted and can
 * be manually refreshed using the returned `refresh` function.
 *
 * @returns The current server settings, loading state, saving state, error
 * state, and functions for refreshing and updating the settings.
 */
export function useServerSettings() {
  const [serverSettings, setServerSettings] = useState<ServerSettings | null>(
    null,
  );
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetches the latest server settings and updates the hook state.
   */
  async function loadSettings() {
    try {
      const config = await getSettings();
      setServerSettings(config);
      setError(null);
    } catch {
      setError("Failed to fetch server settings.");
    } finally {
      setIsLoading(false);
    }
  }

  /**
   * Updates the server settings and refreshes the local settings state.
   */
  async function saveSettings(newSettings: ServerSettingsUpdate) {
    setIsSaving(true);

    try {
      await updateSettings(newSettings);
      await loadSettings();
      await refreshAssignments();
      setError(null);
    } catch {
      setError("Failed to update server settings.");
    } finally {
      setIsSaving(false);
    }
  }

  useEffect(() => {
    void loadSettings();
  }, []);

  return {
    serverSettings,
    isLoading,
    isSaving,
    error,
    refresh: loadSettings,
    saveSettings,
  };
}

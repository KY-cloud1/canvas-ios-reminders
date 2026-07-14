import { useServerConfig } from "../../hooks/useServerConfig";
import styles from "./ServerConfigPanel.module.css";

/**
 * Renders the current backend server configuration.
 *
 * Displays loading and error states while the server config is being
 * retrieved and renders the current config information when available.
 */
export function ServerConfigPanel() {
    const {
        serverConfig,
        isLoading,
        error,
    } = useServerConfig();

    if (isLoading) {
        return <div>Loading status...</div>;
    }

    if (error) {
        return <div>{error}</div>;
    }

    if (!serverConfig) {
        return <div>No server config available.</div>;
    }

    return (
        <div className={styles.configCard}>
            <h2>Configuration</h2>
            <h3>General:</h3>
            <p>Refresh Interval: {serverConfig.refresh_interval}</p>
            <p>Weeks Delta: {serverConfig.weeks_delta}</p>

            <h3>Canvas:</h3>
            <p>Enabled: {serverConfig.canvas.enabled ? "Yes" : "No"}</p>
            <p>Configured: {serverConfig.canvas.configured ? "Yes" : "No"}</p>

            <h3>Gradescope:</h3>
            <p>Enabled: {serverConfig.gradescope.enabled ? "Yes" : "No"}</p>
            <p>Configured: {serverConfig.gradescope.configured ? "Yes" : "No"}</p>

            <h3>ngrok:</h3>
            <p>Enabled: {serverConfig.ngrok.enabled ? "Yes" : "No"}</p>
            <p>Configured: {serverConfig.ngrok.configured ? "Yes" : "No"}</p>
        </div>
    );
}

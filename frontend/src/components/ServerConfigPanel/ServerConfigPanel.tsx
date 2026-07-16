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
            <p><span className={styles.label}>Refresh Interval:</span> {serverConfig.refresh_interval}</p>
            <p><span className={styles.label}>Weeks Delta:</span> {serverConfig.weeks_delta}</p>

            <h3>Canvas:</h3>
            <p><span className={styles.label}>Enabled:</span> {serverConfig.canvas.enabled ? "Yes" : "No"}</p>
            <p><span className={styles.label}>Configured:</span> {serverConfig.canvas.configured ? "Yes" : "No"}</p>

            <h3>Gradescope:</h3>
            <p><span className={styles.label}>Enabled:</span> {serverConfig.gradescope.enabled ? "Yes" : "No"}</p>
            <p><span className={styles.label}>Configured:</span> {serverConfig.gradescope.configured ? "Yes" : "No"}</p>

            <h3>ngrok:</h3>
            <p><span className={styles.label}>Enabled:</span> {serverConfig.ngrok.enabled ? "Yes" : "No"}</p>
            <p><span className={styles.label}>Configured:</span> {serverConfig.ngrok.configured ? "Yes" : "No"}</p>
        </div>
    );
}

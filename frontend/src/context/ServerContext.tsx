import { createContext, useContext, useEffect, useState } from "react";
import type { ServerStatus } from "../types/server";

interface ServerContextValue {
  serverStatus: ServerStatus | null;
  error: string | null;
}

const ServerContext = createContext<ServerContextValue | null>(null);

/**
 * Provides shared backend server state to descendant components.
 *
 * Establishes a single SSE connection to the backend and listens for
 * server status updates. The latest server status and any parsing errors
 * are made available to components through the ServerContext.
 *
 * The SSE connection is automatically closed when the provider unmounts.
 *
 * @param children - The React components that will have access to the
 *   server context.
 */
export function ServerProvider({ children }: { children: React.ReactNode }) {
  const [serverStatus, setServerStatus] = useState<ServerStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const events = new EventSource("/api/events");

    events.addEventListener("server_status", (event) => {
      try {
        const status = JSON.parse(event.data) as ServerStatus;

        setServerStatus(status);
        setError(null);
      } catch {
        setError("Failed to parse server status update.");
      }
    });

    return () => {
      events.close();
    };
  }, []);

  return (
    <ServerContext.Provider value={{ serverStatus, error }}>
      {children}
    </ServerContext.Provider>
  );
}

/**
 * Provides access to the shared backend server state.
 *
 * Must be used within a ServerProvider.
 *
 * @returns The current server status and any server status error.
 *
 * @throws {Error} If the hook is used outside of a ServerProvider.
 */
export function useServer() {
  const context = useContext(ServerContext);

  if (!context) {
    throw new Error("useServer must be used within a ServerProvider");
  }

  return context;
}

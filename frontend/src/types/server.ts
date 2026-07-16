export interface ServerStatus {
    status: "healthy" | "degraded";
    cached_assignments: number;
    last_refresh: string | null;
    last_refresh_error: string | null;
}

export interface ServerConfig {
    canvas: {
        enabled: boolean;
        configured: boolean;
    };
    gradescope: {
        enabled: boolean;
        configured: boolean;
    };
    refresh_interval: number;
    weeks_delta: number;
    ngrok: {
        enabled: boolean;
        configured: boolean;
    };
}

export interface ServerRefreshResponse {
    status: "refresh_started";
}

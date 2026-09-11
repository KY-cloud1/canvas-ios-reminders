export interface ServerStatus {
  status: "healthy" | "degraded";
  cached_assignments: number;
  last_refresh: string | null;
  last_refresh_error: string | null;
  refreshing: boolean;
}

export interface ServerSettings {
  refresh_interval: number;
  weeks_delta: number;
  canvas: {
    enabled: boolean;
    graphql_url: string | null;
    token_configured: boolean;
  };
  gradescope: {
    enabled: boolean;
    email: string | null;
    password_configured: boolean;
  };
  ngrok: {
    enabled: boolean;
    domain: string | null;
    authtoken_configured: boolean;
  };
}

export interface ServerSettingsUpdate {
  refresh_interval?: number;
  weeks_delta?: number;

  canvas_enabled?: boolean;
  canvas_graphql_url?: string | null;
  canvas_token?: string | null;

  gradescope_enabled?: boolean;
  gradescope_email?: string | null;
  gradescope_password?: string | null;

  ngrok_enabled?: boolean;
  ngrok_domain?: string | null;
  ngrok_authtoken?: string | null;
}

export interface ServerRefreshResponse {
  status: "refresh_started";
}

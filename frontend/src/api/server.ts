const API = "/api";

export async function getStatus() {
    const response = await fetch(`${API}/status`);

    if (!response.ok) {
        throw new Error("Failed to fetch status from server.");
    }

    return response.json();
}

export async function getConfig() {
    const response = await fetch(`${API}/config`);

    if (!response.ok) {
        throw new Error("Failed to fetch config from server.");
    }

    return response.json();
}

export async function refreshAssignments() {
    const response = await fetch(`${API}/refresh`, {
        method: "POST",
    });

    if (!response.ok) {
        throw new Error("Failed to refresh assignments with server.");
    }
}

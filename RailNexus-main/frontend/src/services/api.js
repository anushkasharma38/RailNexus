const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export function getStoredUser() {
  const value = localStorage.getItem("railnexus_user");
  if (!value) return null;
  try {
    return JSON.parse(value);
  } catch {
    localStorage.removeItem("railnexus_token");
    localStorage.removeItem("railnexus_user");
    return null;
  }
}

export async function api(path, options = {}) {
  const token = localStorage.getItem("railnexus_token");
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Token ${token}` } : {}),
      ...options.headers,
    },
  });
  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401 && token) {
      localStorage.removeItem("railnexus_token");
      localStorage.removeItem("railnexus_user");
      if (window.location.pathname !== "/login") window.location.assign("/login");
    }
    const details = data.detail ?? data.details;
    const message = typeof details === "string"
      ? details
      : details && typeof details === "object"
        ? Object.values(details).flat().join(" ")
        : "The request could not be completed.";
    const error = new Error(message);
    error.data = data;
    throw error;
  }
  return data;
}

export const list = (resource) => api(`/${resource}/`).then((data) => data.results || data);
export const formatDateTime = (value) =>
  value ? new Intl.DateTimeFormat("en-IN", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "—";

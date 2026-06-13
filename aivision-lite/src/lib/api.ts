/**
 * Centralized API endpoint resolver for AI Vision Lite.
 * Since this has a full-stack architecture, running inside a Capacitor client wrapper (Android/iOS)
 * expects fetch requests to map to the remote live server instead of relative localhost paths.
 */
export function getApiUrl(endpoint: string): string {
  const isCapacitor = typeof (window as any).Capacitor !== "undefined";
  const defaultProdUrl = "https://ais-pre-demsmx6mxmp3hrvpbifrrh-423821099283.europe-west3.run.app";

  // Check if they have configured a custom mobile backend URL (essential for testing on real phones)
  const customBackend = localStorage.getItem("aiv_mobile_backend_url");
  
  let baseUrl = window.location.origin;
  if (isCapacitor) {
    // On real phones, default to the pre-deployed production server
    baseUrl = defaultProdUrl;
    if (customBackend && customBackend.trim() !== "" && (customBackend.startsWith("http://") || customBackend.startsWith("https://"))) {
      baseUrl = customBackend.trim().replace(/\/+$/, "");
    }
  } else {
    // On browser, also allow using custom backend if set or fallback to window.location.origin
    if (customBackend && customBackend.trim() !== "" && (customBackend.startsWith("http://") || customBackend.startsWith("https://"))) {
      baseUrl = customBackend.trim().replace(/\/+$/, "");
    }
  }

  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;

  // If the endpoint is NOT an internal Express route (/api/...) but rather a telemetry SIEM URL,
  // we route that separately if aiv_api_endpoint is customized.
  if (!endpoint.startsWith("/api/") && !endpoint.startsWith("api/")) {
    const customEndpoint = localStorage.getItem("aiv_api_endpoint");
    if (customEndpoint && customEndpoint.trim() !== "" && customEndpoint !== "https://api.aivision.security/v1") {
      const trimmedBase = customEndpoint.trim().replace(/\/+$/, "");
      return `${trimmedBase}${cleanEndpoint}`;
    }
  }

  return `${baseUrl}${cleanEndpoint}`;
}

/**
 * Centralized API endpoint resolver for AI Vision Lite.
 * Since this has a full-stack architecture, running inside a Capacitor client wrapper (Android/iOS)
 * expects fetch requests to map to the remote live server instead of relative localhost paths.
 */
export function getApiUrl(endpoint: string): string {
  // If running inside a Capacitor native app wrapper, route API requests to the deployed Cloud Run live backend.
  // Otherwise, route relatively on the local Web environment.
  const isCapacitor = typeof (window as any).Capacitor !== "undefined";
  const baseUrl = isCapacitor
    ? "https://ais-pre-demsmx6mxmp3hrvpbifrrh-423821099283.europe-west3.run.app"
    : window.location.origin;

  // Make sure we don't duplicate slashes
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  return `${baseUrl}${cleanEndpoint}`;
}

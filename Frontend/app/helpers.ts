export function get_endpoint_url(endpoint: string): string | null {
  if (typeof window === "undefined") {
    return "";
  }

  let domain = `${window.location.protocol}//api.${window.location.host}`;
  return `${domain}/${endpoint}`;
}

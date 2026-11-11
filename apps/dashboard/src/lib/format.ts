/**
 * Formatting Utilities.
 */

export function formatPercent(value: number, decimals: number = 1): string {
  if (value === null || value === undefined || isNaN(value)) {
    return "0.0%";
  }
  return `${(value * 100).toFixed(decimals)}%`;
}

export function formatScore(value: number, decimals: number = 2): string {
  if (value === null || value === undefined || isNaN(value)) {
    return "0.00";
  }
  return value.toFixed(decimals);
}

export function formatDate(isoString: string): string {
  if (!isoString) return "-";
  try {
    const d = new Date(isoString);
    return d.toLocaleString("en-IN", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return isoString;
  }
}

export function truncateDigest(digest: string, length: number = 16): string {
  if (!digest) return "-";
  if (digest.length <= length) return digest;
  return `${digest.slice(0, length)}...`;
}

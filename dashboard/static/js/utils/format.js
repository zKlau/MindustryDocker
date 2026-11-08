const KB = 1024;
const MB = 1024 * KB;
const SECONDS_PER_MINUTE = 60;
const SECONDS_PER_HOUR = 3600;

export function capitalize(text) {
  if (!text) {
    return "";
  }

  return text[0].toUpperCase() + text.slice(1);
}

export function formatBytes(bytes) {
  if (bytes > MB) {
    return `${(bytes / MB).toFixed(1)} MB`;
  }

  return `${Math.max(1, Math.round(bytes / KB))} KB`;
}

export function formatDuration(seconds) {
  const hours = Math.floor(seconds / SECONDS_PER_HOUR);
  const minutes = Math.floor((seconds % SECONDS_PER_HOUR) / SECONDS_PER_MINUTE);
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }

  return `${minutes}m`;
}

export function formatDate(unixSeconds) {
  return new Date(unixSeconds * 1000).toLocaleString();
}

const COMPACT = new Intl.NumberFormat(undefined, { notation: "compact", maximumFractionDigits: 1 });

export function formatCount(count) {
  if (Math.abs(count) < 10000) {
    return count.toLocaleString();
  }

  return COMPACT.format(count);
}

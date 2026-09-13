/**
 * Split a headline into a plain lead-in and the phrase that gets the italic serif accent:
 * everything after a dash/colon separator, or failing that the last `n` words.
 */
export function splitAccent(headline: string, n = 2): [string, string] {
  const m = headline.match(/^(.*?)\s*[-–—:]\s*(.+)$/);
  if (m && m[2].trim().split(/\s+/).length >= 2) return [m[1].trim(), m[2].trim()];
  const w = headline.trim().split(/\s+/);
  if (w.length <= n) return ['', headline.trim()];
  return [w.slice(0, -n).join(' '), w.slice(-n).join(' ')];
}

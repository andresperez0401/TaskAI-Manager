export function toDatetimeLocal(value: string | null): string {
  if (!value) return "";
  const d = new Date(value);
  const offset = d.getTimezoneOffset();
  const local = new Date(d.getTime() - offset * 60000);
  return local.toISOString().slice(0, 16);
}

export function fromDatetimeLocal(value: string): string | null {
  if (!value) return null;
  return new Date(value).toISOString();
}

export function formatDate(value: string | null): string {
  if (!value) return "-";
  return new Date(value).toLocaleString();
}

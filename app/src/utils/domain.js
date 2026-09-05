const MULTI_LABEL_SUFFIXES = new Set([
  "co.in", "co.jp", "co.nz", "co.uk", "com.au", "com.br", "com.mx",
  "com.sg", "com.tr", "com.tw", "org.au", "org.uk",
]);

function hostname(value) {
  const raw = String(value || "").trim().toLowerCase();
  if (!raw) return "";
  try {
    return new URL(raw.includes("://") ? raw : `https://${raw}`).hostname
      .replace(/^www\./, "")
      .replace(/\.$/, "");
  } catch (error) {
    return raw.split("/")[0].replace(/^www\./, "").replace(/:\d+$/, "");
  }
}

export default function parseDomain(value) {
  const host = hostname(value);
  const labels = host.split(".").filter(Boolean);
  if (labels.length < 2) return { domain: host, tld: "" };

  const lastTwo = labels.slice(-2).join(".");
  const suffixLength = MULTI_LABEL_SUFFIXES.has(lastTwo) ? 2 : 1;
  const domain = labels.slice(-(suffixLength + 1)).join(".");
  const tld = labels.slice(-suffixLength).join(".");
  return { domain, tld };
}

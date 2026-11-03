// Cloudflare Worker: signs Enable Banking JWTs server-side, caches balance in KV,
// serves the Scriptable widget source and public logo PNGs.
// Secrets: EB_PRIVATE_KEY (PEM), WIDGET_TOKEN. Vars: EB_APP_ID, EB_ACCOUNT_UID, CONSENT_UNTIL. KV binding: BAL.
// Unattended bank calls = cron only (stay within ~4/day). /balance is cache-only; /refresh is user-present.
import widgetSrc from "./widget.txt";          // copy of coop_widget.js with __BASE__/__TOKEN__ placeholders
import logoLight from "./assets/logo_light.png";
import logoDark from "./assets/logo_dark.png";

const API = "https://api.enablebanking.com";
const COOLDOWN_MS = 20 * 1000;

const b64url = (buf) => {
  let s = "";
  for (const x of new Uint8Array(buf)) s += String.fromCharCode(x);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
};

async function makeJwt(env) {
  const enc = new TextEncoder();
  const iat = Math.floor(Date.now() / 1000);
  const head = b64url(enc.encode(JSON.stringify({ typ: "JWT", alg: "RS256", kid: env.EB_APP_ID })));
  const body = b64url(enc.encode(JSON.stringify({ iss: "enablebanking.com", aud: "api.enablebanking.com", iat, exp: iat + 3600 })));
  const pem = env.EB_PRIVATE_KEY.replace(/-----[^-]+-----/g, "").replace(/\s+/g, "");
  const der = Uint8Array.from(atob(pem), (c) => c.charCodeAt(0));
  const key = await crypto.subtle.importKey("pkcs8", der, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["sign"]);
  const sig = await crypto.subtle.sign("RSASSA-PKCS1-v1_5", key, enc.encode(`${head}.${body}`));
  return `${head}.${body}.${b64url(sig)}`;
}

// psu = { ip, ua } marks the call as user-present (PSU headers); null = unattended (cron).
async function refresh(env, psu) {
  const jwt = await makeJwt(env);
  const headers = { Authorization: `Bearer ${jwt}` };
  if (psu) {
    headers["psu-ip-address"] = psu.ip;
    if (psu.ua) headers["psu-user-agent"] = psu.ua;
  }
  const r = await fetch(`${API}/accounts/${env.EB_ACCOUNT_UID}/balances`, { headers });
  if (!r.ok) {
    const kind = r.status === 429 ? "rate_limited" : [401, 403, 422].includes(r.status) ? "consent_expired" : "api_error";
    // a rate limit is temporary: do not flag the consent as broken
    if (kind !== "rate_limited") await env.BAL.put("error", JSON.stringify({ error: kind, status: r.status, at: Date.now() }));
    return { ok: false, kind, status: r.status };
  }
  const j = await r.json();
  const pick = j.balances.find((b) => b.balance_type === "CLBD") || j.balances[0];
  const rec = { amount: pick.balance_amount.amount, currency: pick.balance_amount.currency, fetched_at: Date.now() };
  await env.BAL.put("balance", JSON.stringify(rec));
  await env.BAL.delete("error");
  return { ok: true, rec };
}

// Cache read only: never calls the bank (an on-demand stale fetch would silently exceed the unattended cap).
async function getBalance(env, extra = {}) {
  const rec = JSON.parse((await env.BAL.get("balance")) || "null");
  const err = JSON.parse((await env.BAL.get("error")) || "null");
  return { amount: rec?.amount ?? null, currency: rec?.currency ?? "EUR", fetched_at: rec?.fetched_at ?? null,
    consent_valid_until: env.CONSENT_UNTIL, error: err?.error ?? null, now: Date.now(), ...extra };
}

async function userRefresh(req, env) {
  const last = Number((await env.BAL.get("last_user_refresh")) || 0);
  if (Date.now() - last < COOLDOWN_MS) return getBalance(env, { refreshed: false, reason: "cooldown" });
  const ip = req.headers.get("cf-connecting-ip");
  if (!ip) return getBalance(env, { refreshed: false, reason: "no_ip" });
  await env.BAL.put("last_user_refresh", String(Date.now()));
  const res = await refresh(env, { ip, ua: req.headers.get("user-agent") });
  // KV reads can be stale ~60s after a write; return the fresh record directly when we have it
  const out = await getBalance(env, { refreshed: res.ok, reason: res.ok ? "ok" : res.kind, bank_status: res.ok ? 200 : res.status });
  if (res.ok) Object.assign(out, { amount: res.rec.amount, currency: res.rec.currency, fetched_at: res.rec.fetched_at });
  return out;
}

const json = (o, s = 200) => new Response(JSON.stringify(o), { status: s, headers: { "content-type": "application/json", "cache-control": "no-store" } });

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    const logo = { "/logo/light.png": logoLight, "/logo/dark.png": logoDark }[url.pathname];
    if (logo) return new Response(logo, { headers: { "content-type": "image/png", "cache-control": "public, max-age=604800" } });
    const token = url.searchParams.get("t") || req.headers.get("x-widget-token");
    if (!token || token !== env.WIDGET_TOKEN) return json({ error: "unauthorized" }, 401);
    if (url.pathname === "/balance") return json(await getBalance(env));
    if (url.pathname === "/refresh") return json(await userRefresh(req, env));
    if (url.pathname === "/widget.js") {
      const src = widgetSrc.replace("__BASE__", url.origin).replace("__TOKEN__", token);
      return new Response(src, { headers: { "content-type": "text/plain; charset=utf-8", "cache-control": "no-store" } });
    }
    return json({ error: "not_found" }, 404);
  },
  async scheduled(_evt, env) { await refresh(env, null); },
};

import { createHmac, timingSafeEqual } from "node:crypto";

const COOKIE = "ksk_admin";
const MAX_AGE_SECONDS = 60 * 60 * 12;

function password(): string | null {
  const value = process.env.ADMIN_PASSWORD;
  return value && value.length > 0 ? value : null;
}

export function adminConfigured(): boolean {
  return password() !== null;
}

export function createAdminCookie(): string {
  const secret = password();
  if (!secret) throw new Error("Das Admin-Passwort ist nicht konfiguriert.");
  const exp = Date.now() + MAX_AGE_SECONDS * 1000;
  const body = `v1.${exp}`;
  const mac = createHmac("sha256", secret).update(body).digest("base64url");
  return `${body}.${mac}`;
}

export function adminCookieHeader(token: string): string {
  const secure = process.env.NODE_ENV === "production" ? "; Secure" : "";
  return `${COOKIE}=${token}; HttpOnly; Path=/; Max-Age=${MAX_AGE_SECONDS}; SameSite=Lax${secure}`;
}

export function clearAdminCookieHeader(): string {
  return `${COOKIE}=; HttpOnly; Path=/; Max-Age=0; SameSite=Lax`;
}

export function readAdminToken(cookieHeader: string | null): boolean {
  const secret = password();
  if (!secret || !cookieHeader) return false;
  const pair = cookieHeader.split(";").map((part) => part.trim()).find((part) => part.startsWith(`${COOKIE}=`));
  if (!pair) return false;
  const token = pair.slice(COOKIE.length + 1);
  const [version, exp, mac] = token.split(".");
  if (version !== "v1" || !exp || !mac) return false;
  if (Number(exp) < Date.now()) return false;
  const body = `v1.${exp}`;
  const expected = createHmac("sha256", secret).update(body).digest("base64url");
  const left = Buffer.from(mac);
  const right = Buffer.from(expected);
  if (left.length !== right.length) return false;
  return timingSafeEqual(left, right);
}

export function passwordsMatch(input: string): boolean {
  const secret = password();
  if (!secret) return false;
  const left = Buffer.from(input);
  const right = Buffer.from(secret);
  if (left.length !== right.length) return false;
  return timingSafeEqual(left, right);
}

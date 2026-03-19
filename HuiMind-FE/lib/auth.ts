import type { LoginData } from "@/lib/types";

const TOKEN_KEY = "huimind_token";
const USER_KEY = "huimind_user";

function canUseStorage() {
  return typeof window !== "undefined";
}

export function getAuthToken() {
  if (!canUseStorage()) {
    return "";
  }
  return window.localStorage.getItem(TOKEN_KEY) ?? "";
}

export function setAuthSession(payload: LoginData) {
  if (!canUseStorage()) {
    return;
  }
  window.localStorage.setItem(TOKEN_KEY, payload.token);
  window.localStorage.setItem(USER_KEY, JSON.stringify(payload.user));
}

export function getStoredUser() {
  if (!canUseStorage()) {
    return null;
  }
  const raw = window.localStorage.getItem(USER_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as LoginData["user"];
  } catch {
    return null;
  }
}

export function clearAuthSession() {
  if (!canUseStorage()) {
    return;
  }
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
}

export function isLoggedIn() {
  return Boolean(getAuthToken());
}

import { get, LOGGED_OUT_EVENT, post } from "../api/client.js";
import { API } from "../api/endpoints.js";
import { $ } from "../ui/dom.js";
import { toast } from "../ui/toast.js";
import { setPollingActive } from "./polling.js";

let onFirstLogin = () => {};
let started = false;

function showLogin() {
  setPollingActive(false);
  $("#app").hidden = true;
  $("#login").hidden = false;
  $("#password").focus();
}

function showApp() {
  setPollingActive(true);
  $("#login").hidden = true;
  $("#app").hidden = false;
  if (!started) {
    started = true;
    onFirstLogin();
  }
}

async function login(event) {
  event.preventDefault();
  try {
    await post(API.login, { password: $("#password").value });
    $("#password").value = "";
    showApp();
  } catch (error) {
    toast(error.message, true);
  }
}

async function logout() {
  await post(API.logout).catch(() => null);
  location.reload();
}

async function checkSession() {
  const session = await get(API.session).catch(() => ({ authed: false }));
  if (session.authed) {
    showApp();
  } else {
    showLogin();
  }
}

export function startSession(startApp) {
  onFirstLogin = startApp;
  $("#loginForm").addEventListener("submit", login);
  $("#logoutButton").addEventListener("click", logout);
  window.addEventListener(LOGGED_OUT_EVENT, showLogin);
  checkSession();
}

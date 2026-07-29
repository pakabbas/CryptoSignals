import { initializeApp, getApp, getApps } from "https://www.gstatic.com/firebasejs/12.16.0/firebase-app.js";
import {
  getMessaging,
  getToken,
  isSupported,
  deleteToken,
} from "https://www.gstatic.com/firebasejs/12.16.0/firebase-messaging.js";

const statusEl = document.getElementById("fcmStatus");
const enableBtn = document.getElementById("fcmEnableBtn");
const disableBtn = document.getElementById("fcmDisableBtn");

function setStatus(text, isError = false) {
  if (statusEl) {
    statusEl.textContent = "Status: " + text;
    statusEl.classList.toggle("text-danger", isError);
  }
}

async function registerServer(token) {
  const res = await fetch(window.__FCM_REGISTER_URL__, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  });
  const data = await res.json();
  if (!res.ok || !data.ok) {
    throw new Error(data.error || "Server registration failed");
  }
}

function firebaseApp() {
  return getApps().length ? getApp() : initializeApp(window.__FIREBASE_CLIENT__);
}

async function enablePush() {
  if (!(await isSupported())) {
    setStatus("Not supported in this browser.", true);
    return;
  }
  if (!("Notification" in window)) {
    setStatus("Notifications API unavailable.", true);
    return;
  }
  const permission = await Notification.requestPermission();
  if (permission !== "granted") {
    setStatus("Permission denied. Allow notifications in browser settings.", true);
    return;
  }

  const reg = await navigator.serviceWorker.register("/firebase-messaging-sw.js", {
    scope: "/",
  });
  await navigator.serviceWorker.ready;

  const app = firebaseApp();
  const messaging = getMessaging(app);
  const token = await getToken(messaging, {
    vapidKey: window.__FIREBASE_VAPID__,
    serviceWorkerRegistration: reg,
  });
  if (!token) {
    setStatus("Could not get FCM token.", true);
    return;
  }
  await registerServer(token);
  setStatus("Enabled — token registered.");
  document.getElementById("fcmDashboardPrompt")?.classList.add("d-none");
}

async function disablePush() {
  try {
    const app = firebaseApp();
    const messaging = getMessaging(app);
    const token = await getToken(messaging, { vapidKey: window.__FIREBASE_VAPID__ });
    if (token) {
      await fetch(window.__FCM_UNREGISTER_URL__, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token }),
      });
      await deleteToken(messaging);
    }
    setStatus("Disabled on this browser.");
  } catch (e) {
    setStatus(String(e), true);
  }
}

enableBtn?.addEventListener("click", () => {
  enablePush().catch((e) => setStatus(String(e), true));
});
disableBtn?.addEventListener("click", () => {
  disablePush().catch((e) => setStatus(String(e), true));
});

const dashboardPrompt = document.getElementById("fcmDashboardPrompt");

function refreshDashboardPrompt() {
  if (!dashboardPrompt) return;
  const perm = Notification?.permission;
  if (perm === "granted") {
    dashboardPrompt.classList.add("d-none");
    return;
  }
  dashboardPrompt.classList.remove("d-none");
  if (perm === "denied") {
    setStatus("Notifications blocked — allow them in browser settings, then refresh.", true);
  } else if (statusEl) {
    setStatus("Click Allow to turn on alerts.");
  }
}

refreshDashboardPrompt();

if (window.__FCM_AUTO_REGISTER__ && Notification?.permission === "granted") {
  enablePush().catch(() => refreshDashboardPrompt());
}

if (Notification?.permission === "granted" && !dashboardPrompt) {
  setStatus("Permission already granted — click Enable to register this device.");
} else if (!dashboardPrompt) {
  setStatus("Not enabled yet.");
}

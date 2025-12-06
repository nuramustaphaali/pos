// static/js/pwa.js

// Register service worker
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/static/service-worker.js")
      .then((reg) => {
        console.log("Service Worker registered", reg);
      })
      .catch((err) => {
        console.error("Service Worker registration failed:", err);
      });
  });
}

// Handle "Add to Home Screen" / Install prompt
let deferredPrompt;
const installBtn = document.getElementById("install-app-btn");

window.addEventListener("beforeinstallprompt", (e) => {
  // Prevent the default mini-infobar
  e.preventDefault();
  deferredPrompt = e;

  if (installBtn) {
    installBtn.classList.remove("d-none");
  }
});

if (installBtn) {
  installBtn.addEventListener("click", async () => {
    if (!deferredPrompt) {
      return;
    }
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    console.log("User install choice:", outcome);
    deferredPrompt = null;
    installBtn.classList.add("d-none");
  });
}

// Optional: react to app being installed
window.addEventListener("appinstalled", () => {
  console.log("Nura POS was installed");
  if (installBtn) {
    installBtn.classList.add("d-none");
  }
});
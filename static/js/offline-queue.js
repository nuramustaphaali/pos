// static/js/offline-queue.js

const OFFLINE_QUEUE_KEY = "nura_pos_offline_queue_v1";

/**
 * Read queue from localStorage
 */
function getOfflineQueue() {
  try {
    const raw = localStorage.getItem(OFFLINE_QUEUE_KEY);
    if (!raw) return [];
    return JSON.parse(raw);
  } catch (e) {
    console.error("Error reading offline queue", e);
    return [];
  }
}

/**
 * Write queue to localStorage
 */
function saveOfflineQueue(queue) {
  try {
    localStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(queue));
  } catch (e) {
    console.error("Error saving offline queue", e);
  }
}

/**
 * Add a new action to the queue
 */
function enqueueOfflineAction(action) {
  const queue = getOfflineQueue();
  queue.push(action);
  saveOfflineQueue(queue);
}

/**
 * Try to process the offline queue when online
 */
async function processOfflineQueue() {
  if (!navigator.onLine) return;

  let queue = getOfflineQueue();
  if (!queue.length) return;

  console.log("Processing offline queue:", queue.length, "items");

  const newQueue = [];

  for (const item of queue) {
    try {
      const response = await fetch(item.url, {
        method: item.method || "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": item.csrfToken || "",
        },
        body: item.body,
        credentials: "include",
      });

      if (!response.ok) {
        console.warn("Offline action failed, keeping in queue:", item, response.status);
        newQueue.push(item); // keep it for retry
      } else {
        console.log("Offline action synced:", item.type);
      }
    } catch (e) {
      console.error("Error syncing offline action:", e);
      newQueue.push(item); // keep it for retry
    }
  }

  saveOfflineQueue(newQueue);
}

/**
 * Collect form data into URL-encoded string
 */
function formToUrlEncoded(form) {
  const formData = new FormData(form);
  const params = new URLSearchParams();
  formData.forEach((value, key) => {
    // We skip files here; offline syncing of images is complex
    if (value instanceof File) return;
    params.append(key, value);
  });
  return params.toString();
}

/**
 * Attach offline handler to forms with data-offline="true"
 */
function setupOfflineForms() {
  const forms = document.querySelectorAll("form[data-offline='true']");

  forms.forEach((form) => {
    form.addEventListener("submit", function (event) {
      if (navigator.onLine) {
        // Online: submit normally
        return;
      }

      event.preventDefault();

      const actionUrl = form.getAttribute("action") || window.location.pathname;
      const csrfInput = form.querySelector("input[name='csrfmiddlewaretoken']");
      const csrfToken = csrfInput ? csrfInput.value : "";
      const formType = form.dataset.offlineType || "generic";

      const body = formToUrlEncoded(form);

      enqueueOfflineAction({
        type: formType,
        url: actionUrl,
        method: form.getAttribute("method") || "POST",
        csrfToken: csrfToken,
        body: body,
        createdAt: new Date().toISOString(),
      });

      // Simple user feedback (you can style this nicer)
      alert("You are offline. Your action has been saved and will sync when you're back online.");

      // Optionally, you can still update the UI locally
      // e.g., clear form, show 'pending' badge, etc.
    });
  });
}

// Setup on load
window.addEventListener("load", () => {
  setupOfflineForms();
  processOfflineQueue();
});

// Retry when connection comes back
window.addEventListener("online", () => {
  processOfflineQueue();
});
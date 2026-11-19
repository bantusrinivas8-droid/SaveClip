const DEFAULT_SERVER = "http://127.0.0.1:8000";

async function getServer() {
  const { server } = await chrome.storage.sync.get({ server: DEFAULT_SERVER });
  return (server || DEFAULT_SERVER).replace(/\/+$/, "");
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const tell = (tabId, data) =>
  tabId !== undefined && chrome.tabs.sendMessage(tabId, { type: "saveclip-status", ...data }).catch(() => {});

// downloadId -> tabId, so we can tell the page when the file is saved
const pending = new Map();

async function runDownload(msg, tabId) {
  const server = await getServer();
  let job;
  try {
    const res = await fetch(`${server}/api/jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: msg.url, kind: msg.kind, quality: msg.quality }),
    });
    job = await res.json().catch(() => ({}));
    if (!res.ok) return tell(tabId, { state: "error", error: job.detail || "Couldn't start the download." });
  } catch {
    return tell(tabId, { state: "error", error: "Can't reach the SaveClip server. Is it running? Check the address in SaveClip settings." });
  }

  // Poll until the server has the file ready (keeps the service worker awake too).
  for (let i = 0; i < 1200; i++) {
    await sleep(1500);
    let st;
    try {
      const r = await fetch(`${server}/api/jobs/${job.id}`, { cache: "no-store" });
      st = await r.json();
      if (!r.ok) return tell(tabId, { state: "error", error: st.detail || "Download expired." });
    } catch {
      continue; // brief network hiccup, keep trying
    }
    if (st.status === "error") return tell(tabId, { state: "error", error: st.error || "Download failed." });
    if (st.status === "done") {
      const id = await chrome.downloads.download({ url: `${server}/api/jobs/${job.id}/file` });
      pending.set(id, tabId);
      return tell(tabId, { state: "saving" });
    }
    tell(tabId, { state: "progress", progress: st.progress });
  }
  tell(tabId, { state: "error", error: "This is taking too long. Try a lower quality." });
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type !== "saveclip-download") return;
  runDownload(msg, sender.tab && sender.tab.id);
  sendResponse({ ok: true });
});

chrome.downloads.onChanged.addListener((delta) => {
  const tabId = pending.get(delta.id);
  if (tabId === undefined || !delta.state) return;
  if (delta.state.current === "complete") tell(tabId, { state: "done" });
  else if (delta.state.current === "interrupted") tell(tabId, { state: "error", error: "Saving the file failed. Please try again." });
  if (delta.state.current !== "in_progress") pending.delete(delta.id);
});

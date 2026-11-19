const DEFAULT_SERVER = "http://127.0.0.1:8000";

async function getServer() {
  const { server } = await chrome.storage.sync.get({ server: DEFAULT_SERVER });
  return (server || DEFAULT_SERVER).replace(/\/+$/, "");
}

// downloadId -> tabId, so we can tell the page when a download finishes or fails
const pending = new Map();

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type !== "saveclip-download") return;
  (async () => {
    const server = await getServer();
    const params = new URLSearchParams({ url: msg.url, kind: msg.kind, quality: msg.quality });
    try {
      const id = await chrome.downloads.download({ url: `${server}/api/download?${params}` });
      if (sender.tab) pending.set(id, sender.tab.id);
      sendResponse({ ok: true, server });
    } catch (e) {
      sendResponse({ ok: false, error: String(e && e.message || e) });
    }
  })();
  return true; // keep sendResponse alive for the async work
});

chrome.downloads.onChanged.addListener((delta) => {
  const tabId = pending.get(delta.id);
  if (tabId === undefined || !delta.state) return;
  if (delta.state.current === "complete") {
    chrome.tabs.sendMessage(tabId, { type: "saveclip-status", ok: true }).catch(() => {});
    pending.delete(delta.id);
  } else if (delta.state.current === "interrupted") {
    chrome.downloads.search({ id: delta.id }).then(([item]) => {
      chrome.tabs.sendMessage(tabId, {
        type: "saveclip-status", ok: false, error: item && item.error
      }).catch(() => {});
    });
    pending.delete(delta.id);
  }
});

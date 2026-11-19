const DEFAULT_SERVER = "http://127.0.0.1:8000";
const input = document.getElementById("server");
const status = document.getElementById("status");
const show = (t, c) => { status.textContent = t; status.className = c; };

chrome.storage.sync.get({ server: DEFAULT_SERVER }, ({ server }) => { input.value = server; });

document.getElementById("save").onclick = () => {
  const v = input.value.trim().replace(/\/+$/, "") || DEFAULT_SERVER;
  if (!/^https?:\/\//i.test(v)) return show("The address must start with http:// or https://", "err");
  chrome.storage.sync.set({ server: v }, () => { input.value = v; show("Saved ✅", "ok"); });
};

document.getElementById("test").onclick = async () => {
  const v = input.value.trim().replace(/\/+$/, "") || DEFAULT_SERVER;
  show("Checking…", "");
  try {
    const r = await fetch(v + "/api/health", { cache: "no-store" });
    const j = await r.json();
    show(j.ok ? "Server is working ✅" : "Server answered, but something is wrong.", j.ok ? "ok" : "err");
  } catch {
    show("Can't reach the server. Is SaveClip running at this address?", "err");
  }
};

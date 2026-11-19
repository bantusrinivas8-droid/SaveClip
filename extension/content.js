(() => {
  if (window.top !== window || document.getElementById("saveclip-root")) return;

  const root = document.createElement("div");
  root.id = "saveclip-root";
  root.innerHTML = `
    <button id="saveclip-hide" title="Hide on this page">✕</button>
    <button id="saveclip-fab" title="Download with SaveClip">
      <svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 3v12"/><path d="M6 10l6 6 6-6"/><path d="M5 21h14"/></svg>
    </button>
    <div id="saveclip-panel" role="dialog" aria-label="SaveClip download">
      <div class="sc-title">SaveClip <button class="sc-close" title="Close">×</button></div>
      <div class="sc-row">
        <select id="sc-vq" title="Video quality">
          <option value="best">Best video</option><option value="1080">1080p</option>
          <option value="720" selected>720p</option><option value="480">480p</option><option value="360">360p</option>
        </select>
        <button class="sc-btn mp4">MP4</button>
      </div>
      <div class="sc-row">
        <select id="sc-aq" title="Audio quality">
          <option value="320">320 kbps</option><option value="192" selected>192 kbps</option><option value="128">128 kbps</option>
        </select>
        <button class="sc-btn mp3">MP3</button>
      </div>
      <div class="sc-msg">Downloads the video on this page.</div>
    </div>`;
  document.documentElement.appendChild(root);

  const panel = root.querySelector("#saveclip-panel");
  const msg = root.querySelector(".sc-msg");
  const setMsg = (text, cls = "") => { msg.textContent = text; msg.className = "sc-msg " + cls; };

  root.querySelector("#saveclip-fab").addEventListener("click", () => {
    panel.classList.toggle("open");
    if (panel.classList.contains("open")) setMsg(hint());
  });
  root.querySelector(".sc-close").addEventListener("click", () => panel.classList.remove("open"));
  root.querySelector("#saveclip-hide").addEventListener("click", () => root.remove());

  // On feed pages the address bar isn't the video itself, so tell the user to open the post.
  function hint() {
    const u = location.href;
    const isPost = /youtube\.com\/(watch|shorts\/)|youtu\.be\/|instagram\.com\/(p|reel|reels|tv)\/|facebook\.com\/.*(videos|watch|reel|story)|fb\.watch|(x|twitter)\.com\/[^/]+\/status\/|tiktok\.com\/@[^/]+\/video\/|vimeo\.com\/\d+|soundcloud\.com\/[^/]+\/[^/]+|dailymotion\.com\/video|reddit\.com\/r\/[^/]+\/comments|twitch\.tv\/(videos|[^/]+\/clip)/i.test(u);
    return isPost ? "Downloads the video on this page." : "Tip: open the video or post itself first, then tap MP4 or MP3.";
  }

  function start(kind) {
    const quality = kind === "mp3" ? root.querySelector("#sc-aq").value : root.querySelector("#sc-vq").value;
    setMsg("Preparing your " + kind.toUpperCase() + "… it appears in your downloads when ready (can take a minute).");
    chrome.runtime.sendMessage({ type: "saveclip-download", url: location.href, kind, quality }, (res) => {
      if (chrome.runtime.lastError || !res || !res.ok) {
        setMsg("Couldn't start the download. Check the server address in the SaveClip settings.", "err");
      }
    });
  }
  root.querySelector(".sc-btn.mp4").addEventListener("click", () => start("mp4"));
  root.querySelector(".sc-btn.mp3").addEventListener("click", () => start("mp3"));

  chrome.runtime.onMessage.addListener((m) => {
    if (m.type !== "saveclip-status") return;
    if (m.state === "progress") setMsg(m.progress > 0 && m.progress < 99 ? `Downloading… ${m.progress}%` : m.progress >= 99 ? "Converting…" : "Preparing…");
    else if (m.state === "saving") setMsg("Saving to your Downloads…");
    else if (m.state === "done") setMsg("✅ Saved! Check your Downloads folder.", "ok");
    else if (m.state === "error") setMsg(m.error, "err");
  });
})();

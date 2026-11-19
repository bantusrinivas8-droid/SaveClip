import { DurableObject } from "cloudflare:workers";

// Stores the tunnel address your computer registers when start-cloudflare.bat runs.
export class Backend extends DurableObject {
  async getUrl() { return (await this.ctx.storage.get("url")) || null; }
  async setUrl(url) { await this.ctx.storage.put("url", url); }
}

const json = (data, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
  });

const OFFLINE = {
  detail: "The SaveClip computer is offline. Start start-cloudflare.bat on your PC and try again.",
};

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (!url.pathname.startsWith("/api/")) return env.ASSETS.fetch(request);

    const store = env.BACKEND.get(env.BACKEND.idFromName("main"));

    // Your PC calls this to say "I'm online at <tunnel address>".
    if (url.pathname === "/api/_register") {
      if (request.method !== "POST") return json({ detail: "Use POST." }, 405);
      if (!env.SECRET) return json({ detail: "Add a SECRET in the Worker's Settings → Variables and Secrets." }, 500);
      const body = await request.json().catch(() => ({}));
      if (body.secret !== env.SECRET) return json({ detail: "Wrong secret." }, 403);
      if (!/^https:\/\/[a-z0-9.-]+$/i.test(body.url || "")) return json({ detail: "Bad tunnel address." }, 400);
      await store.setUrl(body.url);
      return json({ ok: true });
    }

    const backend = await store.getUrl();
    if (!backend) return json(OFFLINE, 503);

    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, POST",
          "Access-Control-Allow-Headers": "Content-Type",
        },
      });
    }

    // Forward the request to your computer and stream the answer back.
    const target = backend + url.pathname + url.search;
    try {
      const res = await fetch(new Request(target, request), { redirect: "manual" });
      if ([502, 503, 530].includes(res.status) && !res.headers.get("content-type")?.includes("json")) {
        return json(OFFLINE, 503);
      }
      const out = new Response(res.body, res);
      out.headers.set("Access-Control-Allow-Origin", "*");
      out.headers.set("Access-Control-Expose-Headers", "Content-Disposition");
      return out;
    } catch {
      return json(OFFLINE, 503);
    }
  },
};

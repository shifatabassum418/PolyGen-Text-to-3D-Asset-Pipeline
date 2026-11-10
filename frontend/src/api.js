async function request(url, options) {
  let res;
  try {
    res = await fetch(url, options);
  } catch {
    throw new Error("Cannot reach the backend. Start it with: uvicorn app.main:app --port 8000");
  }
  if (!res.ok) {
    let detail = "";
    try { detail = (await res.json()).detail; } catch { /* body was not JSON */ }
    throw new Error(typeof detail === "string" && detail ? detail : `Request failed (${res.status})`);
  }
  return res.json();
}

export function startJob({ prompt, generator, seed, texture }) {
  return request("/api/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, generator, seed, ...(texture ? { texture } : {}) }),
  });
}

export async function pollJob(id, onUpdate, intervalMs = 1500) {
  for (;;) {
    const job = await request(`/api/jobs/${id}`);
    onUpdate(job);
    if (job.status !== "running") return job;
    await new Promise((r) => setTimeout(r, intervalMs));
  }
}

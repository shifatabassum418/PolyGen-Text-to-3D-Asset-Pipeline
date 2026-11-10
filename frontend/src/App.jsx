import { useState } from "react";
import PromptPanel from "./components/PromptPanel.jsx";
import Viewer from "./components/Viewer.jsx";
import { pollJob, startJob } from "./api.js";

// Open an existing export without generating:  http://localhost:5173/?obj=/files/<job>/model.obj&mtl=/files/<job>/model.mtl
function presetFromUrl() {
  const q = new URLSearchParams(window.location.search);
  const obj = q.get("obj");
  const mtl = q.get("mtl");
  if (!obj || !obj.startsWith("/files/")) return null; // only files served by the backend
  return { obj_url: obj, mtl_url: mtl && mtl.startsWith("/files/") ? mtl : null };
}

export default function App() {
  const [prompt, setPrompt] = useState("");
  const [generator, setGenerator] = useState("shape");
  const [texture, setTexture] = useState("controlnet");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [result, setResult] = useState(presetFromUrl);

  async function onGenerate() {
    setBusy(true); setError(""); setStatus("Starting…"); setResult(null);
    try {
      const job = await startJob({ prompt, generator, texture });
      const done = await pollJob(job.id, (j) => setStatus(`Stage: ${j.stage}`));
      if (done.status === "error") throw new Error(done.error);
      setResult(done.result);
      setStatus("Done. Drag to rotate, scroll to zoom.");
    } catch (e) {
      setError(e.message); setStatus("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app">
      <PromptPanel {...{ prompt, setPrompt, generator, setGenerator, texture, setTexture, onGenerate, busy, status, error }} stats={result?.stats} />
      <main className="stage">
        <Viewer objUrl={result?.obj_url} mtlUrl={result?.mtl_url} onError={setError} />
        {!result && !busy && <div className="empty">Describe an object on the left to generate it.</div>}
      </main>
    </div>
  );
}

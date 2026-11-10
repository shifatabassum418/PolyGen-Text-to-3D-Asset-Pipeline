const EXAMPLES = [
  "A rusted, medieval broadsword with a glowing blue sapphire in the hilt",
  "A worn wooden tavern chair",
  "A cracked clay pot with a cork lid",
];

export default function PromptPanel({ prompt, setPrompt, generator, setGenerator, texture, setTexture, onGenerate, busy, status, error, stats }) {
  return (
    <aside className="panel">
      <h1>PolyGen</h1>
      <label>
        Describe the asset
        <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="A rusted, medieval broadsword…" />
      </label>
      <label>
        Mesh model
        <select value={generator} onChange={(e) => setGenerator(e.target.value)}>
          <option value="shape">Shap-E (fast, rough)</option>
          <option value="triposr">TripoSR (slower, cleaner)</option>
        </select>
      </label>
      <label>
        Texture
        <select value={texture} onChange={(e) => setTexture(e.target.value)}>
          <option value="controlnet">Depth-guided (ControlNet)</option>
          <option value="flat">Flat material</option>
          <option value="none">None (geometry only)</option>
        </select>
      </label>
      <button className="primary" disabled={busy || prompt.trim().length < 3} onClick={onGenerate}>
        {busy ? "Generating…" : "Generate model"}
      </button>
      {status && <div className="status">{status}</div>}
      {error && <div className="status error">{error}</div>}
      {stats && (
        <dl className="stats">
          <dt>Faces</dt><dd>{stats.faces.toLocaleString()}</dd>
          <dt>Vertices</dt><dd>{stats.vertices.toLocaleString()}</dd>
          <dt>Watertight</dt><dd>{stats.watertight ? "yes" : "no"}</dd>
          <dt>Parts</dt><dd>{stats.components}</dd>
        </dl>
      )}
      <div className="status">Try an example:</div>
      {EXAMPLES.map((ex) => (
        <button key={ex} className="link" onClick={() => setPrompt(ex)}>{ex}</button>
      ))}
    </aside>
  );
}

import { useState } from "react";

export default function ResultsPanel({ generatedTests, suggestions }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    await navigator.clipboard.writeText(generatedTests);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="fade-in">
      <div className="section-label">generated tests</div>
      <div style={{ position: "relative" }}>
        <pre
          style={{
            background: "var(--ink)",
            color: "#e7ebe8",
            padding: "16px 18px",
            borderRadius: "var(--radius)",
            overflowX: "auto",
            fontFamily: "var(--font-mono)",
            fontSize: 13,
            lineHeight: 1.6,
            margin: 0,
          }}
        >
          {generatedTests}
        </pre>
        <button
          className="btn btn-secondary"
          onClick={handleCopy}
          style={{
            position: "absolute",
            top: 10,
            right: 10,
            background: "var(--panel)",
            fontSize: 12,
            padding: "5px 10px",
          }}
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>

      {suggestions?.length > 0 && (
        <>
          <div className="section-label">suggestions</div>
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {suggestions.map((s, i) => (
              <li
                key={i}
                style={{
                  display: "flex",
                  gap: 10,
                  padding: "8px 0",
                  borderBottom: "1px solid var(--line)",
                  fontSize: 14,
                }}
              >
                <span style={{ color: "var(--warn)" }}>▸</span>
                <span>{s}</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}

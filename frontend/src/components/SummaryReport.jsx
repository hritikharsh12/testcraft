export default function SummaryReport({ filename, language, summary }) {
  const { functions = [], classes = [], imports = [], warnings = [], line_count } = summary;

  return (
    <div className="fade-in">
      <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 14 }}>{filename}</span>
        <span className="tag tag-code">{language}</span>
        <span style={{ fontSize: 13, color: "var(--ink-soft)" }}>{line_count} lines</span>
      </div>

      {functions.length > 0 && (
        <>
          <div className="section-label">functions</div>
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {functions.map((fn) => (
              <li
                key={fn.name}
                style={{
                  display: "flex",
                  alignItems: "baseline",
                  gap: 10,
                  padding: "6px 0",
                  borderBottom: "1px solid var(--line)",
                  fontFamily: "var(--font-mono)",
                  fontSize: 13,
                }}
              >
                <span>
                  {fn.is_async && "async "}
                  {fn.name}({fn.args.join(", ")})
                </span>
                <span style={{ color: "var(--ink-soft)", marginLeft: "auto" }}>line {fn.line_number}</span>
                {!fn.has_docstring && <span className="tag tag-warn">no docstring</span>}
              </li>
            ))}
          </ul>
        </>
      )}

      {classes.length > 0 && (
        <>
          <div className="section-label">classes</div>
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {classes.map((cls) => (
              <li
                key={cls.name}
                style={{
                  padding: "6px 0",
                  borderBottom: "1px solid var(--line)",
                  fontFamily: "var(--font-mono)",
                  fontSize: 13,
                }}
              >
                {cls.name} · {cls.methods.join(", ") || "no methods"}
              </li>
            ))}
          </ul>
        </>
      )}

      {imports.length > 0 && (
        <>
          <div className="section-label">imports</div>
          <p style={{ fontFamily: "var(--font-mono)", fontSize: 13, color: "var(--ink-soft)", margin: 0 }}>
            {imports.join(", ")}
          </p>
        </>
      )}

      {warnings.length > 0 && (
        <>
          <div className="section-label">warnings</div>
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {warnings.map((w, i) => (
              <li key={i} style={{ fontSize: 13, color: "var(--warn)", padding: "3px 0" }}>
                {w}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}

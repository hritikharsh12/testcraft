import { useRef, useState } from "react";

const ALLOWED_EXTENSIONS = [".py", ".js", ".ts", ".java", ".go"];

export default function UploadPanel({ onFileSelected, disabled }) {
  const inputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);
  const [localError, setLocalError] = useState(null);

  function validateAndEmit(file) {
    if (!file) return;
    const ext = "." + file.name.split(".").pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setLocalError(`Unsupported file type "${ext}". Allowed: ${ALLOWED_EXTENSIONS.join(", ")}`);
      return;
    }
    setLocalError(null);
    onFileSelected(file);
  }

  return (
    <div>
      {localError && <div className="error-banner">{localError}</div>}
      <div
        role="button"
        tabIndex={0}
        onClick={() => !disabled && inputRef.current?.click()}
        onKeyDown={(e) => e.key === "Enter" && !disabled && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          if (!disabled) validateAndEmit(e.dataTransfer.files?.[0]);
        }}
        style={{
          border: `1px dashed ${dragOver ? "var(--code)" : "var(--line-strong)"}`,
          borderRadius: "var(--radius)",
          padding: "36px 20px",
          textAlign: "center",
          cursor: disabled ? "not-allowed" : "pointer",
          background: dragOver ? "var(--code-bg)" : "var(--panel)",
          transition: "background 0.12s ease, border-color 0.12s ease",
        }}
      >
        <p style={{ margin: 0, fontFamily: "var(--font-mono)", fontSize: 14, color: "var(--ink-soft)" }}>
          drop a file here, or click to browse
        </p>
        <p style={{ margin: "6px 0 0", fontSize: 12, color: "var(--ink-soft)" }}>
          {ALLOWED_EXTENSIONS.join("  ·  ")}
        </p>
        <input
          ref={inputRef}
          type="file"
          hidden
          disabled={disabled}
          accept={ALLOWED_EXTENSIONS.join(",")}
          onChange={(e) => validateAndEmit(e.target.files?.[0])}
        />
      </div>
    </div>
  );
}

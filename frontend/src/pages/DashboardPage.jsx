import { useState } from "react";
import Navbar from "../components/Navbar";
import UploadPanel from "../components/UploadPanel";
import SummaryReport from "../components/SummaryReport";
import ResultsPanel from "../components/ResultsPanel";
import { uploadCode, generateTests } from "../api/codeClient";

const STEP = { IDLE: "idle", ANALYZING: "analyzing", ANALYZED: "analyzed", GENERATING: "generating", DONE: "done" };

export default function DashboardPage() {
  const [step, setStep] = useState(STEP.IDLE);
  const [submission, setSubmission] = useState(null); // { submission_id, filename, language, summary }
  const [result, setResult] = useState(null); // { generated_tests, suggestions }
  const [error, setError] = useState(null);

  async function handleFileSelected(file) {
    setError(null);
    setResult(null);
    setStep(STEP.ANALYZING);
    try {
      const data = await uploadCode(file);
      setSubmission(data);
      setStep(STEP.ANALYZED);
    } catch (err) {
      setError(err.message || "That file couldn't be parsed. Check it's valid and try again.");
      setStep(STEP.IDLE);
    }
  }

  async function handleGenerate() {
    setError(null);
    setStep(STEP.GENERATING);
    try {
      const data = await generateTests(submission.submission_id);
      setResult(data);
      setStep(STEP.DONE);
    } catch (err) {
      setError(err.message || "Test generation failed. Try again in a moment.");
      setStep(STEP.ANALYZED);
    }
  }

  function reset() {
    setSubmission(null);
    setResult(null);
    setError(null);
    setStep(STEP.IDLE);
  }

  return (
    <div className="app-shell">
      <Navbar />
      <main className="container" style={{ paddingTop: 40, paddingBottom: 80, flex: 1 }}>
        <h1 style={{ fontSize: 22, marginBottom: 4 }}>Upload</h1>
        <p style={{ color: "var(--ink-soft)", fontSize: 14, marginBottom: 20 }}>
          Drop in a source file to see what's testable, then generate tests.
        </p>

        {error && <div className="error-banner">{error}</div>}

        {step === STEP.IDLE && <UploadPanel onFileSelected={handleFileSelected} />}
        {step === STEP.ANALYZING && <div className="panel">Analyzing file…</div>}

        {submission && (step === STEP.ANALYZED || step === STEP.GENERATING || step === STEP.DONE) && (
          <div className="panel" style={{ marginTop: 16 }}>
            <SummaryReport
              filename={submission.filename}
              language={submission.language}
              summary={submission.summary}
            />

            <div className="btn-row" style={{ marginTop: 24 }}>
              <button className="btn" onClick={handleGenerate} disabled={step === STEP.GENERATING}>
                {step === STEP.GENERATING ? "Generating…" : "Generate tests"}
              </button>
              <button className="btn btn-secondary" onClick={reset}>
                Upload a different file
              </button>
            </div>
          </div>
        )}

        {result && step === STEP.DONE && (
          <div className="panel" style={{ marginTop: 16 }}>
            <ResultsPanel generatedTests={result.generated_tests} suggestions={result.suggestions} />
          </div>
        )}
      </main>
    </div>
  );
}

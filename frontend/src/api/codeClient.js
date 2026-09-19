import { apiFetch } from "./http";

export async function uploadCode(file) {
  const formData = new FormData();
  formData.append("file", file);
  return apiFetch("/api/v1/upload", { method: "POST", body: formData });
}

export async function generateTests(submissionId) {
  return apiFetch(`/api/v1/generate/${submissionId}`, { method: "POST" });
}

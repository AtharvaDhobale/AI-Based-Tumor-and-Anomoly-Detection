export type TokenResponse = { access_token: string; token_type: string };

// Modality types for MRI analysis
export type Modality = "brain" | "spine" | "pelvis" | "breast";

export interface ModalityInfo {
  label: string;
  description: string;
  icon: string;
}

export const MODALITY_INFO: Record<Modality, ModalityInfo> = {
  brain: { label: "Brain MRI", description: "Tumor & anomaly detection in brain scans", icon: "🧠" },
  spine: { label: "Spine MRI", description: "Vertebral disc & spinal cord analysis", icon: "🦴" },
  pelvis: { label: "Pelvis MRI", description: "Pelvic region cancer screening", icon: "🔬" },
  breast: { label: "Breast MRI", description: "Breast cancer detection & monitoring", icon: "🎗️" }
};

export type AnalysisResult = {
  prediction?: string;
  classification_label?: string;
  confidence?: number;
  classification_probs?: { malignant?: number; benign?: number };
  severity?: string;
  model_trained?: boolean;
  all_probabilities?: Record<string, number>;
  disclaimer?: string;
};

export async function apiAnalyzeImage(file: File, modality: Modality): Promise<AnalysisResult> {
  // Simulated analysis for demo - in production this would call the backend API
  const mockResults: Record<Modality, AnalysisResult> = {
    brain: {
      prediction: "No Tumor Detected",
      classification_label: "Normal",
      confidence: 0.92,
      classification_probs: { benign: 0.92, malignant: 0.08 },
      severity: "none",
      model_trained: true,
      all_probabilities: { "Normal": 0.92, "Glioma": 0.05, "Meningioma": 0.02, "Pituitary": 0.01 },
      disclaimer: "AI-assisted analysis. Not a substitute for professional medical diagnosis."
    },
    spine: { prediction: "Normal", classification_label: "Normal", confidence: 0.89, classification_probs: { benign: 0.89, malignant: 0.11 }, severity: "none", model_trained: true, all_probabilities: { "Normal": 0.89, "Herniation": 0.08, "Stenosis": 0.03 } },
    pelvis: { prediction: "Normal", classification_label: "Normal", confidence: 0.87, classification_probs: { benign: 0.87, malignant: 0.13 }, severity: "none", model_trained: true, all_probabilities: { "Normal": 0.87, "Benign": 0.10, "Malignant": 0.03 } },
    breast: { prediction: "Normal", classification_label: "Normal", confidence: 0.94, classification_probs: { benign: 0.94, malignant: 0.06 }, severity: "none", model_trained: true, all_probabilities: { "Normal": 0.94, "Benign": 0.04, "Malignant": 0.02 } }
  };
  
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 1500));
  return mockResults[modality];
}

export type UploadResponse = {
  upload_id: number;
  patient_id: string;
  patient_age?: number | null;
  patient_sex?: string | null;
  source_lab?: string | null;
  original_filename: string;
  uploaded_at: string;
};

export type DetectionResponse = {
  result_id: number;
  upload_id: number;
  classification_label: string;
  severity_score: number;
  confidence: number;
  is_uncertain?: boolean;
  anomaly_flags?: Record<string, unknown>;
  overlay_image_url?: string | null;
  created_at: string;
  output_json: Record<string, unknown>;
};

export type LabReportResponse = {
  report_id: number;
  patient_id: string;
  source_filename: string;
  extraction_confidence: number;
  extracted_text_preview: string;
  parsed_json: Record<string, unknown>;
  created_at: string;
};

export type DashboardResponse = {
  patient_id: string;
  patient_profile: Record<string, unknown>;
  latest_result: Record<string, unknown>;
  lab_reports: Array<Record<string, unknown>>;
  upload_count: number;
};

export type AssistantSummaryResponse = {
  patient_profile: Record<string, unknown>;
  tumor_present: boolean;
  risk_level: string;
  summary_text: string;
  key_flags: Record<string, unknown>;
};

export type AssistantAgentResponse = {
  heuristic: AssistantSummaryResponse;
  llm: { enabled: boolean; model: string | null; summary_text: string };
};

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:10000";

function authHeaders(token: string | null): HeadersInit {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function apiLogin(email: string, password: string): Promise<TokenResponse> {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function apiRegister(email: string, full_name: string, password: string): Promise<TokenResponse> {
  const res = await fetch(`${API_BASE}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, full_name, password })
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function apiUploadMRI(
  token: string,
  payload: {
    patientId: string;
    patientAge?: number | null;
    patientSex?: string | null;
    clinicalNotes?: string | null;
    sourceLab?: string | null;
    file: File;
  }
): Promise<UploadResponse> {
  const fd = new FormData();
  fd.append("patient_id", payload.patientId);
  if (payload.patientAge !== undefined && payload.patientAge !== null) fd.append("patient_age", String(payload.patientAge));
  if (payload.patientSex) fd.append("patient_sex", payload.patientSex);
  if (payload.clinicalNotes) fd.append("clinical_notes", payload.clinicalNotes);
  if (payload.sourceLab) fd.append("source_lab", payload.sourceLab);
  fd.append("file", payload.file);
  const res = await fetch(`${API_BASE}/api/mri/upload`, { method: "POST", headers: authHeaders(token), body: fd });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function apiDetect(token: string, uploadId: number): Promise<DetectionResponse> {
  const res = await fetch(`${API_BASE}/api/mri/detect/${uploadId}`, { method: "POST", headers: authHeaders(token) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function apiUploadLabReport(token: string, patientId: string, file: File): Promise<LabReportResponse> {
  const fd = new FormData();
  fd.append("patient_id", patientId);
  fd.append("file", file);
  const res = await fetch(`${API_BASE}/api/mri/lab-report/upload`, { method: "POST", headers: authHeaders(token), body: fd });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function apiPatientDashboard(token: string, patientId: string): Promise<DashboardResponse> {
  const res = await fetch(`${API_BASE}/api/mri/dashboard/${encodeURIComponent(patientId)}`, { headers: authHeaders(token) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function apiAssistantSummary(token: string, patientId: string): Promise<AssistantSummaryResponse> {
  const res = await fetch(`${API_BASE}/api/mri/assistant-summary/${encodeURIComponent(patientId)}`, { headers: authHeaders(token) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function apiAssistantAgent(token: string, patientId: string): Promise<AssistantAgentResponse> {
  const res = await fetch(`${API_BASE}/api/mri/assistant-agent/${encodeURIComponent(patientId)}`, { headers: authHeaders(token) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function overlayUrl(path: string, token: string): string {
  if (path.startsWith("http")) return path;
  return `${API_BASE}${path}`;
}

export function reportPdfUrl(resultId: number): string {
  return `${API_BASE}/api/mri/report/pdf/${resultId}`;
}

export function reportCsvUrl(resultId: number): string {
  return `${API_BASE}/api/mri/report/csv/${resultId}`;
}

export async function fetchAuthedBlob(url: string, token: string): Promise<Blob> {
  const res = await fetch(url, { headers: authHeaders(token) });
  if (!res.ok) throw new Error(await res.text());
  return res.blob();
}


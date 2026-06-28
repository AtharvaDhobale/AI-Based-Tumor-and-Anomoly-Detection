import React from "react";
import {
  apiDetect,
  apiAssistantAgent,
  apiAssistantSummary,
  apiPatientDashboard,
  apiUploadLabReport,
  apiUploadMRI,
  fetchAuthedBlob,
  reportCsvUrl,
  reportPdfUrl,
  type DashboardResponse,
  type DetectionResponse,
  type AssistantSummaryResponse,
  type AssistantAgentResponse
} from "../lib/api";

type Props = { token: string };
type ProbabilityMap = { benign: number; malignant: number };

function toPercent(v: number): string { return `${(v * 100).toFixed(1)}%`; }
function clamp(v: number): number { return Math.max(0, Math.min(1, v)); }

function extractMetrics(result: DetectionResponse) {
  const out = result.output_json as Record<string, unknown>;
  const probsRaw = (out.classification_probs ?? {}) as Record<string, unknown>;
  const mask = (out.mask_stats ?? {}) as Record<string, unknown>;
  const consensus = (out.model_consensus ?? {}) as Record<string, unknown>;
  const quality = (out.quality_metrics ?? {}) as Record<string, unknown>;

  const probs: ProbabilityMap = {
    benign: clamp(Number(probsRaw.benign ?? (result.classification_label === "benign" ? result.confidence : 1 - result.confidence))),
    malignant: clamp(Number(probsRaw.malignant ?? (result.classification_label === "malignant" ? result.confidence : 1 - result.confidence)))
  };

  const areaRatio = clamp(Number(mask.area_ratio ?? 0));
  const areaPx = Number(mask.area_px ?? 0);
  const areaMm2 = Number(mask.area_mm2_proxy ?? 0);
  const diamPx = Number(mask.estimated_tumor_diameter_px ?? 0);
  const diamMm = Number(mask.estimated_tumor_diameter_mm ?? 0);
  const region = String(mask.region ?? "n/a");
  const centroid = mask.centroid_xy as { x: number; y: number } | undefined;
  const bbox = mask.bbox_xyxy as { x_min: number; y_min: number; x_max: number; y_max: number } | undefined;

  const edgeDensity = clamp(0.55 * areaRatio + 0.45 * result.severity_score);
  const spreadRisk = clamp(0.5 * areaRatio + 0.5 * probs.malignant);
  const clsMargin = clamp(Number(consensus.classification_margin ?? Math.abs(probs.malignant - probs.benign)));
  const qualStd = Number(quality.std ?? 0);
  const qualEntropy = Number(quality.entropy ?? 0);

  const riskBand =
    result.severity_score >= 0.72 ? "Critical" :
    result.severity_score >= 0.52 ? "High" :
    result.severity_score >= 0.22 ? "Moderate" : "Low";

  const anomalySummary =
    areaRatio >= 0.22 ? "Significant hyperintense mass detected in segmented slices." :
    areaRatio >= 0.10 ? "Moderate spatial anomaly burden flagged in tissue metrics." :
    areaRatio > 0.01 ? "Focal micro-anomaly cluster detected." :
                       "No notable anomaly footprints detected in tissue.";

  return {
    probs, areaRatio, areaPx, areaMm2, diamPx, diamMm, region, centroid, bbox,
    edgeDensity, spreadRisk, clsMargin, qualStd, qualEntropy, riskBand, anomalySummary
  };
}

function getRiskClass(band: string): string {
  if (band === "Critical") return "critical";
  if (band === "High") return "warning";
  if (band === "Moderate") return "info";
  return "success";
}

function getRiskIcon(band: string): string {
  if (band === "Critical") return "🚨";
  if (band === "High") return "⚠";
  if (band === "Moderate") return "🛈";
  return "✓";
}

export default function UploadDetectCard({ token }: Props) {
  const [patientId, setPatientId] = React.useState("P001");
  const [patientAge, setPatientAge] = React.useState<number | null>(45);
  const [patientSex, setPatientSex] = React.useState("Male");
  const [sourceLab, setSourceLab] = React.useState("Central Imaging Unit");
  const [clinicalNotes, setClinicalNotes] = React.useState("");
  
  const [file, setFile] = React.useState<File | null>(null);
  const [labFile, setLabFile] = React.useState<File | null>(null);
  const [uploadId, setUploadId] = React.useState<number | null>(null);
  const [result, setResult] = React.useState<DetectionResponse | null>(null);
  const [dashboard, setDashboard] = React.useState<DashboardResponse | null>(null);
  const [assistantSummary, setAssistantSummary] = React.useState<AssistantSummaryResponse | null>(null);
  const [assistantAgent, setAssistantAgent] = React.useState<AssistantAgentResponse | null>(null);
  const [overlayUrl, setOverlayUrl] = React.useState<string | null>(null);
  
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [dragActive, setDragActive] = React.useState(false);

  React.useEffect(() => {
    return () => {
      if (overlayUrl) URL.revokeObjectURL(overlayUrl);
    };
  }, [overlayUrl]);

  async function upload() {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setUploadId(null);
    if (overlayUrl) {
      URL.revokeObjectURL(overlayUrl);
      setOverlayUrl(null);
    }

    try {
      const up = await apiUploadMRI(token, {
        patientId,
        patientAge,
        patientSex,
        sourceLab,
        clinicalNotes,
        file
      });
      setUploadId(up.upload_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function detect() {
    if (!uploadId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await apiDetect(token, uploadId);
      setResult(res);
      const [summary, agent] = await Promise.all([
        apiAssistantSummary(token, patientId),
        apiAssistantAgent(token, patientId)
      ]);
      setAssistantSummary(summary);
      setAssistantAgent(agent);

      if (res.overlay_image_url) {
        const blob = await fetchAuthedBlob(res.overlay_image_url, token);
        const obj = URL.createObjectURL(blob);
        setOverlayUrl(obj);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function uploadLab() {
    if (!labFile) return;
    setLoading(true);
    setError(null);
    try {
      await apiUploadLabReport(token, patientId, labFile);
      const [dash, summary, agent] = await Promise.all([
        apiPatientDashboard(token, patientId),
        apiAssistantSummary(token, patientId),
        apiAssistantAgent(token, patientId)
      ]);
      setDashboard(dash);
      setAssistantSummary(summary);
      setAssistantAgent(agent);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function loadDashboard() {
    setLoading(true);
    setError(null);
    try {
      const [dash, summary, agent] = await Promise.all([
        apiPatientDashboard(token, patientId),
        apiAssistantSummary(token, patientId),
        apiAssistantAgent(token, patientId)
      ]);
      setDashboard(dash);
      setAssistantSummary(summary);
      setAssistantAgent(agent);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function downloadAuthed(url: string, filename: string) {
    try {
      const blob = await fetchAuthedBlob(url, token);
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = filename;
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  function handleDrag(e: React.DragEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  }

  return (
    <div className="workstation-layout clinic-fade-in-up">
      {/* ── Left Column: Ingestion Controls ── */}
      <div className="grid-gap-24">
        {/* Patient Registration Details */}
        <div className="card-clinical">
          <div className="card-clinical-header">
            <h2 className="card-clinical-title"><span>👤</span> Patient Admission</h2>
            {uploadId && <span className="pill-clinical success">Record Created</span>}
          </div>
          <div className="card-clinical-body">
            <div className="grid-gap-20">
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Patient ID / MRN</label>
                  <input
                    id="patient-id"
                    className="form-input-field"
                    type="text"
                    value={patientId}
                    onChange={(e) => setPatientId(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Age (Years)</label>
                  <input
                    id="patient-age"
                    className="form-input-field"
                    type="number"
                    value={patientAge ?? ""}
                    onChange={(e) => setPatientAge(e.target.value ? Number(e.target.value) : null)}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Biological Sex</label>
                  <select
                    id="patient-sex"
                    className="form-input-field"
                    value={patientSex}
                    onChange={(e) => setPatientSex(e.target.value)}
                  >
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Referring Facility</label>
                  <input
                    id="source-lab"
                    className="form-input-field"
                    type="text"
                    value={sourceLab}
                    onChange={(e) => setSourceLab(e.target.value)}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Admitting Clinical Notes</label>
                <textarea
                  id="clinical-notes"
                  className="form-input-field"
                  value={clinicalNotes}
                  onChange={(e) => setClinicalNotes(e.target.value)}
                  placeholder="Patient background, medical history, focal neurological signs..."
                />
              </div>
            </div>
          </div>
        </div>

        {/* Scan & Lab File Upload */}
        <div className="card-clinical">
          <div className="card-clinical-header">
            <h2 className="card-clinical-title"><span>📡</span> Diagnostic Scan Ingestion</h2>
          </div>
          <div className="card-clinical-body">
            <div className="grid-gap-20">
              <div
                id="mri-drop-zone"
                className={`clinical-upload-zone ${dragActive ? "drag-active" : ""}`}
                onClick={() => document.getElementById("mri-file-input")?.click()}
                onDragEnter={handleDrag}
                onDragOver={handleDrag}
                onDragLeave={handleDrag}
                onDrop={handleDrop}
              >
                <input
                  id="mri-file-input"
                  type="file"
                  accept="image/*"
                  style={{ display: "none" }}
                  onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                />
                <span className="upload-icon-pulse">🧲</span>
                <div className="upload-primary-text">Ingest MRI Image Slice</div>
                <div className="upload-sub-text">Drag & drop PNG/JPG scan file here</div>
                {file && (
                  <div className="upload-file-status">
                    <span>✓</span> {file.name}
                  </div>
                )}
              </div>

              <div className="form-group">
                <label className="form-label">Associated Lab Report (PDF / TXT)</label>
                <input
                  id="lab-file-input"
                  className="form-input-field"
                  type="file"
                  accept=".pdf,.txt"
                  onChange={(e) => setLabFile(e.target.files?.[0] ?? null)}
                />
                {labFile && <div className="upload-file-status"><span>📄</span> {labFile.name}</div>}
              </div>

              {error && (
                <div className="alert alert-red">
                  <span>⚠</span>
                  <span>{error}</span>
                </div>
              )}

              <div className="btn-group-clinical">
                <button
                  id="btn-upload"
                  className="btn-clinical primary"
                  disabled={loading || !file}
                  onClick={upload}
                  style={{ flex: 1 }}
                >
                  {loading && !uploadId ? (
                    <><span className="clinical-spinner" style={{ width: 12, height: 12, borderWidth: 2 }}></span> Ingesting Scan...</>
                  ) : "1. Ingest Scan"}
                </button>
                <button
                  id="btn-detect"
                  className="btn-clinical primary"
                  disabled={loading || !uploadId}
                  onClick={detect}
                  style={{ flex: 1 }}
                >
                  {loading && uploadId ? (
                    <><span className="clinical-spinner" style={{ width: 12, height: 12, borderWidth: 2 }}></span> Diagnosing...</>
                  ) : "2. Run AI Diagnostic"}
                </button>
              </div>

              <div className="btn-group-clinical">
                <button
                  id="btn-upload-lab"
                  className="btn-clinical secondary"
                  disabled={loading || !labFile}
                  onClick={uploadLab}
                  style={{ flex: 1 }}
                >
                  Parse Lab
                </button>
                <button
                  id="btn-load-dashboard"
                  className="btn-clinical secondary"
                  disabled={loading}
                  onClick={loadDashboard}
                  style={{ flex: 1 }}
                >
                  EHR Dashboard
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Right Column: AI Diagnostics Workspace ── */}
      <div className="grid-gap-24">
        {/* Placeholder when no scan is run yet */}
        {!result && !loading && (
          <div className="card-clinical" style={{ minHeight: 400, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <div className="clinic-loader-wrapper">
              <div style={{ fontSize: 64, animation: "pulse-indicator 2s infinite" }}>🔬</div>
              <div style={{ fontSize: 18, fontWeight: 700, color: "var(--text-primary)" }}>PACS Workstation Ready</div>
              <p className="text-muted text-align-center" style={{ maxWidth: 360 }}>
                Please select patient admission details, upload an MRI scan slice, and click <strong>Ingest Scan</strong> to begin diagnostic review.
              </p>
            </div>
          </div>
        )}

        {/* Loading Spinner */}
        {loading && (
          <div className="card-clinical" style={{ minHeight: 400, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <div className="clinic-loader-wrapper">
              <div className="clinical-spinner"></div>
              <div style={{ fontWeight: 600 }}>Executing Multi-Modality AI Diagnostic Inferences...</div>
              <div className="text-muted text-xs">U-Net Segmenter & ResNet18 Classifier telemetry active</div>
            </div>
          </div>
        )}

        {/* Diagnostic Results */}
        {result && (() => {
          const metrics = extractMetrics(result);
          const isMalignant = result.classification_label === "malignant";
          const riskCls = getRiskClass(metrics.riskBand);
          return (
            <div className="grid-gap-24">
              <div className="card-clinical">
                {/* Diagnostic Header */}
                <div className="diagnostic-report-header">
                  <div>
                    <div className="text-muted text-xs" style={{ marginBottom: 4, fontWeight: 600 }}>AI DIAGNOSTIC INFERENCE RESULT</div>
                    <div className={`diagnostic-label-badge ${isMalignant ? "malignant" : "benign"}`}>
                      {result.classification_label.toUpperCase()}
                      {result.is_uncertain && (
                        <span className="pill-clinical warning" style={{ marginLeft: 12, verticalAlign: "middle" }}>
                          <span className="pulse-bullet"></span> Uncertainty Warning
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="btn-group-clinical">
                    <button
                      className="btn-clinical secondary btn-sm"
                      onClick={() => downloadAuthed(reportPdfUrl(result.result_id), `EHR_Report_${result.result_id}.pdf`)}
                    >
                      Export PDF Report
                    </button>
                    <button
                      className="btn-clinical secondary btn-sm"
                      onClick={() => downloadAuthed(reportCsvUrl(result.result_id), `EHR_Data_${result.result_id}.csv`)}
                    >
                      Export CSV Metrics
                    </button>
                  </div>
                </div>

                {/* EHR High-Density Metric Grid */}
                <div className="clinical-metric-grid">
                  <div className="clinical-metric-tile">
                    <div className="clinical-metric-title">Scan Confidence</div>
                    <div className={`clinical-metric-value ${isMalignant ? "critical" : "success"}`}>
                      {toPercent(result.confidence)}
                    </div>
                    <div className="clinical-metric-subtitle">Model prediction certainty</div>
                  </div>

                  <div className="clinical-metric-tile">
                    <div className="clinical-metric-title">Composite Severity</div>
                    <div className={`clinical-metric-value ${result.severity_score >= 0.52 ? "critical" : result.severity_score >= 0.22 ? "warning" : "success"}`}>
                      {Math.round(result.severity_score * 100)}%
                    </div>
                    <div className="clinical-metric-subtitle">Aggregate lesion severity</div>
                  </div>

                  <div className="clinical-metric-tile">
                    <div className="clinical-metric-title">Lesion Max Diameter</div>
                    <div className={`clinical-metric-value ${metrics.diamMm >= 25 ? "critical" : metrics.diamMm >= 10 ? "warning" : "primary"}`}>
                      {metrics.diamMm > 0 ? `${metrics.diamMm} mm` : "N/A"}
                    </div>
                    <div className="clinical-metric-subtitle">Segmented lesion span</div>
                  </div>

                  <div className="clinical-metric-tile">
                    <div className="clinical-metric-title">Volumetric Footprint</div>
                    <div className="clinical-metric-value primary">
                      {metrics.areaMm2 > 0 ? `${metrics.areaMm2} mm²` : "N/A"}
                    </div>
                    <div className="clinical-metric-subtitle">{metrics.areaPx > 0 ? `${metrics.areaPx} pixels` : "N/A"}</div>
                  </div>

                  <div className="clinical-metric-tile">
                    <div className="clinical-metric-title">Anatomical Region</div>
                    <div className="clinical-metric-value primary" style={{ fontSize: 13, letterSpacing: 0, textTransform: "capitalize" }}>
                      {metrics.region.replace("_", " ")}
                    </div>
                    <div className="clinical-metric-subtitle">
                      {metrics.centroid ? `Centroid: ${metrics.centroid.x.toFixed(0)}x, ${metrics.centroid.y.toFixed(0)}y` : "Centroid: N/A"}
                    </div>
                  </div>
                </div>

                {/* Analysis Body */}
                <div className="card-clinical-body">
                  <div className="section-title"><span>🛡️</span> Clinical Risk Assessment</div>
                  <div className={`risk-notification-panel ${riskCls}`}>
                    <div className="risk-panel-icon">{getRiskIcon(metrics.riskBand)}</div>
                    <div>
                      <div className="risk-panel-title">{metrics.riskBand} Risk Category</div>
                      <div className="risk-panel-desc">{metrics.anomalySummary}</div>
                    </div>
                  </div>

                  {/* Probabilities */}
                  <div className="section-title margin-top-20"><span>📊</span> Predictor Probabilities</div>
                  <div className="clinical-progress-container">
                    <div className="clinical-progress-labels">
                      <span className="text-secondary">Malignant Inference</span>
                      <span style={{ color: "var(--status-critical)" }}>{toPercent(metrics.probs.malignant)}</span>
                    </div>
                    <div className="clinical-progress-track">
                      <div className="clinical-progress-fill critical" style={{ width: `${metrics.probs.malignant * 100}%` }}></div>
                    </div>
                  </div>

                  <div className="clinical-progress-container">
                    <div className="clinical-progress-labels">
                      <span className="text-secondary">Benign / Healthy Tissue Inference</span>
                      <span style={{ color: "var(--status-normal)" }}>{toPercent(metrics.probs.benign)}</span>
                    </div>
                    <div className="clinical-progress-track">
                      <div className="clinical-progress-fill success" style={{ width: `${metrics.probs.benign * 100}%` }}></div>
                    </div>
                  </div>

                  {/* Tissue Burden */}
                  <div className="section-title margin-top-20"><span>📐</span> Lesion Morphology & Burden Indicators</div>
                  <div className="clinical-progress-container">
                    <div className="clinical-progress-labels">
                      <span className="text-secondary">Anomaly Area Load</span>
                      <span style={{ color: "var(--status-warning)" }}>{toPercent(metrics.areaRatio)}</span>
                    </div>
                    <div className="clinical-progress-track">
                      <div className="clinical-progress-fill warning" style={{ width: `${metrics.areaRatio * 100}%` }}></div>
                    </div>
                  </div>

                  <div className="clinical-progress-container">
                    <div className="clinical-progress-labels">
                      <span className="text-secondary">Boundary Texture Complexity</span>
                      <span style={{ color: "var(--status-warning)" }}>{toPercent(metrics.edgeDensity)}</span>
                    </div>
                    <div className="clinical-progress-track">
                      <div className="clinical-progress-fill warning" style={{ width: `${metrics.edgeDensity * 100}%` }}></div>
                    </div>
                  </div>

                  <div className="clinical-progress-container">
                    <div className="clinical-progress-labels">
                      <span className="text-secondary">Tissue Dissemination Risk</span>
                      <span style={{ color: "var(--status-critical)" }}>{toPercent(metrics.spreadRisk)}</span>
                    </div>
                    <div className="clinical-progress-track">
                      <div className="clinical-progress-fill critical" style={{ width: `${metrics.spreadRisk * 100}%` }}></div>
                    </div>
                  </div>

                  {/* Flags */}
                  {result.anomaly_flags && Object.keys(result.anomaly_flags).length > 0 && (
                    <>
                      <div className="section-title margin-top-20"><span>🚩</span> Telemetry Anomaly Flags</div>
                      <div className="flag-list">
                        {Object.entries(result.anomaly_flags).map(([key, val]) => (
                          <div key={key} className={`flag-item ${val ? "active" : "inactive"}`}>
                            <span className="flag-item-icon">{val ? "⚠" : "✓"}</span>
                            <span className="flag-item-text">
                              {key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}
                            </span>
                            <span style={{ marginLeft: "auto", fontFamily: "JetBrains Mono, monospace" }}>
                              {String(val)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </>
                  )}

                  {/* Impression Box */}
                  <div className="section-title margin-top-20"><span>📋</span> EHR Clinical Impression Guidance</div>
                  <div className="findings-sheet-box">
                    <ul className="findings-list">
                      <li>Compare AI contour lines side-by-side with raw multi-sequence T2/FLAIR scans.</li>
                      <li>Critical & High risk bands require immediate radiologist sign-off & surgical consultation.</li>
                      <li>Correlate biomarker extractions with recent patient laboratory reports.</li>
                      <li>Diagnostic records archived automatically in PACS database under patient ID.</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Side-by-Side PACS Image Comparison */}
              {(file || overlayUrl) && (
                <div className="card-clinical">
                  <div className="card-clinical-header">
                    <h2 className="card-clinical-title"><span>🖼️</span> PACS Viewports</h2>
                  </div>
                  <div className="card-clinical-body">
                    <div className="pacs-compare-grid">
                      {file && (
                        <div className="pacs-image-viewport">
                          <div className="pacs-viewport-overlay">Raw Scan Slice</div>
                          <img src={URL.createObjectURL(file)} alt="Original Scan" />
                        </div>
                      )}
                      {overlayUrl && (
                        <div className="pacs-image-viewport">
                          <div className="pacs-viewport-overlay" style={{ color: "var(--color-primary-hover)" }}>U-Net Overlay Contour</div>
                          <img src={overlayUrl} alt="AI Segmentation Mask Overlay" />
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })()}

        {/* Patient Dashboard Overview */}
        {dashboard && (
          <div className="card-clinical">
            <div className="card-clinical-header">
              <h2 className="card-clinical-title"><span>◫</span> Patient Case Overview</h2>
              <span className="pill-clinical info">{dashboard.upload_count} Ingested Studies</span>
            </div>
            <div className="card-clinical-body">
              <div className="form-row">
                {/* Patient Profile info */}
                <div>
                  <div className="section-title">Patient Profile Summary</div>
                  {[
                    ["ID / MRN", dashboard.patient_id],
                    ["Age (Years)", (dashboard.patient_profile as Record<string, unknown>).age],
                    ["Biological Sex", (dashboard.patient_profile as Record<string, unknown>).sex],
                    ["Origin Laboratory", (dashboard.patient_profile as Record<string, unknown>).source_lab]
                  ].map(([label, val]) => (
                    <div key={String(label)} className="patient-profile-item">
                      <span className="patient-profile-label">{String(label)}</span>
                      <span className="patient-profile-value">{String(val ?? "—")}</span>
                    </div>
                  ))}
                </div>

                {/* Latest Scan Findings */}
                <div>
                  <div className="section-title">Latest Diagnostic Inferences</div>
                  {(() => {
                    const lr = dashboard.latest_result as Record<string, unknown>;
                    const ms = (lr.output_json as Record<string, unknown>)?.mask_stats as Record<string, unknown> ?? {};
                    return [
                      ["Classification Label", lr.classification_label],
                      ["Classification Confidence", typeof lr.confidence === "number" ? toPercent(lr.confidence) : "—"],
                      ["Severity Score Index", typeof lr.severity_score === "number" ? `${Math.round(lr.severity_score * 100)}%` : "—"],
                      ["Target Lesion Region", ms.region],
                      ["Estimated Max Diameter", ms.estimated_tumor_diameter_mm ? `${ms.estimated_tumor_diameter_mm} mm` : "—"],
                      ["Area Load Proxy", ms.area_mm2_proxy ? `${ms.area_mm2_proxy} mm²` : "—"]
                    ].map(([label, val]) => (
                      <div key={String(label)} className="patient-profile-item">
                        <span className="patient-profile-label">{String(label)}</span>
                        <span className="patient-profile-value">{String(val ?? "—")}</span>
                      </div>
                    ));
                  })()}
                </div>
              </div>

              {/* Lab Reports */}
              {dashboard.lab_reports.length > 0 && (
                <div className="margin-top-20">
                  <div className="section-title">Associated Laboratory Records</div>
                  <div className="flag-list">
                    {dashboard.lab_reports.slice(0, 3).map((r, idx) => (
                      <div key={idx} className="flag-item inactive">
                        <span className="flag-item-icon">📄</span>
                        <span className="flag-item-text">{String(r.source_filename ?? "unnamed_report.txt")}</span>
                        <span style={{ marginLeft: "auto", fontSize: 11, color: "var(--text-muted)", fontFamily: "JetBrains Mono, monospace" }}>
                          Confidence: {r.extraction_confidence ? toPercent(Number(r.extraction_confidence)) : "—"}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* AI Clinical Assistant Summary */}
        {assistantSummary && (
          <div className="clinical-assistant-container clinic-fade-in-up">
            <div className="clinical-assistant-header">
              <div className="clinical-assistant-title">🤖 AI Diagnostic Assistant — Summary Transcript</div>
              <div className="flex-center gap-2">
                <span className={`pill-clinical ${assistantSummary.tumor_present ? "critical" : "success"}`}>
                  Signal: {assistantSummary.tumor_present ? "Abnormal" : "Normal"}
                </span>
                <span className={`pill-clinical ${assistantSummary.risk_level === "critical" || assistantSummary.risk_level === "high" ? "critical" : "warning"}`}>
                  Risk: {assistantSummary.risk_level}
                </span>
              </div>
            </div>
            <div className="clinical-assistant-body">
              <pre className="clinical-assistant-text">{assistantSummary.summary_text}</pre>
            </div>
          </div>
        )}

        {/* LLM Agent Summary */}
        {assistantAgent?.llm?.enabled && assistantAgent.llm.summary_text && (
          <div className="clinical-assistant-container clinic-fade-in-up">
            <div className="clinical-assistant-header">
              <div className="clinical-assistant-title">✨ Clinical AI Agent — LLM Diagnostic Insight</div>
              <span className="pill-clinical info">{String(assistantAgent.llm.model ?? "EHR AI")}</span>
            </div>
            <div className="clinical-assistant-body">
              <pre className="clinical-assistant-text">{assistantAgent.llm.summary_text}</pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

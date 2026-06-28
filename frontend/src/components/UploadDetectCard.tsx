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
  const mask     = (out.mask_stats ?? {}) as Record<string, unknown>;
  const consensus = (out.model_consensus ?? {}) as Record<string, unknown>;
  const quality  = (out.quality_metrics ?? {}) as Record<string, unknown>;

  const probs: ProbabilityMap = {
    benign:    clamp(Number(probsRaw.benign    ?? (result.classification_label === "benign"    ? result.confidence : 1 - result.confidence))),
    malignant: clamp(Number(probsRaw.malignant ?? (result.classification_label === "malignant" ? result.confidence : 1 - result.confidence))),
  };

  const areaRatio    = clamp(Number(mask.area_ratio ?? 0));
  const areaPx       = Number(mask.area_px ?? 0);
  const areaMm2      = Number(mask.area_mm2_proxy ?? 0);
  const diamPx       = Number(mask.estimated_tumor_diameter_px ?? 0);
  const diamMm       = Number(mask.estimated_tumor_diameter_mm ?? 0);
  const region       = String(mask.region ?? "n/a");
  const centroid     = mask.centroid_xy as { x: number; y: number } | undefined;
  const bbox         = mask.bbox_xyxy as { x_min: number; y_min: number; x_max: number; y_max: number } | undefined;

  const edgeDensity  = clamp(0.55 * areaRatio + 0.45 * result.severity_score);
  const spreadRisk   = clamp(0.5 * areaRatio + 0.5 * probs.malignant);

  const clsMargin    = clamp(Number(consensus.classification_margin ?? Math.abs(probs.malignant - probs.benign)));
  const qualStd      = Number(quality.std ?? 0);
  const qualEntropy  = Number(quality.entropy ?? 0);

  const riskBand =
    result.severity_score >= 0.8  ? "Critical" :
    result.severity_score >= 0.55 ? "High"     :
    result.severity_score >= 0.3  ? "Moderate" : "Low";

  const anomalySummary =
    areaRatio >= 0.3  ? "Large anomaly footprint — significant tumour burden in segmented region." :
    areaRatio >= 0.12 ? "Moderate anomaly footprint with clinically notable mass effect." :
    areaRatio > 0.02  ? "Small focal anomaly region identified. Further evaluation recommended." :
                        "No dominant anomaly burden detected in current segmentation.";

  return {
    probs, areaRatio, areaPx, areaMm2, diamPx, diamMm, region, centroid, bbox,
    edgeDensity, spreadRisk, clsMargin, qualStd, qualEntropy, riskBand, anomalySummary,
  };
}

function riskClass(band: string): string {
  if (band === "Critical") return "critical";
  if (band === "High")     return "high";
  if (band === "Moderate") return "moderate";
  return "low";
}

function riskIcon(band: string): string {
  if (band === "Critical") return "🔴";
  if (band === "High")     return "🟡";
  if (band === "Moderate") return "🔵";
  return "🟢";
}

export default function UploadDetectCard({ token }: Props) {
  const [patientId,    setPatientId]    = React.useState("P001");
  const [patientAge,   setPatientAge]   = React.useState<number | null>(45);
  const [patientSex,   setPatientSex]   = React.useState("Male");
  const [sourceLab,    setSourceLab]    = React.useState("Central Radiology Lab");
  const [clinicalNotes, setClinicalNotes] = React.useState("");
  const [file,     setFile]     = React.useState<File | null>(null);
  const [labFile,  setLabFile]  = React.useState<File | null>(null);
  const [uploadId, setUploadId] = React.useState<number | null>(null);
  const [result,   setResult]   = React.useState<DetectionResponse | null>(null);
  const [dashboard, setDashboard] = React.useState<DashboardResponse | null>(null);
  const [assistantSummary, setAssistantSummary] = React.useState<AssistantSummaryResponse | null>(null);
  const [assistantAgent,   setAssistantAgent]   = React.useState<AssistantAgentResponse | null>(null);
  const [overlayUrl, setOverlayUrl] = React.useState<string | null>(null);
  const [loading,  setLoading]  = React.useState(false);
  const [error,    setError]    = React.useState<string | null>(null);
  const [dragOver, setDragOver] = React.useState(false);

  React.useEffect(() => { return () => { if (overlayUrl) URL.revokeObjectURL(overlayUrl); }; }, [overlayUrl]);

  async function upload() {
    if (!file) return;
    setLoading(true); setError(null); setResult(null); setUploadId(null);
    if (overlayUrl) { URL.revokeObjectURL(overlayUrl); setOverlayUrl(null); }
    try {
      const up = await apiUploadMRI(token, { patientId, patientAge, patientSex, sourceLab, clinicalNotes, file });
      setUploadId(up.upload_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally { setLoading(false); }
  }

  async function detect() {
    if (!uploadId) return;
    setLoading(true); setError(null);
    try {
      const res = await apiDetect(token, uploadId);
      setResult(res);
      const [summary, agent] = await Promise.all([
        apiAssistantSummary(token, patientId),
        apiAssistantAgent(token, patientId),
      ]);
      setAssistantSummary(summary);
      setAssistantAgent(agent);
      if (res.overlay_image_url) {
        const blob = await fetchAuthedBlob(res.overlay_image_url, token);
        setOverlayUrl(URL.createObjectURL(blob));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally { setLoading(false); }
  }

  async function uploadLab() {
    if (!labFile) return;
    setLoading(true); setError(null);
    try {
      await apiUploadLabReport(token, patientId, labFile);
      const [dash, summary, agent] = await Promise.all([
        apiPatientDashboard(token, patientId),
        apiAssistantSummary(token, patientId),
        apiAssistantAgent(token, patientId),
      ]);
      setDashboard(dash); setAssistantSummary(summary); setAssistantAgent(agent);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally { setLoading(false); }
  }

  async function loadDashboard() {
    setLoading(true); setError(null);
    try {
      const [dash, summary, agent] = await Promise.all([
        apiPatientDashboard(token, patientId),
        apiAssistantSummary(token, patientId),
        apiAssistantAgent(token, patientId),
      ]);
      setDashboard(dash); setAssistantSummary(summary); setAssistantAgent(agent);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally { setLoading(false); }
  }

  async function downloadAuthed(url: string, filename: string) {
    try {
      const blob = await fetchAuthedBlob(url, token);
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = filename;
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    } catch (err) { setError(err instanceof Error ? err.message : String(err)); }
  }

  function handleFileDrop(e: React.DragEvent) {
    e.preventDefault(); setDragOver(false);
    const f = e.dataTransfer.files?.[0];
    if (f && f.type.startsWith("image/")) setFile(f);
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

      {/* ── Patient Information ── */}
      <div className="card animate-in">
        <div className="card-header">
          <div className="card-title">
            <div className="card-title-icon">🧾</div>
            Patient Information
          </div>
          {uploadId && <span className="badge badge-green">Upload #{uploadId} Ready</span>}
        </div>
        <div className="card-body">
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Patient ID</label>
              <input id="patient-id" className="form-input" type="text" value={patientId}
                onChange={e => setPatientId(e.target.value)} placeholder="e.g. P001" />
            </div>
            <div className="form-group">
              <label className="form-label">Age</label>
              <input id="patient-age" className="form-input" type="number" value={patientAge ?? ""}
                onChange={e => setPatientAge(e.target.value ? Number(e.target.value) : null)} placeholder="Years" />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Sex</label>
              <select id="patient-sex" className="form-input form-select" value={patientSex}
                onChange={e => setPatientSex(e.target.value)}>
                <option>Male</option>
                <option>Female</option>
                <option>Other</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Source Lab / Facility</label>
              <input id="source-lab" className="form-input" type="text" value={sourceLab}
                onChange={e => setSourceLab(e.target.value)} placeholder="Hospital / Lab name" />
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Clinical Notes</label>
            <textarea id="clinical-notes" className="form-input" value={clinicalNotes}
              onChange={e => setClinicalNotes(e.target.value)}
              placeholder="Relevant history, symptoms, clinical observations…" />
          </div>
        </div>
      </div>

      {/* ── MRI Upload ── */}
      <div className="card animate-in">
        <div className="card-header">
          <div className="card-title">
            <div className="card-title-icon">📡</div>
            MRI Scan Upload
          </div>
        </div>
        <div className="card-body">
          <div
            id="mri-drop-zone"
            className={`upload-zone ${dragOver ? "drag-over" : ""}`}
            onClick={() => document.getElementById("mri-file-input")?.click()}
            onDragOver={e => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleFileDrop}
          >
            <input id="mri-file-input" type="file" accept="image/*" style={{ display: "none" }}
              onChange={e => setFile(e.target.files?.[0] ?? null)} />
            <div className="upload-zone-icon">🧲</div>
            <div className="upload-zone-title">Drop MRI scan here or click to browse</div>
            <div className="upload-zone-sub">PNG, JPG, DICOM-exported images • Max 20 MB</div>
            {file && (
              <div className="upload-zone-file">
                <span>✓</span> {file.name}
              </div>
            )}
          </div>

          <div className="divider"></div>

          <div className="form-group">
            <label className="form-label">Lab Report (optional)</label>
            <input id="lab-file-input" className="form-input" type="file" accept=".pdf,.txt"
              onChange={e => setLabFile(e.target.files?.[0] ?? null)} />
            {labFile && <div className="text-muted mt-2">Selected: {labFile.name}</div>}
          </div>

          {error && (
            <div className="alert alert-red mt-3">
              <span>⚠</span><span>{error}</span>
            </div>
          )}

          <div className="btn-group mt-4">
            <button id="btn-upload" className="btn btn-primary" disabled={loading || !file} onClick={upload}>
              {loading && !uploadId ? <><span className="spinner spinner-sm"></span> Uploading…</> : <><span>⬆</span> Upload MRI</>}
            </button>
            <button id="btn-detect" className="btn btn-primary" disabled={loading || !uploadId} onClick={detect}>
              {loading && !!uploadId ? <><span className="spinner spinner-sm"></span> Analysing…</> : <><span>🔬</span> Run AI Detection</>}
            </button>
            <button id="btn-upload-lab" className="btn btn-secondary" disabled={loading || !labFile} onClick={uploadLab}>
              <span>📄</span> Upload Lab Report
            </button>
            <button id="btn-load-dashboard" className="btn btn-secondary" disabled={loading} onClick={loadDashboard}>
              <span>◫</span> Load Dashboard
            </button>
          </div>
        </div>
      </div>

      {/* ── AI Detection Results ── */}
      {result && (() => {
        const m = extractMetrics(result);
        const ismalignant = result.classification_label === "malignant";
        const riskCls = riskClass(m.riskBand);
        return (
          <div className="card animate-in">
            {/* Result header */}
            <div className="result-header">
              <div>
                <div className="text-xs text-muted" style={{ marginBottom: 4 }}>AI CLASSIFICATION RESULT</div>
                <div className={`result-classification ${ismalignant ? "red" : "green"}`}
                  style={{ color: ismalignant ? "var(--red)" : "var(--green)" }}>
                  {result.classification_label.toUpperCase()}
                  {result.is_uncertain && <span className="badge badge-yellow" style={{ marginLeft: 12, fontSize: 11 }}>Uncertain</span>}
                </div>
              </div>
              <div className="result-meta">
                <div className="btn-group">
                  <button className="btn btn-secondary btn-sm"
                    onClick={() => downloadAuthed(reportPdfUrl(result.result_id), `report_${result.result_id}.pdf`)}>
                    <span>⬇</span> PDF Report
                  </button>
                  <button className="btn btn-secondary btn-sm"
                    onClick={() => downloadAuthed(reportCsvUrl(result.result_id), `report_${result.result_id}.csv`)}>
                    <span>⬇</span> CSV Export
                  </button>
                </div>
              </div>
            </div>

            {/* Key metrics grid */}
            <div className="metric-grid">
              <div className="metric-cell">
                <div className="metric-cell-label">Confidence</div>
                <div className={`metric-cell-value ${ismalignant ? "red" : "green"}`}>
                  {toPercent(result.confidence)}
                </div>
                <div className="metric-cell-sub">Model certainty</div>
              </div>
              <div className="metric-cell">
                <div className="metric-cell-label">Severity Score</div>
                <div className={`metric-cell-value ${result.severity_score >= 0.55 ? "red" : result.severity_score >= 0.3 ? "yellow" : "green"}`}>
                  {(result.severity_score * 100).toFixed(0)}
                </div>
                <div className="metric-cell-sub">/ 100 composite</div>
              </div>
              <div className="metric-cell">
                <div className="metric-cell-label">Tumour Diameter</div>
                <div className={`metric-cell-value ${m.diamMm > 30 ? "red" : m.diamMm > 15 ? "yellow" : "blue"}`}>
                  {m.diamMm > 0 ? `${m.diamMm} mm` : "—"}
                </div>
                <div className="metric-cell-sub">Proxy estimate</div>
              </div>
              <div className="metric-cell">
                <div className="metric-cell-label">Anomaly Area</div>
                <div className="metric-cell-value yellow">{m.areaMm2 > 0 ? `${m.areaMm2} mm²` : "—"}</div>
                <div className="metric-cell-sub">{m.areaPx > 0 ? `${m.areaPx} px` : "—"}</div>
              </div>
              <div className="metric-cell">
                <div className="metric-cell-label">Brain Region</div>
                <div className="metric-cell-value blue" style={{ fontSize: 14, letterSpacing: 0 }}>
                  {m.region.replace("_", " ")}
                </div>
                <div className="metric-cell-sub">
                  {m.centroid ? `Centroid (${m.centroid.x.toFixed(0)}, ${m.centroid.y.toFixed(0)})` : "—"}
                </div>
              </div>
              <div className="metric-cell">
                <div className="metric-cell-label">Model Version</div>
                <div className="metric-cell-value blue" style={{ fontSize: 14, letterSpacing: 0, fontFamily: "JetBrains Mono, monospace" }}>
                  {String((result.output_json as Record<string, unknown>).model_version ?? "v0")}
                </div>
                <div className="metric-cell-sub">Inference engine</div>
              </div>
            </div>

            <div className="card-body">
              {/* Risk Band */}
              <div className="section-title">
                <span>⚕</span> Clinical Risk Assessment
              </div>
              <div className={`risk-band ${riskCls}`}>
                <div className="risk-band-icon">{riskIcon(m.riskBand)}</div>
                <div>
                  <div className="risk-band-title">{m.riskBand} Risk</div>
                  <div className="risk-band-desc">{m.anomalySummary}</div>
                </div>
              </div>

              {/* Classification probabilities */}
              <div className="section-title mt-4"><span>📊</span> Classification Probabilities</div>
              <div className="progress-row">
                <div className="progress-header">
                  <span className="progress-label">Malignant</span>
                  <span className="progress-value" style={{ color: "var(--red)" }}>{toPercent(m.probs.malignant)}</span>
                </div>
                <div className="progress-track">
                  <div className="progress-fill red" style={{ width: `${m.probs.malignant * 100}%` }}></div>
                </div>
              </div>
              <div className="progress-row">
                <div className="progress-header">
                  <span className="progress-label">Benign</span>
                  <span className="progress-value" style={{ color: "var(--green)" }}>{toPercent(m.probs.benign)}</span>
                </div>
                <div className="progress-track">
                  <div className="progress-fill green" style={{ width: `${m.probs.benign * 100}%` }}></div>
                </div>
              </div>

              {/* Anomaly burden */}
              <div className="section-title mt-4"><span>📐</span> Anomaly Burden & Morphology</div>
              <div className="progress-row">
                <div className="progress-header">
                  <span className="progress-label">Anomaly Area Ratio</span>
                  <span className="progress-value" style={{ color: "var(--yellow)" }}>{toPercent(m.areaRatio)}</span>
                </div>
                <div className="progress-track">
                  <div className="progress-fill yellow" style={{ width: `${m.areaRatio * 100}%` }}></div>
                </div>
              </div>
              <div className="progress-row">
                <div className="progress-header">
                  <span className="progress-label">Boundary Complexity</span>
                  <span className="progress-value" style={{ color: "var(--yellow)" }}>{toPercent(m.edgeDensity)}</span>
                </div>
                <div className="progress-track">
                  <div className="progress-fill yellow" style={{ width: `${m.edgeDensity * 100}%` }}></div>
                </div>
              </div>
              <div className="progress-row">
                <div className="progress-header">
                  <span className="progress-label">Potential Spread Risk</span>
                  <span className="progress-value" style={{ color: "var(--red)" }}>{toPercent(m.spreadRisk)}</span>
                </div>
                <div className="progress-track">
                  <div className="progress-fill red" style={{ width: `${m.spreadRisk * 100}%` }}></div>
                </div>
              </div>

              {/* Anomaly flags */}
              {result.anomaly_flags && Object.keys(result.anomaly_flags).length > 0 && (
                <>
                  <div className="section-title mt-4"><span>🚩</span> Anomaly Flags</div>
                  <div className="flag-list">
                    {Object.entries(result.anomaly_flags).map(([key, val]) => (
                      <div key={key} className={`flag-item ${val ? "active" : "inactive"}`}>
                        <span className="flag-item-icon">{val ? "⚠" : "✓"}</span>
                        <span className="flag-item-text">
                          {key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}
                        </span>
                        <span style={{ marginLeft: "auto", fontFamily: "JetBrains Mono, monospace", fontSize: 12 }}>
                          {String(val)}
                        </span>
                      </div>
                    ))}
                  </div>
                </>
              )}

              {/* Clinical impression */}
              <div className="section-title mt-4"><span>📋</span> Clinical Impression & Guidance</div>
              <div className="impression-box">
                <ul>
                  <li>Cross-reference AI overlay with full radiology sequence before sign-off.</li>
                  <li>If Risk Band is High or Critical — escalate to specialist for same-day review.</li>
                  <li>Correlate with patient history, lab values, and clinical presentation.</li>
                  <li>Use PDF/CSV export for PACS integration and patient record documentation.</li>
                  <li>This report is AI-assisted. Not a substitute for qualified radiologist diagnosis.</li>
                </ul>
              </div>

              {/* MRI Image Comparison */}
              {(file || overlayUrl) && (
                <>
                  <div className="section-title mt-4"><span>🖼</span> Image Comparison</div>
                  <div className="image-compare">
                    {file && (
                      <div className="image-panel">
                        <div className="image-panel-label">Original MRI</div>
                        <img src={URL.createObjectURL(file)} alt="Original MRI scan" />
                      </div>
                    )}
                    {overlayUrl && (
                      <div className="image-panel">
                        <div className="image-panel-label">AI Segmentation Overlay</div>
                        <img src={overlayUrl} alt="AI tumour segmentation overlay" />
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
        );
      })()}

      {/* ── Patient Dashboard ── */}
      {dashboard && (
        <div className="card animate-in">
          <div className="card-header">
            <div className="card-title">
              <div className="card-title-icon">◫</div>
              Patient Overview — {String(dashboard.patient_id)}
            </div>
            <span className="badge badge-blue">{dashboard.upload_count} Scans</span>
          </div>
          <div className="card-body">
            <div className="form-row">
              {/* Profile */}
              <div>
                <div className="section-title"><span>👤</span> Patient Profile</div>
                {[
                  ["Age",        (dashboard.patient_profile as Record<string, unknown>).age],
                  ["Sex",        (dashboard.patient_profile as Record<string, unknown>).sex],
                  ["Source Lab", (dashboard.patient_profile as Record<string, unknown>).source_lab],
                ].map(([label, val]) => (
                  <div key={String(label)} className="flex-between" style={{ padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
                    <span className="text-muted text-sm">{String(label)}</span>
                    <span style={{ fontSize: 13, fontWeight: 500 }}>{String(val ?? "—")}</span>
                  </div>
                ))}
              </div>
              {/* Latest findings */}
              <div>
                <div className="section-title"><span>🔬</span> Latest AI Findings</div>
                {(() => {
                  const lr = dashboard.latest_result as Record<string, unknown>;
                  const ms = (lr.output_json as Record<string, unknown>)?.mask_stats as Record<string, unknown> ?? {};
                  return [
                    ["Classification", lr.classification_label],
                    ["Confidence",     typeof lr.confidence === "number" ? `${(lr.confidence * 100).toFixed(1)}%` : "—"],
                    ["Severity",       typeof lr.severity_score === "number" ? `${(lr.severity_score * 100).toFixed(0)}/100` : "—"],
                    ["Region",         ms.region],
                    ["Diameter (mm)",  ms.estimated_tumor_diameter_mm],
                    ["Area (mm²)",     ms.area_mm2_proxy],
                  ].map(([label, val]) => (
                    <div key={String(label)} className="flex-between" style={{ padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
                      <span className="text-muted text-sm">{String(label)}</span>
                      <span style={{ fontSize: 13, fontWeight: 500 }}>{String(val ?? "—")}</span>
                    </div>
                  ));
                })()}
              </div>
            </div>

            {/* Lab reports */}
            {dashboard.lab_reports.length > 0 && (
              <>
                <div className="divider"></div>
                <div className="section-title"><span>📄</span> Lab Reports</div>
                {dashboard.lab_reports.slice(0, 4).map((r, i) => (
                  <div key={i} className="flag-item inactive mt-2">
                    <span className="flag-item-icon">📄</span>
                    <span className="flag-item-text">{String((r.source_filename as string) ?? "report")}</span>
                    <span style={{ marginLeft: "auto", fontSize: 12, color: "var(--text-muted)" }}>
                      confidence: {String(r.extraction_confidence ?? "—")}
                    </span>
                  </div>
                ))}
              </>
            )}
          </div>
        </div>
      )}

      {/* ── AI Clinical Assistant ── */}
      {assistantSummary && (
        <div className="assistant-panel animate-in">
          <div className="assistant-header">
            <span style={{ fontSize: 18 }}>🤖</span>
            <div className="assistant-title">AI Clinical Assistant — Heuristic Summary</div>
            <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
              <span className={`badge ${assistantSummary.tumor_present ? "badge-red" : "badge-green"}`}>
                Tumour Signal: {assistantSummary.tumor_present ? "Suspicious" : "Low"}
              </span>
              <span className={`badge ${assistantSummary.risk_level === "critical" || assistantSummary.risk_level === "high" ? "badge-red" : "badge-yellow"}`}>
                Risk: {assistantSummary.risk_level}
              </span>
            </div>
          </div>
          <div className="assistant-body">
            <div className="assistant-text">{assistantSummary.summary_text}</div>
          </div>
        </div>
      )}

      {/* ── LLM Agent Summary ── */}
      {assistantAgent?.llm?.enabled && assistantAgent.llm.summary_text && (
        <div className="assistant-panel animate-in">
          <div className="assistant-header">
            <span style={{ fontSize: 18 }}>✨</span>
            <div className="assistant-title">AI Agent — LLM Summary</div>
            <span className="badge badge-blue" style={{ marginLeft: "auto" }}>
              {String(assistantAgent.llm.model ?? "LLM")}
            </span>
          </div>
          <div className="assistant-body">
            <div className="assistant-text">{assistantAgent.llm.summary_text}</div>
          </div>
        </div>
      )}

    </div>
  );
}

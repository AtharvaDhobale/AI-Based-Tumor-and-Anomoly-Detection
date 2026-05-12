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

type ProbabilityMap = {
  benign: number;
  malignant: number;
};

function toPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function clamp01(value: number): number {
  return Math.max(0, Math.min(1, value));
}

function extractClinicalMetrics(result: DetectionResponse) {
  const out = result.output_json as Record<string, unknown>;
  const probsRaw = (out.classification_probs ?? {}) as Record<string, unknown>;
  const maskStatsRaw = (out.mask_stats ?? {}) as Record<string, unknown>;

  const probs: ProbabilityMap = {
    benign: clamp01(Number(probsRaw.benign ?? (result.classification_label === "benign" ? result.confidence : 1 - result.confidence))),
    malignant: clamp01(Number(probsRaw.malignant ?? (result.classification_label === "malignant" ? result.confidence : 1 - result.confidence)))
  };

  const areaRatio = clamp01(Number(maskStatsRaw.area_ratio ?? 0));
  const edgeDensity = clamp01(0.55 * areaRatio + 0.45 * result.severity_score);
  const spreadRisk = clamp01(0.5 * areaRatio + 0.5 * probs.malignant);

  const riskBand =
    result.severity_score >= 0.8 ? "Critical" :
      result.severity_score >= 0.55 ? "High" :
        result.severity_score >= 0.3 ? "Moderate" : "Low";

  const anomalySummary =
    areaRatio >= 0.3 ? "Large anomaly footprint detected in the segmented region." :
      areaRatio >= 0.12 ? "Moderate anomaly footprint with clinically notable burden." :
        areaRatio > 0.02 ? "Small focal anomaly region detected." :
          "No dominant anomaly burden detected in current segmentation.";

  return { probs, areaRatio, edgeDensity, spreadRisk, riskBand, anomalySummary };
}

export default function UploadDetectCard({ token }: Props) {
  const [patientId, setPatientId] = React.useState("P001");
  const [patientAge, setPatientAge] = React.useState<number | null>(45);
  const [patientSex, setPatientSex] = React.useState("male");
  const [sourceLab, setSourceLab] = React.useState("Central Lab");
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
    if (overlayUrl) URL.revokeObjectURL(overlayUrl);
    setOverlayUrl(null);

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

  async function uploadLab() {
    if (!labFile) return;
    setLoading(true);
    setError(null);
    try {
      await apiUploadLabReport(token, patientId, labFile);
      const dash = await apiPatientDashboard(token, patientId);
      setDashboard(dash);
      const summary = await apiAssistantSummary(token, patientId);
      setAssistantSummary(summary);
      const agent = await apiAssistantAgent(token, patientId);
      setAssistantAgent(agent);
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
      const summary = await apiAssistantSummary(token, patientId);
      setAssistantSummary(summary);
      const agent = await apiAssistantAgent(token, patientId);
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

  async function downloadAuthed(url: string, filename: string) {
    const blob = await fetchAuthedBlob(url, token);
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }

  async function loadDashboard() {
    setLoading(true);
    setError(null);
    try {
      const dash = await apiPatientDashboard(token, patientId);
      setDashboard(dash);
      const summary = await apiAssistantSummary(token, patientId);
      setAssistantSummary(summary);
      const agent = await apiAssistantAgent(token, patientId);
      setAssistantAgent(agent);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card mainCard">
      <h2>MRI Upload, Detection & Clinical Report</h2>

      <div className="field">
        <label>Patient ID</label>
        <input type="text" value={patientId} onChange={(e) => setPatientId(e.target.value)} />
      </div>
      <div className="field">
        <label>Patient Age</label>
        <input type="text" value={patientAge ?? ""} onChange={(e) => setPatientAge(e.target.value ? Number(e.target.value) : null)} />
      </div>
      <div className="field">
        <label>Patient Sex</label>
        <input type="text" value={patientSex} onChange={(e) => setPatientSex(e.target.value)} />
      </div>
      <div className="field">
        <label>Source Lab</label>
        <input type="text" value={sourceLab} onChange={(e) => setSourceLab(e.target.value)} />
      </div>
      <div className="field">
        <label>Clinical Notes</label>
        <input type="text" value={clinicalNotes} onChange={(e) => setClinicalNotes(e.target.value)} />
      </div>

      <div className="field">
        <label>MRI image (PNG/JPG)</label>
        <input type="file" accept="image/*" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
      </div>
      <div className="field">
        <label>Lab report (PDF/TXT)</label>
        <input type="file" accept=".pdf,.txt" onChange={(e) => setLabFile(e.target.files?.[0] ?? null)} />
      </div>

      {error && <div className="muted" style={{ color: "var(--danger)" }}>{error}</div>}

      <div className="row actionRow" style={{ marginTop: 10 }}>
        <button disabled={loading || !file} onClick={upload}>
          {loading ? "Working..." : "Upload"}
        </button>
        <button disabled={loading || !uploadId} onClick={detect}>
          Run AI Detection
        </button>
        <button disabled={loading || !labFile} onClick={uploadLab}>
          Upload Lab Report
        </button>
        <button disabled={loading} onClick={loadDashboard}>
          Load Dashboard
        </button>
      </div>

      <div style={{ height: 12 }} />
      {uploadId && <div className="pill ok">Upload ID: {uploadId}</div>}

      {result && (
        <>
          <div style={{ height: 14 }} />
          <div className="row">
            <div className={`pill ${result.classification_label === "malignant" ? "bad" : "ok"}`}>
              Label: {result.classification_label}
            </div>
            <div className="pill">Confidence: {(result.confidence * 100).toFixed(1)}%</div>
            <div className="pill">Severity: {(result.severity_score * 100).toFixed(1)}%</div>
            {result.is_uncertain && <div className="pill bad">Uncertain - Expert review needed</div>}
          </div>

          {(() => {
            const metrics = extractClinicalMetrics(result);
            return (
              <div className="clinicalReport">
                <h3>Clinical AI Report</h3>
                <div className="reportGrid">
                  <div className="reportSection">
                    <h4>Risk Stratification</h4>
                    <div className="row">
                      <span className={`pill ${result.classification_label === "malignant" ? "bad" : "ok"}`}>
                        Primary Suggestion: {result.classification_label}
                      </span>
                      <span className={`pill ${metrics.riskBand === "Critical" || metrics.riskBand === "High" ? "bad" : "ok"}`}>
                        Risk Band: {metrics.riskBand}
                      </span>
                    </div>
                    <div className="muted" style={{ marginTop: 8 }}>
                      {metrics.anomalySummary}
                    </div>
                  </div>

                  <div className="reportSection">
                    <h4>Classification Probabilities</h4>
                    <div className="metricBar">
                      <div className="metricLabel"><span>Malignant</span><span>{toPercent(metrics.probs.malignant)}</span></div>
                      <div className="meter"><div className="fill bad" style={{ width: `${metrics.probs.malignant * 100}%` }} /></div>
                    </div>
                    <div className="metricBar">
                      <div className="metricLabel"><span>Benign</span><span>{toPercent(metrics.probs.benign)}</span></div>
                      <div className="meter"><div className="fill ok" style={{ width: `${metrics.probs.benign * 100}%` }} /></div>
                    </div>
                  </div>

                  <div className="reportSection">
                    <h4>Anomaly Burden & Edges</h4>
                    <div className="metricBar">
                      <div className="metricLabel"><span>Anomaly Area Ratio</span><span>{toPercent(metrics.areaRatio)}</span></div>
                      <div className="meter"><div className="fill warn" style={{ width: `${metrics.areaRatio * 100}%` }} /></div>
                    </div>
                    <div className="metricBar">
                      <div className="metricLabel"><span>Boundary Complexity</span><span>{toPercent(metrics.edgeDensity)}</span></div>
                      <div className="meter"><div className="fill warn" style={{ width: `${metrics.edgeDensity * 100}%` }} /></div>
                    </div>
                    <div className="metricBar">
                      <div className="metricLabel"><span>Potential Spread Risk</span><span>{toPercent(metrics.spreadRisk)}</span></div>
                      <div className="meter"><div className="fill bad" style={{ width: `${metrics.spreadRisk * 100}%` }} /></div>
                    </div>
                  </div>

                  <div className="reportSection">
                    <h4>Impression & Recommendations</h4>
                    <ul className="reportList">
                      <li>Cross-check AI overlay with radiology sequence context before final sign-off.</li>
                      <li>If risk band is High/Critical, prioritize specialist review and follow-up imaging.</li>
                      <li>Use downloadable PDF/CSV as part of patient record documentation.</li>
                    </ul>
                    <div className="muted">
                      Model Version: {String((result.output_json as Record<string, unknown>).model_version ?? "n/a")}
                    </div>
                  </div>
                </div>
              </div>
            );
          })()}

          <div style={{ height: 14 }} />
          <div className="row">
            <button onClick={() => downloadAuthed(reportPdfUrl(result.result_id), `report_${result.result_id}.pdf`)}>
              Download PDF
            </button>
            <button onClick={() => downloadAuthed(reportCsvUrl(result.result_id), `report_${result.result_id}.csv`)}>
              Download CSV
            </button>
          </div>
        </>
      )}

      {dashboard && (
        <div className="clinicalReport">
          <h3>Doctor Overview Dashboard</h3>
          <div className="reportGrid">
            <div className="reportSection">
              <h4>Patient Profile</h4>
              <div className="muted">ID: {String(dashboard.patient_id)}</div>
              <div className="muted">Age: {String((dashboard.patient_profile as Record<string, unknown>).age ?? "n/a")}</div>
              <div className="muted">Sex: {String((dashboard.patient_profile as Record<string, unknown>).sex ?? "n/a")}</div>
              <div className="muted">Source Lab: {String((dashboard.patient_profile as Record<string, unknown>).source_lab ?? "n/a")}</div>
            </div>
            <div className="reportSection">
              <h4>Latest AI Findings</h4>
              <div className="muted">Classification: {String((dashboard.latest_result as Record<string, unknown>).classification_label ?? "n/a")}</div>
              <div className="muted">Confidence: {String((dashboard.latest_result as Record<string, unknown>).confidence ?? "n/a")}</div>
              <div className="muted">Severity: {String((dashboard.latest_result as Record<string, unknown>).severity_score ?? "n/a")}</div>
              {(() => {
                const ms = (((dashboard.latest_result as Record<string, unknown>).output_json as Record<string, unknown>)?.mask_stats as Record<string, unknown>) ?? {};
                const region = String((ms as Record<string, unknown>)?.region ?? "n/a");
                const diam = String((ms as Record<string, unknown>)?.estimated_tumor_diameter_mm ?? "n/a");
                const areaPx = String((ms as Record<string, unknown>)?.area_px ?? "n/a");
                const areaMm2 = String((ms as Record<string, unknown>)?.area_mm2_proxy ?? "n/a");
                return (
                  <>
                    <div className="muted">Region: {region}</div>
                    <div className="muted">Diameter (mm proxy): {diam}</div>
                    <div className="muted">Area: {areaPx} px | {areaMm2} mm² (proxy)</div>
                  </>
                );
              })()}
              <div className="muted">Uploads: {dashboard.upload_count}</div>
            </div>
            <div className="reportSection">
              <h4>Lab Report Extraction</h4>
              {dashboard.lab_reports.length === 0 ? (
                <div className="muted">No parsed lab reports yet.</div>
              ) : (
                dashboard.lab_reports.slice(0, 3).map((r, idx) => (
                  <div key={idx} className="muted">
                    {String((r.source_filename as string) ?? "report")} | confidence {String(r.extraction_confidence ?? "n/a")}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {assistantSummary && (
        <div className="clinicalReport assistantPanel">
          <h3>AI Clinical Assistant</h3>
          <div className="row">
            <span className={`pill ${assistantSummary.tumor_present ? "bad" : "ok"}`}>
              Tumor Signal: {assistantSummary.tumor_present ? "Suspicious/Present" : "Low"}
            </span>
            <span className={`pill ${assistantSummary.risk_level === "critical" || assistantSummary.risk_level === "high" ? "bad" : "ok"}`}>
              Risk: {assistantSummary.risk_level}
            </span>
          </div>
          <pre className="assistantText">{assistantSummary.summary_text}</pre>
        </div>
      )}

      {assistantAgent?.llm?.enabled && assistantAgent.llm.summary_text && (
        <div className="clinicalReport assistantPanel">
          <h3>AI Agent (LLM Summary)</h3>
          <div className="muted">Model: {String(assistantAgent.llm.model ?? "n/a")}</div>
          <pre className="assistantText">{assistantAgent.llm.summary_text}</pre>
        </div>
      )}

      <div style={{ height: 16 }} />
      <div className="muted">
        Overlay image requires auth; the app fetches it as a blob and renders it locally.
      </div>

      <div style={{ height: 10 }} />
      <div className="imgWrap">
        {file && (
          <img
            src={URL.createObjectURL(file)}
            alt="Original MRI"
            onLoad={(e) => URL.revokeObjectURL((e.target as HTMLImageElement).src)}
          />
        )}
        {overlayUrl && <img src={overlayUrl} alt="AI overlay" />}
      </div>
    </div>
  );
}


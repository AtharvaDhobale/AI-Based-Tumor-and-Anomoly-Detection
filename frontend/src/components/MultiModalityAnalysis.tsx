import React from "react";
import { apiAnalyzeImage, type Modality, type AnalysisResult, MODALITY_INFO } from "../lib/api";

interface Props {
  modality: Modality;
  token: string;
}

function getSeverityColor(severity: string): string {
  switch (severity) {
    case "critical": return "#ef4444";
    case "high": return "#f97316";
    case "moderate": return "#eab308";
    case "none": return "#22c55e";
    default: return "#6b7280";
  }
}

function getSeverityLabel(severity: string): string {
  switch (severity) {
    case "critical": return "🔴 Critical";
    case "high": return "🟠 High";
    case "moderate": return "🟡 Moderate";
    case "none": return "🟢 Normal";
    default: return "⚪ Unknown";
  }
}

export default function MultiModalityAnalysis({ modality, token }: Props) {
  const [file, setFile] = React.useState<File | null>(null);
  const [preview, setPreview] = React.useState<string | null>(null);
  const [result, setResult] = React.useState<AnalysisResult | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) {
      setFile(f);
      const reader = new FileReader();
      reader.onload = () => setPreview(reader.result as string);
      reader.readAsDataURL(f);
      setResult(null);
      setError(null);
    }
  };

  async function analyze() {
    if (!file) return;
    setLoading(true);
    setError(null);

    try {
      const res = await apiAnalyzeImage(file, modality);
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }

  const modalityInfo = MODALITY_INFO[modality];

  return (
    <div className="card mainCard">
      <h2>{modalityInfo.label} Analysis</h2>
      <p className="muted" style={{ marginBottom: "1rem" }}>{modalityInfo.description}</p>

      {/* File Upload */}
      <div className="field">
        <label>Upload {modalityInfo.label} Image</label>
        <input 
          type="file" 
          accept="image/*,.dcm"
          onChange={handleFileChange}
          style={{ padding: "0.5rem" }}
        />
      </div>

      {/* Preview */}
      {preview && (
        <div style={{ marginBottom: "1rem" }}>
          <img 
            src={preview} 
            alt="Preview" 
            style={{ 
              maxWidth: "100%", 
              maxHeight: "200px", 
              borderRadius: "8px",
              border: "1px solid #374151"
            }} 
          />
        </div>
      )}

      {/* Analyze Button */}
      <button 
        onClick={analyze}
        disabled={!file || loading}
        style={{
          width: "100%",
          padding: "0.75rem",
          backgroundColor: loading ? "#4b5563" : "#3b82f6",
          color: "white",
          border: "none",
          borderRadius: "6px",
          cursor: loading ? "not-allowed" : "pointer",
          fontWeight: "600",
          marginBottom: "1rem"
        }}
      >
        {loading ? "Analyzing..." : "Run AI Analysis"}
      </button>

      {/* Error */}
      {error && (
        <div style={{ 
          padding: "0.75rem", 
          backgroundColor: "#fee2e2", 
          color: "#dc2626",
          borderRadius: "6px",
          marginBottom: "1rem"
        }}>
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div style={{ 
          padding: "1rem", 
          backgroundColor: "#1f2937", 
          borderRadius: "8px",
          border: "1px solid #374151"
        }}>
          <h3 style={{ marginBottom: "0.75rem", color: "#e2e8f0" }}>Analysis Results</h3>
          
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", marginBottom: "1rem" }}>
            <div>
              <div className="muted" style={{ fontSize: "0.75rem" }}>Prediction</div>
              <div style={{ fontSize: "1.125rem", fontWeight: "600", color: "#fff" }}>
                {result.prediction || result.classification_label}
              </div>
            </div>
            <div>
              <div className="muted" style={{ fontSize: "0.75rem" }}>Confidence</div>
              <div style={{ fontSize: "1.125rem", fontWeight: "600", color: "#fff" }}>
                {Math.round((result.confidence || result.classification_probs?.malignant || result.classification_probs?.benign || 0) * 100)}%
              </div>
            </div>
            <div>
              <div className="muted" style={{ fontSize: "0.75rem" }}>Severity</div>
              <div style={{ fontSize: "0.875rem", fontWeight: "600", color: getSeverityColor(result.severity || "none") }}>
                {getSeverityLabel(result.severity || "none")}
              </div>
            </div>
            <div>
              <div className="muted" style={{ fontSize: "0.75rem" }}>Model Status</div>
              <div style={{ fontSize: "0.875rem", color: result.model_trained ? "#22c55e" : "#eab308" }}>
                {result.model_trained ? "✅ Trained" : "⚠️ Calibration"}
              </div>
            </div>
          </div>

          {/* Probability Distribution */}
          {result.all_probabilities && (
            <div style={{ marginBottom: "1rem" }}>
              <div className="muted" style={{ fontSize: "0.75rem", marginBottom: "0.5rem" }}>Probability Distribution</div>
              {Object.entries(result.all_probabilities).map(([label, prob]) => (
                <div key={label} style={{ marginBottom: "0.25rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem" }}>
                    <span style={{ color: "#9ca3af" }}>{label}</span>
                    <span style={{ color: "#fff" }}>{(prob * 100).toFixed(1)}%</span>
                  </div>
                  <div style={{ 
                    height: "4px", 
                    backgroundColor: "#374151", 
                    borderRadius: "2px",
                    overflow: "hidden" 
                  }}>
                    <div style={{ 
                      height: "100%", 
                      width: `${prob * 100}%`, 
                      backgroundColor: "#3b82f6",
                      borderRadius: "2px"
                    }} />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Disclaimer */}
          {result.disclaimer && (
            <div style={{ 
              padding: "0.5rem", 
              backgroundColor: "#fef3c7", 
              color: "#92400e",
              fontSize: "0.75rem",
              borderRadius: "4px"
            }}>
              {result.disclaimer}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
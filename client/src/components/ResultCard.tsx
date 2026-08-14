import type { ScoreResponse } from "../types";

function formatPrediction(value: number, mode: "percent" | "score"): string {
  if (mode === "percent") {
    return `${(value * 100).toFixed(2)}%`;
  }
  return value.toFixed(4);
}

interface ResultCardProps {
  title: string;
  result: ScoreResponse;
  format?: "percent" | "score";
}

export function ResultCard({ title, result, format = "percent" }: ResultCardProps) {
  return (
    <div className={`result ${result.risk_level}`}>
      <div className="muted-label">{title}</div>
      <div className="metric">{formatPrediction(result.prediction, format)}</div>
      <p className={`result-message ${result.risk_level}`}>{result.message}</p>
    </div>
  );
}

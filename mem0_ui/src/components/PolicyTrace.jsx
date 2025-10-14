import React from "react";
import { Paper, Stack, Typography, Alert } from "@mui/material";
import { TYPE_STYLE } from "./TypeStyle";

export default function PolicyTrace({ policy }) {
  if (!policy) return <Alert severity="info" variant="outlined">No policy data.</Alert>;
  const rows = [
    ["Classified type", policy.classified_type],
    ["Rationale", policy.rationale],
    ["Specificity", policy.specificity],
    ["Longevity", policy.longevity],
    ["Score", policy.score],
    ["Decision", policy.decision],
    ["Dedup top scores", (policy.dedup_top_scores || []).map(s => typeof s === "number" ? s.toFixed(3) : s).join(", ") || "—"]
  ];
  const style = TYPE_STYLE[(policy.classified_type || "default").toLowerCase()] || TYPE_STYLE.default;
  return (
    <Paper variant="outlined" sx={{ p: 1.5, borderRadius: 2, bgcolor: style.bg }}>
      <Stack spacing={0.75}>
        {rows.map(([k, v], idx) => (
          <div key={idx} style={{ display: "grid", gridTemplateColumns: "160px 1fr", gap: 8, alignItems: "start" }}>
            <Typography variant="caption" sx={{ color: "#666" }}>{k}</Typography>
            <Typography variant="body2" sx={{ color: style.fg, whiteSpace: "pre-wrap" }}>{String(v ?? "—")}</Typography>
          </div>
        ))}
      </Stack>
    </Paper>
  );
}
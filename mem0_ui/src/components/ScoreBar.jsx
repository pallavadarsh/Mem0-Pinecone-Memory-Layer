import React from "react";
import { Box, Typography, LinearProgress } from "@mui/material";

export default function ScoreBar({ score }) {
  if (typeof score !== "number") return <Typography variant="body2" color="text.secondary">—</Typography>;
  const pct = Math.max(0, Math.min(1, score)) * 100;
  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1, minWidth: 120 }}>
      <Box sx={{ flex: 1 }}>
        <LinearProgress variant="determinate" value={pct} sx={{ height: 8, borderRadius: 6 }} />
      </Box>
      <Typography variant="caption" sx={{ width: 38, textAlign: "right", fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Courier New', monospace" }}>
        {Number.isFinite(score) ? score.toFixed(3) : "—"}
      </Typography>
    </Box>
  );
}
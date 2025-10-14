import React from "react";
import { Alert, Divider, Paper, Stack, Typography } from "@mui/material";
import TypeChip from "./TypeChip";

export default function StoredCard({ stored, summary }) {
  if (!stored && !summary) return <Alert severity="info" variant="outlined">Skipped storing this turn.</Alert>;
  return (
    <Stack spacing={1.2}>
      <Paper variant="outlined" sx={{ p: 1.5, borderRadius: 2 }}>
        <Typography variant="caption" sx={{ color: "#666" }}>Stored ID</Typography>
        <Typography variant="body2" sx={{ fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Courier New', monospace" }}>{stored?.id || "—"}</Typography>
        <Divider sx={{ my: 1 }} />
        <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
          <Typography variant="caption" sx={{ color: "#666" }}>Type</Typography>
          <TypeChip type={stored?.metadata?.type} />
        </Stack>
        <Typography variant="caption" sx={{ color: "#666" }}>Text</Typography>
        <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>{stored?.metadata?.text || "—"}</Typography>
      </Paper>
      <Paper variant="outlined" sx={{ p: 1.5, borderRadius: 2 }}>
        <Typography variant="caption" sx={{ color: "#666" }}>Summary (Q/A)</Typography>
        <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>{summary || "—"}</Typography>
      </Paper>
    </Stack>
  );
}
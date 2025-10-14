import React from "react";
import { Alert, Paper, Stack, Typography } from "@mui/material";
import TypeChip from "./TypeChip";
import ScoreBar from "./ScoreBar";
import { TYPE_STYLE } from "./TypeStyle";

export default function RetrievedTable({ items }) {
  if (!items || items.length === 0) {
    return <Alert severity="info" variant="outlined">No retrieved memories for this turn.</Alert>;
  }
  return (
    <Stack spacing={1.2}>
      {items.map((r, i) => {
        const style = TYPE_STYLE[(r.type || "default").toLowerCase()] || TYPE_STYLE.default;
        return (
          <Paper key={i} variant="outlined" sx={{ p: 1.5, borderRadius: 2, bgcolor: style.bg, borderColor: "#eaeaea" }}>
            <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 0.5 }}>
              <TypeChip type={r.type} />
              <ScoreBar score={r.score} />
            </Stack>
            <Typography variant="body2" sx={{ color: style.fg, whiteSpace: "pre-wrap" }}>
              {r.text || "—"}
            </Typography>
          </Paper>
        );
      })}
    </Stack>
  );
}
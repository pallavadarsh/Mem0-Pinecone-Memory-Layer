import React from "react";
import { Avatar, Box, Paper, Typography } from "@mui/material";
import { blue } from "@mui/material/colors";

export default function Message({ role, content }) {
  const isUser = role === "user";
  return (
    <Box sx={{ display: "flex", gap: 1.5, alignItems: "flex-start" }}>
      <Avatar sx={{ bgcolor: isUser ? "#111" : blue[700] }}>{isUser ? "U" : "A"}</Avatar>
      <Paper elevation={0} sx={{ p: 1.5, bgcolor: isUser ? "#fff" : "#f7f9ff", border: "1px solid #eee", borderRadius: 2, maxWidth: "100%" }}>
        <Typography sx={{ whiteSpace: "pre-wrap" }}>{content}</Typography>
      </Paper>
    </Box>
  );
}
import React from "react";
import Chip from "@mui/material/Chip";
import { TYPE_STYLE } from "./TypeStyle";

export default function TypeChip({ type }) {
  const key = (type || "default").toLowerCase();
  const style = TYPE_STYLE[key] || TYPE_STYLE.default;
  return <Chip size="small" label={type || "—"} color={style.chip} variant="filled" />;
}
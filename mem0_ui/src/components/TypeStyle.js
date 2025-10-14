import { blue, deepPurple, orange, pink, teal, green, grey, indigo } from "@mui/material/colors";

export const TYPE_STYLE = {
  factual:   { bg: blue[50],       fg: blue[800],       chip: "primary" },
  semantic:  { bg: deepPurple[50], fg: deepPurple[800], chip: "secondary" },
  episodic:  { bg: orange[50],     fg: orange[900],     chip: "warning" },
  preference:{ bg: pink[50],       fg: pink[800],       chip: "secondary" },
  task_state:{ bg: teal[50],       fg: teal[900],       chip: "success" },
  procedure: { bg: indigo[50],     fg: indigo[800],     chip: "info" },
  ltm:       { bg: green[50],      fg: green[900],      chip: "success" },
  stm:       { bg: grey[100],      fg: grey[800],       chip: "default" },
  default:   { bg: grey[50],       fg: grey[800],       chip: "default" },
};
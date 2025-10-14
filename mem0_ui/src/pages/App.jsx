import React from "react";
import {
  Alert, Box, Button, Card, CardContent, CardHeader, Container, Divider, Grid,
  Stack, TextField, Typography
} from "@mui/material";
import { createTheme, ThemeProvider } from "@mui/material/styles";
import { Send, Search, Bolt } from "@mui/icons-material";

import Message from "../components/Message";
import RetrievedTable from "../components/RetrievedTable";
import StoredCard from "../components/StoredCard";
import PolicyTrace from "../components/PolicyTrace";

const API = process.env.REACT_APP_API || "http://localhost:8000";

function Header() {
  return (
    <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 2 }}>
      <Stack direction="row" spacing={1} alignItems="center">
        <Bolt fontSize="small" color="primary" />
        <Typography variant="h6" sx={{ fontWeight: 700 }}>
          Chat + Memory <Typography component="span" color="primary">Mem0</Typography> / Pinecone
        </Typography>
      </Stack>
      <Typography variant="body2" sx={{ color: "#666" }}>Demo UI • Material UI</Typography>
    </Box>
  );
}

export default function App() {
  const [userId, setUserId] = React.useState("adarsh");
  const [input, setInput] = React.useState("");
  const [chatLog, setChatLog] = React.useState([]);
  const [retrievalQuery, setRetrievalQuery] = React.useState("endpoint");
  const [retrievalResults, setRetrievalResults] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");

  const send = async () => {
    if (!input.trim()) return;
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, message: input, type: "auto" }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || "Request failed");
      setChatLog((prev) => [...prev, { role: "user", content: input }, { role: "assistant", content: data.reply, raw: data }]);
      setInput("");
    } catch (e) {
      console.error(e);
      setError(String(e.message || e));
    } finally {
      setLoading(false);
    }
  };

  const runRetrieve = async () => {
    setError("");
    try {
      const url = new URL(`${API}/memory/retrieve`);
      url.searchParams.set("user_id", userId);
      url.searchParams.set("q", retrievalQuery);
      url.searchParams.set("top_k", "8");
      const res = await fetch(url.toString());
      const data = await res.json();
      setRetrievalResults(data?.results || []);
    } catch (e) {
      console.error(e);
      setError(String(e.message || e));
    }
  };

  const lastTurn = [...chatLog].reverse().find(m => m.role === "assistant");

  const theme = createTheme({
    palette: { mode: "light" },
    shape: { borderRadius: 12 },
    typography: { fontFamily: "Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif" },
  });

  return (
    <ThemeProvider theme={theme}>
      <Container maxWidth="lg" sx={{ py: 2.5 }}>
        <Header />
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        <Grid container spacing={2.5}>
          {/* LEFT: Chat */}
          <Grid item xs={12} md={7}>
            <Box sx={{ p: 2, border: "1px solid #eee", borderRadius: 2, bgcolor: "#fff" }}>
              <Stack direction="row" spacing={1} sx={{ mb: 1.5 }}>
                <TextField
                  label="User ID"
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  size="small"
                  sx={{ width: 180 }}
                />
                <TextField
                  fullWidth
                  label="Type a message"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && send()}
                  size="small"
                />
                <Button variant="contained" onClick={send} disabled={loading} startIcon={<Send />}>
                  Send
                </Button>
              </Stack>
              <Divider sx={{ mb: 2 }} />
              <Stack spacing={1.5} sx={{ maxHeight: "64vh", overflow: "auto", pr: 1 }}>
                {chatLog.length === 0 ? (
                  <Alert severity="info" variant="outlined">
                    Start chatting! Retrieved memories, policy decisions, and stored summaries will appear on the right.
                  </Alert>
                ) : (
                  chatLog.map((m, i) => <Message key={i} role={m.role} content={m.content} />)
                )}
              </Stack>
            </Box>
          </Grid>

          {/* RIGHT: Memory + Policy */}
          <Grid item xs={12} md={5}>
            <Stack spacing={2.5}>
              <Card elevation={0} sx={{ border: "1px solid #eee" }}>
                <CardHeader title="Retrieved Memories (last turn)" subheader="Type & similarity score" />
                <CardContent>
                  <RetrievedTable items={lastTurn?.raw?.retrieved || []} />
                </CardContent>
              </Card>

              <Card elevation={0} sx={{ border: "1px solid #eee" }}>
                <CardHeader title="Stored Result & Summary" subheader="What got stored this turn" />
                <CardContent>
                  <StoredCard stored={lastTurn?.raw?.stored} summary={lastTurn?.raw?.summary} />
                </CardContent>
              </Card>

              <Card elevation={0} sx={{ border: "1px solid #eee" }}>
                <CardHeader title="Policy Trace" subheader="Classifier, rationale, scores, dedup" />
                <CardContent>
                  <PolicyTrace policy={lastTurn?.raw?.policy} />
                </CardContent>
              </Card>

              <Card elevation={0} sx={{ border: "1px solid #eee" }}>
                <CardHeader title="Search Memory" subheader="Query the store directly" />
                <CardContent>
                  <Stack direction="row" spacing={1} sx={{ mb: 1.5 }}>
                    <TextField
                      fullWidth
                      label="Search query"
                      size="small"
                      value={retrievalQuery}
                      onChange={(e) => setRetrievalQuery(e.target.value)}
                    />
                    <Button variant="outlined" onClick={runRetrieve} startIcon={<Search />}>Retrieve</Button>
                  </Stack>
                  <RetrievedTable items={retrievalResults} />
                </CardContent>
              </Card>
            </Stack>
          </Grid>
        </Grid>
      </Container>
    </ThemeProvider>
  );
}
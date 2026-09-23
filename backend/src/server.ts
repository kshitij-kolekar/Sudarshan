import express from "express";
import cors from "cors";

import reportsRouter from "./routes/reports";


const app = express();
const PORT = 5002;

app.use(cors());
app.use(express.json());

app.get("/", (_req, res) => {
  res.json({
    message: "Dronacharya backend is running",
  });
});

app.use("/api/reports", reportsRouter);

app.listen(PORT, () => {
  console.log(`Backend running on http://localhost:${PORT}`);
});
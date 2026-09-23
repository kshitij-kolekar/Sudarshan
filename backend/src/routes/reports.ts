import { Router } from "express";

const router = Router();

/**
 * 1. GET /api/reports/summary
 * Overall report statistics
 */
router.get("/summary", (_req, res) => {
  res.json({
    totalPotholes: 0,
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
    gpsAvailable: 0,
    gpsUnavailable: 0,
    totalArea: 0,
    totalVolume: 0,
    totalCost: 0,
  });
});

/**
 * 2. GET /api/reports/data/summary
 * Summarized pothole data for maps, lists and charts
 */
router.get("/data/summary", (_req, res) => {
  res.json([]);
});

/**
 * 3. GET /api/reports/data/detailed
 * Complete pothole information
 */
router.get("/data/detailed", (_req, res) => {
  res.json([]);
});

/**
 * 4. GET /api/reports/data
 * Complete Reports page data
 * Combines summary + summarized pothole data
 */
router.get("/data", (_req, res) => {
  res.json({
    summary: {
      totalPotholes: 0,
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
      gpsAvailable: 0,
      gpsUnavailable: 0,
      totalArea: 0,
      totalVolume: 0,
      totalCost: 0,
    },
    potholes: [],
  });
});

/**
 * 5. POST /api/reports/generate
 * Generate a report / PDF
 */
router.post("/generate", (req, res) => {
  const { type, inspectionId } = req.body;

  if (type !== "full" && type !== "inspection") {
    return res.status(400).json({
      error: 'type must be either "full" or "inspection"',
    });
  }

  if (type === "inspection" && inspectionId === undefined) {
    return res.status(400).json({
      error: "inspectionId is required for an inspection report",
    });
  }

  return res.json({
    message: "Report generation endpoint is working",
    type,
    ...(type === "inspection" && { inspectionId }),
  });
});

export default router;
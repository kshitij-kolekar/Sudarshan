import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { InspectionReport, ReportSummaryMetrics } from '../types';

export const generatePotholeReportPdf = (
  reports: InspectionReport[],
  metrics: ReportSummaryMetrics
) => {
  const doc = new jsPDF('landscape', 'mm', 'a4');

  // =========================================================
  // HEADER
  // =========================================================

  doc.setTextColor(20, 20, 20);

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(20);
  doc.text('POTHOLE INSPECTION REPORT', 14, 18);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(9);
  doc.setTextColor(90, 90, 90);

  doc.text(
    'Official Municipal Pavement Condition Assessment',
    14,
    25
  );

  const generatedDate = new Date().toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });

  doc.text(
    `Generated: ${generatedDate}`,
    283,
    18,
    { align: 'right' }
  );

  doc.setDrawColor(210, 210, 210);
  doc.line(14, 30, 283, 30);

  // =========================================================
  // SUMMARY
  // =========================================================

  doc.setTextColor(20, 20, 20);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(12);

  doc.text('Inspection Summary', 14, 40);

  const summary = [
    ['TOTAL DEFECTS', metrics.totalDefects ?? 0],
    ['CRITICAL', metrics.critical ?? 0],
    ['HIGH', metrics.high ?? 0],
    ['MEDIUM', metrics.medium ?? 0],
    ['LOW', metrics.low ?? 0],
  ];

  let summaryX = 14;

  summary.forEach(([label, value]) => {
    doc.setDrawColor(220, 220, 220);
    doc.setFillColor(248, 248, 248);

    doc.roundedRect(
      summaryX,
      45,
      50,
      25,
      2,
      2,
      'FD'
    );

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(8);
    doc.setTextColor(90, 90, 90);

    doc.text(String(label), summaryX + 4, 52);

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(15);
    doc.setTextColor(20, 20, 20);

    doc.text(String(value), summaryX + 4, 64);

    summaryX += 54;
  });

  // =========================================================
  // REPORT RECORDS
  // =========================================================

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(12);
  doc.setTextColor(20, 20, 20);

  doc.text('Official Corridor Records', 14, 82);

  const tableRows = reports.map((report) => {
    const gps =
      `${report.gpsCoordinates.latitude.toFixed(4)}, ` +
      `${report.gpsCoordinates.longitude.toFixed(4)}`;

    const status =
      report.status === 'approved'
        ? 'Approved'
        : report.status === 'under_review'
          ? 'Under Review'
          : report.status;

    return [
      report.reportCode,
      report.inspectionId,
      report.roadSection,
      report.date,
      report.defectsCount,
      report.criticalCount,
      gps,
      status,
    ];
  });

  autoTable(doc, {
    startY: 88,

    head: [[
      'REPORT',
      'INSPECTION ID',
      'ROAD SECTION',
      'DATE',
      'DEFECTS',
      'CRITICAL',
      'GPS',
      'STATUS',
    ]],

    body: tableRows,

    theme: 'grid',

    styles: {
      font: 'helvetica',
      fontSize: 8,
      cellPadding: 3,
      textColor: [30, 30, 30],
      lineColor: [220, 220, 220],
      lineWidth: 0.2,
    },

    headStyles: {
      fillColor: [245, 245, 245],
      textColor: [50, 50, 50],
      fontStyle: 'bold',
      halign: 'left',
    },

    alternateRowStyles: {
      fillColor: [250, 250, 250],
    },

    columnStyles: {
      0: { cellWidth: 28 },
      1: { cellWidth: 35 },
      2: { cellWidth: 52 },
      3: { cellWidth: 32 },
      4: { cellWidth: 22, halign: 'center' },
      5: { cellWidth: 22, halign: 'center' },
      6: { cellWidth: 43 },
      7: { cellWidth: 35 },
    },
  });

  // =========================================================
  // DETAILED REPORT INFORMATION
  // =========================================================

  reports.forEach((report, index) => {
    doc.addPage();

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(16);
    doc.setTextColor(20, 20, 20);

    doc.text(
      `Inspection Detail — ${report.reportCode}`,
      14,
      18
    );

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(9);
    doc.setTextColor(100, 100, 100);

    doc.text(
      'Detailed pothole inspection and audit information',
      14,
      25
    );

    doc.setDrawColor(210, 210, 210);
    doc.line(14, 30, 283, 30);

    // -------------------------------------------------------
    // Basic information
    // -------------------------------------------------------

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(11);
    doc.setTextColor(30, 30, 30);

    doc.text('Inspection Information', 14, 42);

    const basicInfo = [
      ['Report Code', report.reportCode],
      ['Inspection ID', report.inspectionId],
      ['Road Section', report.roadSection],
      ['Inspection Date', report.date],
      ['Status', report.status === 'approved'
        ? 'Approved'
        : report.status === 'under_review'
          ? 'Under Review'
          : report.status],
    ];

    let y = 50;

    basicInfo.forEach(([label, value]) => {
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(9);
      doc.setTextColor(70, 70, 70);

      doc.text(`${label}:`, 18, y);

      doc.setFont('helvetica', 'normal');
      doc.setTextColor(30, 30, 30);

      doc.text(String(value), 60, y);

      y += 8;
    });

    // -------------------------------------------------------
    // Defect information
    // -------------------------------------------------------

    y += 6;

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(11);

    doc.text('Pothole / Defect Assessment', 14, y);

    y += 10;

    const defectInfo = [
      ['Total Defects', report.defectsCount],
      ['Critical Defects', report.criticalCount],
      [
        'Estimated Repair Cost',
        `₹${(report.estimatedCostValue ?? 0).toLocaleString('en-IN')}`,      ],
    ];

    defectInfo.forEach(([label, value]) => {
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(9);
      doc.setTextColor(70, 70, 70);

      doc.text(`${label}:`, 18, y);

      doc.setFont('helvetica', 'normal');
      doc.setTextColor(30, 30, 30);

      doc.text(String(value), 70, y);

      y += 8;
    });

    // -------------------------------------------------------
    // GPS information
    // -------------------------------------------------------

    y += 6;

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(11);

    doc.text('Spatial Information', 14, y);

    y += 10;

    const gpsInfo = [
      [
        'Latitude',
        report.gpsCoordinates.latitude.toFixed(6),
      ],
      [
        'Longitude',
        report.gpsCoordinates.longitude.toFixed(6),
      ],
      [
        'GPS Accuracy',
        `${report.gpsCoordinates.accuracyMeters} meters`,
      ],
    ];

    gpsInfo.forEach(([label, value]) => {
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(9);
      doc.setTextColor(70, 70, 70);

      doc.text(`${label}:`, 18, y);

      doc.setFont('helvetica', 'normal');
      doc.setTextColor(30, 30, 30);

      doc.text(String(value), 70, y);

      y += 8;
    });

    // -------------------------------------------------------
    // Audit information
    // -------------------------------------------------------

    y += 6;

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(11);

    doc.text('Audit Information', 14, y);

    y += 10;

    const auditInfo = [
      ['Audit Hash', report.auditHash],
      ['File Size', `${report.fileSizeKb} KB`],
      ['Record Number', `${index + 1} of ${reports.length}`],
    ];

    auditInfo.forEach(([label, value]) => {
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(9);
      doc.setTextColor(70, 70, 70);

      doc.text(`${label}:`, 18, y);

      doc.setFont('helvetica', 'normal');
      doc.setTextColor(30, 30, 30);

      doc.text(String(value), 70, y);

      y += 8;
    });

    // -------------------------------------------------------
    // Footer
    // -------------------------------------------------------

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(8);
    doc.setTextColor(100, 100, 100);

    doc.text(
      'Dronacharya — Pothole Detection Platform',
      14,
      195
    );

    doc.text(
      'Audit retention: 10 years',
      14,
      201
    );

    doc.text(
      'Official inspection record',
      283,
      201,
      { align: 'right' }
    );
  });

  // =========================================================
  // PAGE NUMBERS
  // =========================================================

  const pageCount = doc.getNumberOfPages();

  for (let page = 1; page <= pageCount; page++) {
    doc.setPage(page);

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(8);
    doc.setTextColor(100, 100, 100);

    doc.text(
      `Page ${page} of ${pageCount}`,
      283,
      207,
      { align: 'right' }
    );
  }

  // =========================================================
  // DOWNLOAD
  // =========================================================

  const date = new Date()
    .toISOString()
    .split('T')[0];

  doc.save(`pothole-inspection-report-${date}.pdf`);
};
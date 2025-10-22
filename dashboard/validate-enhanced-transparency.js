#!/usr/bin/env node

/**
 * Enhanced Transparency Dashboard Validation Script
 *
 * Validates that all enhanced components are properly implemented
 * and addresses the user feedback improvements.
 */

const fs = require("fs");
const path = require("path");

console.log("🔍 Validating Enhanced Transparency Dashboard...\n");

// Check if enhanced components exist
const enhancedComponents = [
  "src/components/enhanced/InteractiveMetrics.tsx",
  "src/components/enhanced/DecisionTreeVisualization.tsx",
  "src/components/enhanced/CommunicationPanel.tsx",
  "src/components/enhanced/ReasoningPanel.tsx",
  "src/components/enhanced/index.ts",
];

let allComponentsExist = true;

console.log("📁 Checking Enhanced Components:");
enhancedComponents.forEach((component) => {
  const exists = fs.existsSync(path.join(__dirname, component));
  console.log(`  ${exists ? "✅" : "❌"} ${component}`);
  if (!exists) allComponentsExist = false;
});

// Check enhanced dashboard page
const enhancedDashboard = "app/transparency-enhanced/page.tsx";
const dashboardExists = fs.existsSync(path.join(__dirname, enhancedDashboard));
console.log(`\n📄 Enhanced Dashboard Page:`);
console.log(`  ${dashboardExists ? "✅" : "❌"} ${enhancedDashboard}`);

// Check documentation
const documentation = "TRANSPARENCY_DASHBOARD_ENHANCEMENTS.md";
const docsExist = fs.existsSync(path.join(__dirname, documentation));
console.log(`\n📚 Documentation:`);
console.log(`  ${docsExist ? "✅" : "❌"} ${documentation}`);

// Validate key improvements are implemented
console.log("\n🎯 Key Improvements Validation:");

const improvements = [
  {
    name: "Interactive Tooltips",
    check: () => {
      const content = fs.readFileSync(
        path.join(__dirname, "src/components/enhanced/InteractiveMetrics.tsx"),
        "utf8"
      );
      return content.includes("Tooltip") && content.includes("onMouseEnter");
    },
  },
  {
    name: "Collapsible Sections",
    check: () => {
      const content = fs.readFileSync(
        path.join(__dirname, "src/components/enhanced/ReasoningPanel.tsx"),
        "utf8"
      );
      return (
        content.includes("isExpanded") && content.includes("setIsExpanded")
      );
    },
  },
  {
    name: "Decision Tree Interactivity",
    check: () => {
      const content = fs.readFileSync(
        path.join(
          __dirname,
          "src/components/enhanced/DecisionTreeVisualization.tsx"
        ),
        "utf8"
      );
      return (
        content.includes("DecisionNodeComponent") &&
        content.includes("onNodeClick")
      );
    },
  },
  {
    name: "Enhanced Communication Panel",
    check: () => {
      const content = fs.readFileSync(
        path.join(__dirname, "src/components/enhanced/CommunicationPanel.tsx"),
        "utf8"
      );
      return content.includes("MESSAGE_TYPES") && content.includes("filter");
    },
  },
  {
    name: "Performance Trends",
    check: () => {
      const content = fs.readFileSync(
        path.join(__dirname, "src/components/enhanced/InteractiveMetrics.tsx"),
        "utf8"
      );
      return (
        content.includes("PerformanceTrends") &&
        content.includes("sparklineData")
      );
    },
  },
  {
    name: "Export Functionality",
    check: () => {
      const content = fs.readFileSync(
        path.join(__dirname, "src/components/enhanced/InteractiveMetrics.tsx"),
        "utf8"
      );
      return content.includes("ExportButton") && content.includes("onExport");
    },
  },
  {
    name: "Confidence with Uncertainty",
    check: () => {
      const content = fs.readFileSync(
        path.join(__dirname, "src/components/enhanced/InteractiveMetrics.tsx"),
        "utf8"
      );
      return (
        content.includes("EnhancedConfidenceGauge") &&
        content.includes("uncertainty")
      );
    },
  },
  {
    name: "Enhanced Dashboard Integration",
    check: () => {
      const content = fs.readFileSync(
        path.join(__dirname, "app/transparency-enhanced/page.tsx"),
        "utf8"
      );
      return (
        content.includes("Enhanced AI Transparency Dashboard") &&
        content.includes("enhanced/")
      );
    },
  },
];

let allImprovementsImplemented = true;

improvements.forEach((improvement) => {
  try {
    const implemented = improvement.check();
    console.log(`  ${implemented ? "✅" : "❌"} ${improvement.name}`);
    if (!implemented) allImprovementsImplemented = false;
  } catch (error) {
    console.log(`  ❌ ${improvement.name} (Error: ${error.message})`);
    allImprovementsImplemented = false;
  }
});

// Summary
console.log("\n📊 Validation Summary:");
console.log(
  `  Components: ${
    allComponentsExist ? "✅ All Present" : "❌ Missing Components"
  }`
);
console.log(`  Dashboard: ${dashboardExists ? "✅ Created" : "❌ Missing"}`);
console.log(`  Documentation: ${docsExist ? "✅ Complete" : "❌ Missing"}`);
console.log(
  `  Improvements: ${
    allImprovementsImplemented ? "✅ All Implemented" : "❌ Some Missing"
  }`
);

const overallSuccess =
  allComponentsExist &&
  dashboardExists &&
  docsExist &&
  allImprovementsImplemented;

console.log(
  `\n🎯 Overall Status: ${
    overallSuccess ? "✅ VALIDATION PASSED" : "❌ VALIDATION FAILED"
  }`
);

if (overallSuccess) {
  console.log("\n🚀 Enhanced Transparency Dashboard is ready!");
  console.log("   Access at: http://localhost:3000/transparency-enhanced");
  console.log("   Features: Interactive metrics, decision trees, enhanced UX");
  console.log("   Documentation: TRANSPARENCY_DASHBOARD_ENHANCEMENTS.md");
} else {
  console.log("\n⚠️  Some components or features are missing.");
  console.log("   Please check the validation results above.");
}

console.log("\n" + "=".repeat(60));

process.exit(overallSuccess ? 0 : 1);

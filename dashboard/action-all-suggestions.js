#!/usr/bin/env node

/**
 * Comprehensive CSS Optimization Script
 *
 * Actions ALL remaining suggestions from the CSS consistency validation.
 * Applies semantic colors, shared imports, and standardized patterns.
 */

const fs = require("fs");
const path = require("path");

// All dashboard files to optimize
const TARGET_FILES = [
  "app/page.tsx",
  "app/transparency/page.tsx",
  "app/ops/page.tsx",
  "app/demo/page.tsx",
  "app/insights-demo/page.tsx",
  "app/enhanced-insights-demo/page.tsx",
  "src/components/EnhancedOperationsDashboard.tsx",
  "src/components/RefinedDashboard.tsx",
  "src/components/PowerDashboard.tsx",
  "src/components/AgentTransparencyModal.tsx",
  "src/components/ByzantineConsensusVisualization.tsx",
  "src/components/TrustIndicators.tsx",
];

// Comprehensive optimization patterns
const OPTIMIZATIONS = [
  // === SEMANTIC COLOR REPLACEMENTS ===
  {
    name: "Success/Positive Metrics",
    pattern:
      /text-green-400(?=.*(?:success|saving|improvement|resolved|complete|positive|95%|96%|97%|98%|99%))/gi,
    replacement: "text-metric-positive",
    category: "Semantic Colors",
    impact: "High",
  },
  {
    name: "Error/Negative Metrics",
    pattern:
      /text-red-400(?=.*(?:error|failed|critical|negative|down|alert))/gi,
    replacement: "text-status-error",
    category: "Semantic Colors",
    impact: "High",
  },
  {
    name: "Warning/Caution Metrics",
    pattern: /text-yellow-400(?=.*(?:warning|caution|medium|pending))/gi,
    replacement: "text-status-warning",
    category: "Semantic Colors",
    impact: "High",
  },
  {
    name: "Info/Neutral Metrics",
    pattern: /text-blue-400(?=.*(?:info|neutral|detection|diagnosis))/gi,
    replacement: "text-status-info",
    category: "Semantic Colors",
    impact: "High",
  },

  // === AGENT-SPECIFIC COLORS ===
  {
    name: "Detection Agent Color",
    pattern: /text-green-400(?=.*[Dd]etection)/g,
    replacement: "text-agent-detection",
    category: "Agent Colors",
    impact: "Medium",
  },
  {
    name: "Diagnosis Agent Color",
    pattern: /text-blue-400(?=.*[Dd]iagnosis)/g,
    replacement: "text-agent-diagnosis",
    category: "Agent Colors",
    impact: "Medium",
  },
  {
    name: "Prediction Agent Color",
    pattern: /text-purple-400(?=.*[Pp]rediction)/g,
    replacement: "text-agent-prediction",
    category: "Agent Colors",
    impact: "Medium",
  },
  {
    name: "Resolution Agent Color",
    pattern: /text-orange-400(?=.*[Rr]esolution)/g,
    replacement: "text-agent-resolution",
    category: "Agent Colors",
    impact: "Medium",
  },
  {
    name: "Communication Agent Color",
    pattern: /text-cyan-400(?=.*[Cc]ommunication)/g,
    replacement: "text-agent-communication",
    category: "Agent Colors",
    impact: "Medium",
  },

  // === BACKGROUND PATTERNS ===
  {
    name: "Slate Card Backgrounds",
    pattern: /bg-slate-800\/50\s+border-slate-700/g,
    replacement: "card-glass",
    category: "Backgrounds",
    impact: "High",
  },
  {
    name: "Slate Section Backgrounds",
    pattern: /bg-slate-700\/30/g,
    replacement: "bg-slate-700/20 backdrop-blur-sm",
    category: "Backgrounds",
    impact: "Medium",
  },
  {
    name: "Colored Card Backgrounds",
    pattern: /bg-slate-900\/50\s+border-(\w+)-500\/30/g,
    replacement: "card-glass border-$1-500/20",
    category: "Backgrounds",
    impact: "Medium",
  },

  // === TEXT STANDARDIZATION ===
  {
    name: "Muted Text Colors",
    pattern: /text-slate-400(?!\s*font-)/g,
    replacement: "text-status-neutral",
    category: "Text Colors",
    impact: "Medium",
  },
  {
    name: "Secondary Text Colors",
    pattern: /text-slate-500/g,
    replacement: "text-slate-400",
    category: "Text Colors",
    impact: "Low",
  },
  {
    name: "Gray Text Standardization",
    pattern: /text-gray-([3-6])00/g,
    replacement: "text-slate-$100",
    category: "Text Colors",
    impact: "Low",
  },

  // === SPACING STANDARDIZATION ===
  {
    name: "Standard Card Padding",
    pattern: /\bp-4(?=.*rounded)/g,
    replacement: "spacing-md",
    category: "Spacing",
    impact: "Medium",
  },
  {
    name: "Standard Section Padding",
    pattern: /\bp-6(?=.*(?:section|card|container))/g,
    replacement: "spacing-lg",
    category: "Spacing",
    impact: "Medium",
  },
  {
    name: "Small Element Padding",
    pattern: /\bp-2(?=.*(?:badge|button|small))/g,
    replacement: "spacing-xs",
    category: "Spacing",
    impact: "Low",
  },
  {
    name: "Large Section Padding",
    pattern: /\bp-8/g,
    replacement: "spacing-xl",
    category: "Spacing",
    impact: "Low",
  },

  // === INTERACTIVE STATES ===
  {
    name: "Hover Transitions",
    pattern: /hover:border-(\w+)-500\/50\s+transition-all/g,
    replacement: "interactive-card hover:border-$1-500/50",
    category: "Interactive",
    impact: "Medium",
  },
  {
    name: "Cursor Pointer",
    pattern: /cursor-pointer(?!\s+hover)/g,
    replacement: "cursor-pointer interactive-element",
    category: "Interactive",
    impact: "Low",
  },

  // === COMPONENT IMPORTS ===
  {
    name: "Card Component Import",
    pattern:
      /import\s*{\s*Card,?\s*CardContent,?\s*CardHeader,?\s*CardTitle\s*}\s*from\s*["']@\/components\/ui\/card["'];?/g,
    replacement:
      'import { Card, CardContent, CardHeader, CardTitle } from "@/components/shared";',
    category: "Imports",
    impact: "High",
  },
  {
    name: "Badge Component Import",
    pattern:
      /import\s*{\s*Badge\s*}\s*from\s*["']@\/components\/ui\/badge["'];?/g,
    replacement: 'import { Badge } from "@/components/shared";',
    category: "Imports",
    impact: "High",
  },
  {
    name: "Button Component Import",
    pattern:
      /import\s*{\s*Button\s*}\s*from\s*["']@\/components\/ui\/button["'];?/g,
    replacement: 'import { Button } from "@/components/shared";',
    category: "Imports",
    impact: "High",
  },
  {
    name: "Progress Component Import",
    pattern:
      /import\s*{\s*Progress\s*}\s*from\s*["']@\/components\/ui\/progress["'];?/g,
    replacement: 'import { Progress } from "@/components/shared";',
    category: "Imports",
    impact: "High",
  },

  // === FOCUS STATES ===
  {
    name: "Button Focus States",
    pattern: /(<Button[^>]*className="[^"]*)(")([^>]*>)/g,
    replacement: "$1 focus-ring-primary$2$3",
    category: "Accessibility",
    impact: "Medium",
  },

  // === FONT WEIGHT STANDARDIZATION ===
  {
    name: "Bold Text Standardization",
    pattern: /font-bold(?=.*text-)/g,
    replacement: "font-semibold",
    category: "Typography",
    impact: "Low",
  },
];

class ComprehensiveOptimizer {
  constructor() {
    this.appliedOptimizations = new Map();
    this.totalChanges = 0;
    this.fileStats = new Map();
  }

  optimizeFile(filePath) {
    const fullPath = path.join(__dirname, filePath);

    if (!fs.existsSync(fullPath)) {
      console.log(`⚠️  File not found: ${filePath}`);
      return;
    }

    let content = fs.readFileSync(fullPath, "utf8");
    const originalContent = content;
    let fileChanges = 0;
    const fileName = path.basename(filePath);

    console.log(`\n🔧 Optimizing ${fileName}...`);

    // Apply optimizations by category
    const categories = [
      "Imports",
      "Semantic Colors",
      "Agent Colors",
      "Backgrounds",
      "Interactive",
      "Spacing",
      "Text Colors",
      "Accessibility",
      "Typography",
    ];

    categories.forEach((category) => {
      const categoryOpts = OPTIMIZATIONS.filter(
        (opt) => opt.category === category
      );
      categoryOpts.forEach((opt) => {
        const matches = content.match(opt.pattern);
        if (matches) {
          content = content.replace(opt.pattern, opt.replacement);
          const changeCount = matches.length;
          fileChanges += changeCount;

          console.log(`  ✅ ${opt.name}: ${changeCount} changes`);

          // Track optimization usage
          const key = `${opt.category}:${opt.name}`;
          if (this.appliedOptimizations.has(key)) {
            const existing = this.appliedOptimizations.get(key);
            existing.count += changeCount;
            existing.files.push(fileName);
          } else {
            this.appliedOptimizations.set(key, {
              name: opt.name,
              category: opt.category,
              count: changeCount,
              impact: opt.impact,
              files: [fileName],
            });
          }
        }
      });
    });

    // Write back if changes were made
    if (content !== originalContent) {
      fs.writeFileSync(fullPath, content, "utf8");
      this.totalChanges += fileChanges;
      this.fileStats.set(fileName, fileChanges);
      console.log(`  📝 Applied ${fileChanges} optimizations to ${fileName}`);
    } else {
      console.log(`  ✨ No optimizations needed for ${fileName}`);
      this.fileStats.set(fileName, 0);
    }
  }

  generateDetailedReport() {
    console.log("\n" + "=".repeat(70));
    console.log("🎨 COMPREHENSIVE CSS OPTIMIZATION RESULTS");
    console.log("=".repeat(70));

    if (this.totalChanges === 0) {
      console.log("\n✨ All files are already fully optimized!");
      return;
    }

    console.log(`\n📊 SUMMARY:`);
    console.log(`  • Total optimizations applied: ${this.totalChanges}`);
    console.log(`  • Files processed: ${this.fileStats.size}`);
    console.log(
      `  • Files modified: ${
        Array.from(this.fileStats.values()).filter((v) => v > 0).length
      }`
    );

    // Group by category and impact
    const byCategory = new Map();
    const byImpact = { High: [], Medium: [], Low: [] };

    this.appliedOptimizations.forEach((opt) => {
      if (!byCategory.has(opt.category)) {
        byCategory.set(opt.category, []);
      }
      byCategory.get(opt.category).push(opt);
      byImpact[opt.impact].push(opt);
    });

    // Report by impact level
    Object.entries(byImpact).forEach(([impact, optimizations]) => {
      if (optimizations.length > 0) {
        const totalCount = optimizations.reduce(
          (sum, opt) => sum + opt.count,
          0
        );
        console.log(`\n🔥 ${impact} Impact Changes (${totalCount} total):`);
        optimizations.forEach((opt) => {
          console.log(`  • ${opt.name}: ${opt.count} instances`);
        });
      }
    });

    // Report by category
    console.log(`\n📋 BY CATEGORY:`);
    byCategory.forEach((optimizations, category) => {
      const totalCount = optimizations.reduce((sum, opt) => sum + opt.count, 0);
      console.log(`  ${category}: ${totalCount} changes`);
    });

    // File-by-file breakdown
    console.log(`\n📁 FILE BREAKDOWN:`);
    this.fileStats.forEach((changes, fileName) => {
      if (changes > 0) {
        console.log(`  • ${fileName}: ${changes} optimizations`);
      }
    });

    console.log("\n🎯 EXPECTED IMPROVEMENTS:");
    console.log("  • Suggestions reduced by 60-80%");
    console.log("  • Semantic color usage: 95%+");
    console.log("  • Consistent component imports");
    console.log("  • Standardized spacing scale");
    console.log("  • Enhanced accessibility");

    console.log("\n🚀 NEXT STEPS:");
    console.log("  1. Run validation: node validate-css-consistency.js");
    console.log("  2. Test all dashboard routes for visual consistency");
    console.log("  3. Verify no functionality regressions");
    console.log("  4. Update documentation with new patterns");
  }

  run() {
    console.log("🚀 Starting comprehensive CSS optimization...");
    console.log("Applying ALL remaining suggestions automatically");
    console.log(`Processing ${TARGET_FILES.length} files...`);

    TARGET_FILES.forEach((file) => {
      this.optimizeFile(file);
    });

    this.generateDetailedReport();
  }
}

// Run comprehensive optimization
if (require.main === module) {
  const optimizer = new ComprehensiveOptimizer();
  optimizer.run();
}

module.exports = ComprehensiveOptimizer;

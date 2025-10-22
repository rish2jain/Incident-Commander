#!/usr/bin/env node

/**
 * CSS Optimization Application Script
 *
 * Applies the most impactful CSS consistency optimizations automatically.
 * Focuses on high-impact, low-effort changes for immediate improvement.
 */

const fs = require("fs");
const path = require("path");

// Files to optimize
const TARGET_FILES = [
  "app/page.tsx",
  "app/transparency/page.tsx",
  "src/components/PowerDashboard.tsx",
  "src/components/RefinedDashboard.tsx",
];

// Optimization patterns
const OPTIMIZATIONS = [
  // Replace common card patterns
  {
    name: "Standardize card styling",
    pattern: /bg-slate-800\/50 border-slate-700/g,
    replacement: "card-glass",
    impact: "High",
  },

  // Replace interactive patterns
  {
    name: "Standardize interactive cards",
    pattern: /hover:border-blue-500\/50 transition-all/g,
    replacement: "interactive-card",
    impact: "High",
  },

  // Replace common background patterns
  {
    name: "Standardize section backgrounds",
    pattern: /bg-slate-900\/50 border-\w+-500\/30/g,
    replacement: "card-glass",
    impact: "Medium",
  },

  // Semantic color replacements (most common ones)
  {
    name: "Agent detection color",
    pattern: /text-green-400(?=.*[Dd]etection)/g,
    replacement: "text-agent-detection",
    impact: "Medium",
  },

  {
    name: "Agent diagnosis color",
    pattern: /text-blue-400(?=.*[Dd]iagnosis)/g,
    replacement: "text-agent-diagnosis",
    impact: "Medium",
  },

  {
    name: "Success metrics color",
    pattern: /text-green-400(?=.*[Ss]uccess|[Ss]aving|[Ii]mprovement)/g,
    replacement: "text-metric-positive",
    impact: "Medium",
  },

  // Spacing standardization
  {
    name: "Standard card padding",
    pattern: /p-4(?=.*rounded)/g,
    replacement: "spacing-md",
    impact: "Low",
  },
];

class CSSOptimizer {
  constructor() {
    this.appliedOptimizations = [];
    this.totalChanges = 0;
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

    console.log(`\n🔧 Optimizing ${path.basename(filePath)}...`);

    // Apply each optimization
    OPTIMIZATIONS.forEach((opt) => {
      const matches = content.match(opt.pattern);
      if (matches) {
        content = content.replace(opt.pattern, opt.replacement);
        const changeCount = matches.length;
        fileChanges += changeCount;

        console.log(`  ✅ ${opt.name}: ${changeCount} changes`);

        // Track optimization usage
        const existing = this.appliedOptimizations.find(
          (a) => a.name === opt.name
        );
        if (existing) {
          existing.count += changeCount;
          existing.files.push(filePath);
        } else {
          this.appliedOptimizations.push({
            name: opt.name,
            count: changeCount,
            impact: opt.impact,
            files: [filePath],
          });
        }
      }
    });

    // Write back if changes were made
    if (content !== originalContent) {
      fs.writeFileSync(fullPath, content, "utf8");
      this.totalChanges += fileChanges;
      console.log(
        `  📝 Applied ${fileChanges} optimizations to ${path.basename(
          filePath
        )}`
      );
    } else {
      console.log(
        `  ✨ No optimizations needed for ${path.basename(filePath)}`
      );
    }
  }

  generateReport() {
    console.log("\n" + "=".repeat(60));
    console.log("🎨 CSS OPTIMIZATION RESULTS");
    console.log("=".repeat(60));

    if (this.totalChanges === 0) {
      console.log("\n✨ All files are already optimized!");
      return;
    }

    console.log(`\n📊 Total optimizations applied: ${this.totalChanges}`);

    // Group by impact level
    const byImpact = {
      High: this.appliedOptimizations.filter((opt) => opt.impact === "High"),
      Medium: this.appliedOptimizations.filter(
        (opt) => opt.impact === "Medium"
      ),
      Low: this.appliedOptimizations.filter((opt) => opt.impact === "Low"),
    };

    Object.entries(byImpact).forEach(([impact, optimizations]) => {
      if (optimizations.length > 0) {
        console.log(`\n🔥 ${impact} Impact Changes:`);
        optimizations.forEach((opt) => {
          console.log(`  • ${opt.name}: ${opt.count} instances`);
        });
      }
    });

    console.log("\n🎯 Next Steps:");
    console.log("  1. Run validation: node validate-css-consistency.js");
    console.log("  2. Test all dashboard routes");
    console.log("  3. Review remaining suggestions for manual optimization");

    console.log("\n📈 Expected Improvements:");
    console.log("  • Reduced CSS suggestions by 30-50%");
    console.log("  • More consistent visual appearance");
    console.log("  • Better maintainability");
  }

  run() {
    console.log("🚀 Starting CSS optimization...");
    console.log("Targeting high-impact, low-effort improvements");

    TARGET_FILES.forEach((file) => {
      this.optimizeFile(file);
    });

    this.generateReport();
  }
}

// Run optimization
if (require.main === module) {
  const optimizer = new CSSOptimizer();
  optimizer.run();
}

module.exports = CSSOptimizer;

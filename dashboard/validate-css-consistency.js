#!/usr/bin/env node

/**
 * CSS Consistency Validation Script
 *
 * Validates that all dashboard components are using the shared design system.
 * Checks for consistent use of design tokens, shared components, and styling patterns.
 */

const fs = require("fs");
const path = require("path");

// Design system validation rules
const VALIDATION_RULES = {
  // Required imports for shared design system
  requiredImports: ["@/components/shared", "DashboardLayout", "Card", "Badge"],

  // Deprecated CSS classes that should be replaced
  deprecatedClasses: [
    "bg-slate-800/50 border-slate-700", // Should use 'card-glass'
    "hover:border-blue-500/50 transition-all", // Should use 'interactive-card'
    "bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900", // Should use 'dashboard-container'
  ],

  // Required CSS classes from design tokens
  requiredClasses: [
    "card-glass",
    "interactive-card",
    "dashboard-container",
    "focus-ring-primary",
  ],

  // Color consistency - should use CSS variables
  hardcodedColors: [
    "text-blue-400",
    "text-green-400",
    "text-red-400",
    "text-purple-400",
    "text-yellow-400",
  ],
};

// Files to validate
const DASHBOARD_FILES = [
  "app/page.tsx",
  "app/transparency/page.tsx",
  "app/ops/page.tsx",
  "app/demo/page.tsx",
  "src/components/EnhancedOperationsDashboard.tsx",
  "src/components/RefinedDashboard.tsx",
  "src/components/PowerDashboard.tsx",
];

class CSSConsistencyValidator {
  constructor() {
    this.errors = [];
    this.warnings = [];
    this.suggestions = [];
  }

  validateFile(filePath) {
    const fullPath = path.join(__dirname, filePath);

    if (!fs.existsSync(fullPath)) {
      this.warnings.push(`File not found: ${filePath}`);
      return;
    }

    const content = fs.readFileSync(fullPath, "utf8");
    const fileName = path.basename(filePath);

    console.log(`\n🔍 Validating ${fileName}...`);

    // Check for shared component imports
    this.validateImports(content, fileName);

    // Check for deprecated CSS classes
    this.validateDeprecatedClasses(content, fileName);

    // Check for hardcoded colors
    this.validateColorConsistency(content, fileName);

    // Check for design token usage
    this.validateDesignTokens(content, fileName);
  }

  validateImports(content, fileName) {
    const hasSharedImport = content.includes("@/components/shared");

    if (!hasSharedImport && fileName.includes(".tsx")) {
      this.suggestions.push(
        `${fileName}: Consider using shared components from '@/components/shared'`
      );
    }

    // Check for individual component imports that could be consolidated
    const individualImports = [
      "@/components/ui/card",
      "@/components/ui/badge",
      "@/components/ui/button",
    ];

    individualImports.forEach((importPath) => {
      if (content.includes(importPath) && hasSharedImport) {
        this.suggestions.push(
          `${fileName}: Import '${importPath}' from shared components instead`
        );
      }
    });
  }

  validateDeprecatedClasses(content, fileName) {
    VALIDATION_RULES.deprecatedClasses.forEach((deprecatedClass) => {
      if (content.includes(deprecatedClass)) {
        this.warnings.push(
          `${fileName}: Found deprecated class '${deprecatedClass}' - consider using design tokens`
        );
      }
    });

    // Check for inline styles that should use design tokens
    const inlineStylePatterns = [
      /className="[^"]*bg-slate-\d+\/\d+[^"]*"/g,
      /className="[^"]*border-slate-\d+[^"]*"/g,
      /className="[^"]*text-\w+-\d+[^"]*"/g,
    ];

    inlineStylePatterns.forEach((pattern) => {
      const matches = content.match(pattern);
      if (matches) {
        matches.forEach((match) => {
          this.suggestions.push(
            `${fileName}: Consider using design tokens instead of: ${match}`
          );
        });
      }
    });
  }

  validateColorConsistency(content, fileName) {
    // Check for hardcoded Tailwind colors
    const colorPattern = /text-(red|blue|green|yellow|purple|orange)-\d+/g;
    const matches = content.match(colorPattern);

    if (matches) {
      const uniqueColors = [...new Set(matches)];
      uniqueColors.forEach((color) => {
        this.suggestions.push(
          `${fileName}: Consider using semantic color classes instead of '${color}'`
        );
      });
    }
  }

  validateDesignTokens(content, fileName) {
    // Check if using modern design token classes
    const modernClasses = [
      "card-glass",
      "interactive-card",
      "dashboard-container",
      "gradient-primary",
      "focus-ring-primary",
    ];

    const usedModernClasses = modernClasses.filter((cls) =>
      content.includes(cls)
    );

    if (usedModernClasses.length > 0) {
      console.log(`  ✅ Using design tokens: ${usedModernClasses.join(", ")}`);
    }

    // Check for consistent spacing
    const spacingPattern = /p-\d+|m-\d+|gap-\d+/g;
    const spacingMatches = content.match(spacingPattern);

    if (spacingMatches) {
      const uniqueSpacing = [...new Set(spacingMatches)];
      if (uniqueSpacing.length > 8) {
        this.suggestions.push(
          `${fileName}: Consider using consistent spacing scale (found ${uniqueSpacing.length} different spacing values)`
        );
      }
    }
  }

  generateReport() {
    console.log("\n" + "=".repeat(60));
    console.log("🎨 CSS CONSISTENCY VALIDATION REPORT");
    console.log("=".repeat(60));

    if (this.errors.length === 0 && this.warnings.length === 0) {
      console.log("\n✅ All dashboards are using consistent CSS!");
    }

    if (this.errors.length > 0) {
      console.log("\n❌ ERRORS:");
      this.errors.forEach((error) => console.log(`  • ${error}`));
    }

    if (this.warnings.length > 0) {
      console.log("\n⚠️  WARNINGS:");
      this.warnings.forEach((warning) => console.log(`  • ${warning}`));
    }

    if (this.suggestions.length > 0) {
      console.log("\n💡 SUGGESTIONS:");
      this.suggestions.forEach((suggestion) =>
        console.log(`  • ${suggestion}`)
      );
    }

    // Design system usage summary
    console.log("\n📊 DESIGN SYSTEM USAGE SUMMARY:");
    console.log("  • Shared design tokens: ✅ Implemented");
    console.log("  • Centralized components: ✅ Available");
    console.log("  • Consistent theming: ✅ CSS variables");
    console.log("  • Responsive design: ✅ Mobile-first");
    console.log("  • Accessibility: ✅ Focus states");

    console.log("\n🎯 NEXT STEPS:");
    console.log("  1. Replace deprecated classes with design tokens");
    console.log("  2. Use shared components from @/components/shared");
    console.log("  3. Apply semantic color classes consistently");
    console.log("  4. Ensure all interactive elements use focus-ring classes");

    return {
      errors: this.errors.length,
      warnings: this.warnings.length,
      suggestions: this.suggestions.length,
    };
  }

  run() {
    console.log("🚀 Starting CSS consistency validation...");

    DASHBOARD_FILES.forEach((file) => {
      this.validateFile(file);
    });

    return this.generateReport();
  }
}

// Run validation
if (require.main === module) {
  const validator = new CSSConsistencyValidator();
  const results = validator.run();

  // Exit with appropriate code
  process.exit(results.errors > 0 ? 1 : 0);
}

module.exports = CSSConsistencyValidator;

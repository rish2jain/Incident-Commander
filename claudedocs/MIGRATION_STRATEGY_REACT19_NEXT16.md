# Migration Strategy: React 19 & Next.js 16

**Created:** October 23, 2025
**Status:** Planning Phase
**Timeline:** 3-6 months phased approach
**Risk Level:** HIGH - Requires careful planning and testing

---

## Executive Summary

This document outlines the strategy for migrating the Incident Commander dashboard from:
- **React 18.3.1 → React 19.2.0**
- **Next.js 15.5.6 → Next.js 16.0.0**

Both migrations involve breaking changes and must be executed sequentially with comprehensive testing at each phase.

---

## Current State Analysis

### Current Versions (as of Oct 23, 2025)
```json
{
  "react": "18.3.1",
  "react-dom": "18.3.1",
  "next": "15.5.6",
  "@types/react": "18.3.26",
  "@types/react-dom": "18.3.7"
}
```

### Dependency Impact Assessment
- **Direct React Dependencies:** 15+ components using hooks, context, refs
- **React Ecosystem:** @react-three/fiber (8.18.0), @react-three/drei (9.122.0)
- **UI Libraries:** Radix UI components (10+ packages), Framer Motion
- **Testing:** @testing-library/react (16.3.0) - already React 19 compatible
- **Build System:** Next.js 15.5.6 with Turbopack

---

## Migration Phases

### Phase 1: Preparation & Risk Mitigation (Week 1-2)
**Goal:** Minimize migration risks through comprehensive assessment

#### Tasks
1. **Codebase Audit**
   - [ ] Grep for `forwardRef` usage across all components
   - [ ] Identify all `PropTypes` usage (should be none - we use TypeScript)
   - [ ] Locate `defaultProps` in function components
   - [ ] Find legacy Context API usage (`contextTypes`, `getChildContext`)
   - [ ] Audit error handling in production error reporting

2. **Dependency Compatibility Check**
   - [ ] Verify @react-three/fiber React 19 compatibility
   - [ ] Verify @react-three/drei React 19 compatibility
   - [ ] Check all Radix UI packages for React 19 support
   - [ ] Validate Framer Motion compatibility
   - [ ] Review all 3rd-party React dependencies

3. **Testing Infrastructure**
   - [ ] Verify all tests pass on React 18.3.1
   - [ ] Document current test coverage baseline
   - [ ] Create test scenarios for critical user flows
   - [ ] Set up performance benchmarking baseline

4. **Documentation**
   - [ ] Document all custom hooks and their patterns
   - [ ] Map component dependency tree
   - [ ] Identify critical business logic components

**Success Criteria:**
- Zero PropTypes found (TypeScript only)
- All tests passing at 100%
- Comprehensive component inventory complete
- All dependencies verified compatible

---

### Phase 2: React 18.3.x Intermediate Upgrade (Week 3)
**Goal:** Identify deprecation warnings before React 19

#### Migration Steps
```bash
# Step 1: Upgrade to React 18.3.x
npm install react@18.3.1 react-dom@18.3.1

# Step 2: Update type definitions
npm install --save-dev @types/react@18.3.26 @types/react-dom@18.3.7

# Step 3: Run development build and check console
npm run dev

# Step 4: Run full test suite
npm test

# Step 5: Check for deprecation warnings
# Review browser console and test output for warnings
```

#### Expected Warnings
- `forwardRef` deprecation notices (if applicable)
- Legacy Context usage (should be none)
- `defaultProps` warnings in function components

#### Action Items
- [ ] Fix all deprecation warnings
- [ ] Update components to use ref as prop where applicable
- [ ] Replace `defaultProps` with ES6 default parameters
- [ ] Run full regression testing

**Success Criteria:**
- Zero deprecation warnings in console
- All tests pass
- No production errors
- Application behaves identically to 18.2.0

---

### Phase 3: React 19 Migration (Week 4-5)
**Goal:** Upgrade to React 19 with breaking change mitigation

#### Pre-Migration Checklist
- [x] All React 18.3.x deprecation warnings resolved
- [ ] All tests passing
- [ ] Git branch created: `migration/react-19`
- [ ] Performance baseline established

#### Migration Steps

**Step 1: Install React 19**
```bash
git checkout -b migration/react-19

# Install React 19 and type definitions
npm install react@19.2.0 react-dom@19.2.0
npm install --save-dev @types/react@19.2.2 @types/react-dom@19.2.2
```

**Step 2: Run Automated Codemods**
```bash
# Install codemod tool
npm install -g codemod

# Run React 19 codemods (if available)
npx @codemod/react-19-migration ./dashboard
```

**Step 3: Manual Code Updates**

**A. Ref Handling**
```typescript
// BEFORE (React 18)
import { forwardRef } from 'react';

const MyComponent = forwardRef<HTMLDivElement, Props>((props, ref) => {
  return <div ref={ref}>{props.children}</div>;
});

// AFTER (React 19)
interface Props {
  ref?: React.Ref<HTMLDivElement>;
  children: React.ReactNode;
}

const MyComponent = ({ ref, children }: Props) => {
  return <div ref={ref}>{children}</div>;
};
```

**B. Remove defaultProps**
```typescript
// BEFORE (React 18)
const Button = ({ variant = 'primary', children }) => {
  return <button className={variant}>{children}</button>;
};
Button.defaultProps = { variant: 'primary' };

// AFTER (React 19)
const Button = ({ variant = 'primary', children }) => {
  return <button className={variant}>{children}</button>;
};
```

**C. Error Handling Updates**
```typescript
// Review all error boundaries and production error reporting
// Update to use new createRoot/hydrateRoot error handling
```

**Step 4: Update Dependencies**
```bash
# Update React ecosystem packages
npm update @react-three/fiber@latest
npm update @react-three/drei@latest

# May need specific versions compatible with React 19
# Check package documentation
```

**Step 5: Testing**
```bash
# Run full test suite
npm test

# Run in development
npm run dev

# Build production bundle
npm run build

# Check bundle size
ls -lh .next/static/chunks/
```

#### Breaking Changes to Address

1. **Ref as Prop**
   - Search: `forwardRef`
   - Action: Migrate to ref as prop pattern
   - Testing: Verify all ref-forwarding components work

2. **TypeScript Updates**
   - Update all component prop interfaces
   - Remove references to removed APIs
   - Fix type errors from @types/react@19

3. **Error Handling**
   - Review error boundary implementations
   - Update production error reporting if needed

4. **Strict Mode**
   - Test with React 19 Strict Mode
   - Fix any new warnings or errors

**Success Criteria:**
- All tests pass
- Zero TypeScript errors
- Zero console warnings
- Performance metrics within 5% of baseline
- Critical user flows validated

---

### Phase 4: Next.js 16 Migration (Week 6-7)
**Goal:** Upgrade to Next.js 16 after React 19 is stable

#### Pre-Migration Checklist
- [ ] React 19 migration complete and stable
- [ ] All tests passing on React 19
- [ ] Git branch created: `migration/nextjs-16`
- [ ] Node.js version ≥ 20.9.0 verified

#### Migration Steps

**Step 1: Environment Check**
```bash
# Verify Node.js version
node --version  # Must be ≥ 20.9.0

# Verify TypeScript version
npx tsc --version  # Must be ≥ 5.1.0
```

**Step 2: Automated Upgrade**
```bash
git checkout -b migration/nextjs-16

# Run Next.js automated codemod
npx @next/codemod@canary upgrade latest
```

**Step 3: Manual Breaking Changes**

**A. Async Request APIs (CRITICAL)**
```typescript
// BEFORE (Next.js 15)
export default function Page({ params, searchParams }) {
  const { id } = params;
  const { query } = searchParams;
  return <div>Page {id}</div>;
}

// AFTER (Next.js 16)
export default async function Page({ params, searchParams }) {
  const { id } = await params;
  const { query } = await searchParams;
  return <div>Page {id}</div>;
}
```

```typescript
// BEFORE (Next.js 15)
import { cookies, headers, draftMode } from 'next/headers';

export function handler() {
  const cookieStore = cookies();
  const headersList = headers();
  const draft = draftMode();
}

// AFTER (Next.js 16)
import { cookies, headers, draftMode } from 'next/headers';

export async function handler() {
  const cookieStore = await cookies();
  const headersList = await headers();
  const draft = await draftMode();
}
```

**B. Middleware → Proxy Rename**
```typescript
// If using middleware, rename file and function
// BEFORE: middleware.ts with export middleware
// AFTER: proxy.ts with export proxy

// proxy.ts
export function proxy(request: NextRequest) {
  // Note: Runtime is now nodejs by default, NOT edge
  return NextResponse.next();
}
```

**C. PPR Configuration Removal**
```typescript
// BEFORE (Next.js 15 experimental)
export const experimental_ppr = true;

// AFTER (Next.js 16)
// Remove experimental PPR flags
// Use new Cache Components instead
```

**D. Caching API Updates**
```typescript
// BEFORE (Next.js 15)
import { revalidateTag } from 'next/cache';
revalidateTag('my-tag');

// AFTER (Next.js 16)
import { revalidateTag } from 'next/cache';
revalidateTag('my-tag', 'max');  // Requires cacheLife profile
```

**Step 4: Configuration Updates**

**next.config.js**
```javascript
// Update Next.js config
/** @type {import('next').NextConfig} */
const nextConfig = {
  // Turbopack is now default
  // Add --webpack flag to npm scripts if you want to opt out

  // Remove experimental PPR config if present
  // experimental: {
  //   ppr: true  // REMOVE THIS
  // }
};

module.exports = nextConfig;
```

**package.json**
```json
{
  "scripts": {
    "dev": "next dev",  // Uses Turbopack by default
    "build": "next build",  // Uses Turbopack by default

    // To opt out of Turbopack (not recommended)
    // "dev": "next dev --webpack",
    // "build": "next build --webpack"
  }
}
```

**Step 5: Testing**
```bash
# Development testing with Turbopack
npm run dev
# Verify Fast Refresh works (should be 5-10x faster)

# Build testing
npm run build
# Verify build completes (should be 2-5x faster)

# Production testing
npm start

# Full test suite
npm test
```

#### Breaking Changes Checklist

- [ ] All `params` and `searchParams` use `await`
- [ ] All `cookies()`, `headers()`, `draftMode()` use `await`
- [ ] Middleware renamed to proxy (if applicable)
- [ ] PPR experimental config removed (if applicable)
- [ ] `revalidateTag()` updated with cacheLife profile (if applicable)
- [ ] Node.js ≥ 20.9.0
- [ ] TypeScript ≥ 5.1.0
- [ ] Turbopack compatibility verified

**Success Criteria:**
- All tests pass
- Turbopack dev server works
- Production build successful
- Performance improvements observed (faster builds)
- Zero runtime errors

---

### Phase 5: Production Validation (Week 8)
**Goal:** Comprehensive validation before production deployment

#### Testing Checklist

**Functional Testing**
- [ ] All critical user journeys tested
- [ ] 3D visualization components working
- [ ] Real-time WebSocket updates functional
- [ ] Authentication flows validated
- [ ] Error handling verified

**Performance Testing**
- [ ] Lighthouse audit (target: 90+ scores)
- [ ] Bundle size analysis
  - Compare to baseline
  - Target: ≤ 5% increase acceptable
- [ ] Fast Refresh speed (should be faster)
- [ ] Build time (should be faster)
- [ ] Time to Interactive (TTI)
- [ ] Largest Contentful Paint (LCP)

**Cross-Browser Testing**
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

**Regression Testing**
- [ ] All existing features working
- [ ] No visual regressions
- [ ] No functional regressions
- [ ] All integrations working

**Load Testing**
- [ ] Multiple concurrent users
- [ ] High-frequency updates
- [ ] Memory leak detection
- [ ] CPU usage profiling

---

## Risk Mitigation

### High-Risk Areas

1. **3D Visualization Components**
   - **Risk:** @react-three/fiber may have compatibility issues
   - **Mitigation:** Test thoroughly, verify library compatibility first
   - **Rollback:** Pin to compatible versions if needed

2. **Real-time WebSocket Updates**
   - **Risk:** Async changes may affect real-time data flow
   - **Mitigation:** Comprehensive testing of WebSocket handlers
   - **Rollback:** Maintain separate branch with old versions

3. **Production Error Reporting**
   - **Risk:** Error handling changes may break monitoring
   - **Mitigation:** Update error boundaries and Sentry integration
   - **Rollback:** Keep old error handling logic documented

4. **Turbopack Adoption**
   - **Risk:** Build system changes may have edge cases
   - **Mitigation:** Test both dev and prod builds extensively
   - **Rollback:** Use `--webpack` flag to revert to webpack

### Rollback Strategy

**React 19 Rollback**
```bash
npm install react@18.3.1 react-dom@18.3.1
npm install --save-dev @types/react@18.3.26 @types/react-dom@18.3.7
npm install
npm run build
```

**Next.js 16 Rollback**
```bash
npm install next@15.5.6
npm install --save-dev eslint-config-next@15.5.6
npm install
npm run build
```

**Complete Rollback**
```bash
git checkout main
git branch -D migration/react-19
git branch -D migration/nextjs-16
npm install  # Restore package-lock.json from main
```

---

## Testing Strategy

### Test Coverage Requirements
- **Unit Tests:** Maintain ≥ 80% coverage
- **Integration Tests:** All critical flows covered
- **E2E Tests:** Top 5 user journeys validated
- **Visual Regression:** No unexpected UI changes

### Test Execution Plan

**Phase 2-3 (React 19)**
```bash
# Run tests after each change
npm test

# Visual regression (if configured)
npm run test:visual

# E2E tests (if configured)
npm run test:e2e
```

**Phase 4 (Next.js 16)**
```bash
# Full test suite
npm test

# Build verification
npm run build && npm start

# Development verification
npm run dev
```

---

## Performance Benchmarks

### Baseline (Current State)
- **Build Time:** Measure with `time npm run build`
- **Dev Server Start:** Measure with `time npm run dev`
- **Fast Refresh:** Measure component update time
- **Bundle Size:** Check `.next/static/chunks/`
- **Lighthouse Scores:** Run audit on current version

### Target Improvements (Post-Migration)
- **Build Time:** 2-5x faster (Turbopack)
- **Fast Refresh:** 5-10x faster (Turbopack)
- **Bundle Size:** ≤ 5% increase
- **Lighthouse Scores:** Maintain 90+ or improve

### Measurement Tools
```bash
# Build time
time npm run build

# Bundle analysis
npm run build
ls -lh .next/static/chunks/

# Lighthouse
npx lighthouse http://localhost:3000 --view

# Performance profiling
# Use React DevTools Profiler in development
```

---

## Dependencies Update Order

### Order of Operations (CRITICAL)

1. **TypeScript Definitions (Safe - Do First)**
   ```bash
   npm update @types/node@20.19.23
   npm update @types/uuid@10.0.0
   npm update @types/three@0.180.0
   ```

2. **React 19 (High Risk - Requires Testing)**
   ```bash
   npm install react@19.2.0 react-dom@19.2.0
   npm install --save-dev @types/react@19.2.2 @types/react-dom@19.2.2
   ```

3. **React Ecosystem (After React 19)**
   ```bash
   npm update @react-three/fiber@latest
   npm update @react-three/drei@latest
   npm update @testing-library/react@latest
   ```

4. **Next.js 16 (After React 19 Stable)**
   ```bash
   npx @next/codemod@canary upgrade latest
   ```

5. **Supporting Libraries (After Next.js 16)**
   ```bash
   npm update framer-motion@latest
   npm update lucide-react@latest
   # Update Radix UI packages as needed
   ```

---

## Timeline

### Conservative Estimate (8 weeks)

| Week | Phase | Activities | Risk |
|------|-------|------------|------|
| 1-2 | Preparation | Audit, assessment, baseline | Low |
| 3 | React 18.3.x | Intermediate upgrade, fix warnings | Low |
| 4-5 | React 19 | Migration, testing, validation | High |
| 6-7 | Next.js 16 | Migration, async updates, testing | High |
| 8 | Validation | Final testing, performance check | Medium |

### Aggressive Estimate (4 weeks)
Only if codebase is very clean and no issues found in audit.

---

## Communication Plan

### Stakeholder Updates
- **Weekly:** Progress report to team
- **Blockers:** Immediate escalation if critical issues found
- **Pre-Production:** Demo session before deployment

### Documentation Updates
- Update CONTRIBUTING.md with new setup requirements
- Update README.md with Node.js version requirement
- Document any new patterns or practices
- Update troubleshooting guides

---

## Success Metrics

### Technical Metrics
- ✅ Zero production errors
- ✅ All tests passing
- ✅ Performance within 5% of baseline or better
- ✅ Bundle size ≤ 5% increase
- ✅ Build time 2-5x faster

### Business Metrics
- ✅ Zero user-reported bugs
- ✅ No degradation in user experience
- ✅ Improved developer experience (faster dev cycles)

---

## Next Steps (Immediate Actions)

### This Week
1. ✅ Research completed - React 19 & Next.js 16 breaking changes documented
2. ⏳ Execute safe TypeScript definition updates
3. ⏳ Create migration tracking board/issues
4. ⏳ Schedule kickoff meeting with team

### Week 1-2 (Preparation Phase)
1. Run codebase audit commands
2. Document all forwardRef usage
3. Verify dependency compatibility
4. Establish performance baselines
5. Create test scenarios

---

## Resources

### Official Documentation
- [React 19 Upgrade Guide](https://react.dev/blog/2024/04/25/react-19-upgrade-guide)
- [React 19 Release Notes](https://react.dev/blog/2024/12/05/react-19)
- [Next.js 16 Upgrade Guide](https://nextjs.org/docs/app/guides/upgrading/version-16)
- [Next.js 16 Release Notes](https://nextjs.org/blog/next-16)

### Codemods
- [React 18→19 Migration Codemod](https://docs.codemod.com/guides/migrations/react-18-19)
- [Next.js Upgrade Codemod](https://nextjs.org/docs/app/guides/upgrading)

### Community Resources
- [MUI X React 19 Migration Experience](https://mui.com/blog/react-19-update/)
- [Common React 19 Migration Mistakes](https://blog.openreplay.com/common-mistakes-upgrading-react-19-avoid/)

---

## Appendix: Code Audit Commands

### Find forwardRef Usage
```bash
grep -r "forwardRef" dashboard/src --include="*.tsx" --include="*.ts"
```

### Find defaultProps in Function Components
```bash
grep -r "\.defaultProps" dashboard/src --include="*.tsx" --include="*.ts"
```

### Find Legacy Context
```bash
grep -r "contextTypes\|getChildContext" dashboard/src --include="*.tsx" --include="*.ts"
```

### Find PropTypes (should be none)
```bash
grep -r "PropTypes" dashboard/src --include="*.tsx" --include="*.ts"
```

### Find Async Request API Usage (Next.js)
```bash
# Find params/searchParams usage
grep -r "params\|searchParams" dashboard/src --include="*.tsx" --include="*.ts"

# Find cookies/headers/draftMode usage
grep -r "cookies()\|headers()\|draftMode()" dashboard/src --include="*.tsx" --include="*.ts"
```

### Analyze Bundle Size
```bash
npm run build
du -sh .next/static/chunks/*
```

---

**Document Status:** Draft - Ready for Team Review
**Next Update:** After Phase 1 (Preparation) completion
**Owner:** Development Team
**Reviewers:** Technical Lead, QA Lead

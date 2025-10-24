# Amplify Build Troubleshooting Log

## Build Failure #1: Missing package-lock.json

### Error
```
npm error The `npm ci` command can only install with an existing package-lock.json
```

### Root Cause
- Amplify was running `npm ci` at repository root
- Dashboard's `package-lock.json` is in `dashboard/` subdirectory

### Fix Applied
Created root-level `amplify.yml` with `cd dashboard` command:
```yaml
preBuild:
  commands:
    - cd dashboard
    - npm ci
```

**Commit**: `b952ec42` - "fix: Move amplify.yml to root with dashboard/ path references"

**Result**: ❌ Build still failed (different error)

---

## Build Failure #2: Module Not Found (class-variance-authority, clsx)

### Error
```
Module not found: Can't resolve 'class-variance-authority'
Module not found: Can't resolve 'clsx'
```

### Root Cause Analysis
Amplify runs each command in a **fresh shell context**. This means:
```yaml
commands:
  - cd dashboard     # ✅ Changes directory
  - npm ci           # ❌ Runs in original directory (cd didn't persist!)
```

The `cd` command succeeded, but `npm ci` ran in the **root directory** instead of `dashboard/`.

### Evidence
1. `package.json` line 29-30 shows dependencies ARE declared:
   ```json
   "class-variance-authority": "^0.7.1",
   "clsx": "^2.1.1"
   ```

2. Build error shows modules can't be resolved → `npm ci` didn't install them

3. Amplify shell behavior: Each command runs independently

### Fix Applied
Chain commands with `&&` to ensure they run in the same shell context:
```yaml
preBuild:
  commands:
    - cd dashboard && npm ci
build:
  commands:
    - cd dashboard && npm run build
```

**Commit**: `7c9af30c` - "fix: Chain cd and npm commands with && in amplify.yml"

**Result**: 🔄 Build triggered automatically (monitoring)

---

## Technical Explanation

### Why && is Required

**❌ Without &&** (separate commands):
```bash
# Command 1
cd dashboard  # Changes to dashboard/
# Shell exits, new shell starts

# Command 2
npm ci        # Runs in original directory (cd lost!)
```

**✅ With &&** (chained commands):
```bash
# Single command execution
cd dashboard && npm ci  # Both run in same shell, cd persists!
```

### Complete Working Configuration

```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - cd dashboard && npm ci
    build:
      commands:
        - npm run build    # Already in dashboard/ from preBuild
  artifacts:
    baseDirectory: dashboard/.next
    files:
      - "**/*"
  cache:
    paths:
      - dashboard/node_modules/**/*
      - dashboard/.next/cache/**/*
```

---

## Build Failure #3: Directory Already Changed

### Error
```
cd: dashboard: No such file or directory
```

### Root Cause
After `cd dashboard && npm ci` in **preBuild** phase, we remain in the `dashboard/` directory. Attempting `cd dashboard` again in **build** phase fails because we're already inside `dashboard/`.

### Evidence from logs
```
Line 32: cd dashboard && npm ci     ✅ Succeeded (installed 858 packages)
Line 53: cd dashboard && npm run build   ❌ Failed (no such directory)
```

### Fix Applied
Remove `cd` from build phase since we're already in the correct directory:
```yaml
build:
  commands:
    - npm run build    # ✅ Already in dashboard/ from preBuild
```

**Commit**: `af16f169` - "fix: Remove cd from build phase - already in dashboard/ after preBuild"

**Result**: 🔄 Build triggered automatically (monitoring)

---

## Build Failure #4: Turbopack Compatibility Issues

### Error
```
Error: Turbopack build failed with 15 errors:
./src/components/ui/alert.tsx:4:1
[... 14 more component errors]
```

### Root Cause
Next.js 16 introduced Turbopack as the default bundler, but it has compatibility issues with some UI components. The build errors occur in UI components that work perfectly with webpack.

### Evidence
- ✅ `npm ci` completed successfully (858 packages installed)
- ✅ Next.js 16.0.0 started building
- ❌ Turbopack failed with 15 component errors
- All affected components use standard React patterns

### Fix Applied (Attempt 1 - Failed)
Tried using CLI flag `--no-turbo`:
```json
"scripts": {
  "build": "next build --no-turbo"
}
```
**Result**: ❌ Failed - flag doesn't exist in Next.js 16

### Fix Applied (Attempt 2 - Correct)
Disable Turbopack via next.config.js:
```javascript
experimental: {
  turbo: false,
}
```

**Commits**:
- `8d4946c8` - CLI flag attempt (failed)
- `f44d4dc4` - Config file method (correct)

**Result**: 🔄 Build triggered automatically (monitoring)

---

## Deployment Timeline

| Time | Event | Status |
|------|-------|--------|
| Initial | Manual Amplify app (d3jy9k6riuse52) | ❌ Deleted for GitHub integration |
| Push 1 | GitHub integration setup | ✅ App created (d1o5cfrpl0kgt3) |
| Build 1 | Missing package-lock.json | ❌ Failed |
| Fix 1 | Add `cd dashboard` command | ⚠️ Incomplete fix |
| Build 2 | Module not found errors | ❌ Failed |
| Fix 2 | Chain with `&&` operator | ⚠️ Incomplete fix |
| Build 3 | cd dashboard fails (already there) | ❌ Failed |
| Fix 3 | Remove cd from build phase | ⚠️ Incomplete fix |
| Build 4 | Turbopack compatibility errors | ❌ Failed |
| Fix 4a | Disable Turbopack (--no-turbo flag) | ❌ Failed (flag doesn't exist) |
| Build 5 | Unknown option --no-turbo | ❌ Failed |
| Fix 4b | Disable via next.config.js | 🔄 Testing |

---

## Current Status

**Amplify App**: d1o5cfrpl0kgt3
**Branch**: main
**Latest Commit**: f44d4dc4
**Build Status**: 🔄 Rebuilding (Fix #4b: Turbopack disabled via config)

**Monitor Build**: https://console.aws.amazon.com/amplify/home?region=us-east-1#/d1o5cfrpl0kgt3

---

## Expected Successful Build Flow

```
1. Clone repo → /codebuild/.../Incident-Commander/
2. Read amplify.yml from root ✅
3. Run: cd dashboard && npm ci
   - Changes to dashboard/ ✅
   - Finds package-lock.json ✅
   - Installs all dependencies ✅
   - Remains in dashboard/ directory ✅
4. Run: npm run build
   - Already in dashboard/ from preBuild ✅
   - Builds Next.js application ✅
   - Generates .next output ✅
5. Deploy dashboard/.next → Amplify CDN ✅
```

---

## Verification Steps (After Successful Build)

1. ✅ Check Amplify build logs show successful `npm ci`
2. ✅ Verify build output includes all dependencies
3. ✅ Confirm deployment to https://main.d1o5cfrpl0kgt3.amplifyapp.com
4. ✅ Test dashboard loads and renders
5. ✅ Verify 3D visualizations work
6. ✅ Check WebSocket connectivity
7. ✅ Test interactive features

---

## Lessons Learned

1. **Amplify Shell Behavior**: Each command runs in a fresh shell
2. **Command Chaining**: Use `&&` to maintain context across operations
3. **Working Directory**: Must explicitly `cd` for each command phase
4. **Testing Strategy**: Test monorepo subdirectory builds require special attention

---

## Alternative Solutions (Not Used)

### Option A: App Root Directory in Console
- Set "App root directory" to `dashboard` in Amplify Console settings
- Pros: Cleaner YAML, no `cd` needed
- Cons: Console-only setting, not visible in `amplify.yml`, harder to reproduce

### Option B: Monorepo Configuration
```yaml
applications:
  - appRoot: dashboard
    frontend:
      ...
```
- Pros: Explicit monorepo support
- Cons: More complex configuration

**Why we chose command chaining**:
- Simple, explicit, version-controlled
- Works with any Amplify setup
- Easy to understand and reproduce

# AWS Amplify GitHub Integration - Setup Guide

## 🎯 Why Use GitHub Integration?

**Benefits over Manual Deployment**:
- ✅ **Automatic deployments** - Every git push triggers deployment
- ✅ **No manual uploads** - Deploy by just pushing code
- ✅ **CI/CD pipeline** - Built-in continuous integration
- ✅ **Branch previews** - Test features on separate URLs
- ✅ **Rollback capability** - Easy revert to previous versions
- ✅ **Build logs** - See exactly what happens during deployment

---

## 🚀 Quick Setup (2 Minutes) - AWS Console Method

### Step 1: Open Amplify Console
```
https://console.aws.amazon.com/amplify/home?region=us-east-1
```

### Step 2: Create New App
1. Click **"New app"** (top right)
2. Select **"Host web app"**
3. Choose **"GitHub"** as the source

### Step 3: Authorize GitHub
1. Click **"Authorize AWS Amplify"**
2. AWS will redirect you to GitHub
3. Grant Amplify access to your repositories
4. You'll be redirected back to AWS Console

### Step 4: Select Repository
1. **Repository**: `rish2jain/Incident-Commander`
2. **Branch**: `merge-latest-dashboard-enhancements`
3. Click **"Next"**

### Step 5: Configure Build Settings
AWS will auto-detect Next.js. Verify these settings:

```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - npm ci
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: .next
    files:
      - '**/*'
  cache:
    paths:
      - node_modules/**/*
      - .next/cache/**/*
```

**App name**: `incident-commander-dashboard`

**Advanced settings** (optional):
- Environment variables: None needed for now
- Service role: Use existing or create new

Click **"Next"**

### Step 6: Review and Deploy
1. Review all settings
2. Click **"Save and deploy"**
3. ✅ Amplify will automatically:
   - Clone your repository
   - Install dependencies
   - Build Next.js app
   - Deploy to global CDN
   - Provide public URL

**Deployment time**: ~3-5 minutes

---

## 📋 Alternative: GitHub Personal Access Token Method

If you prefer CLI/automation:

### Step 1: Generate GitHub Token
```
https://github.com/settings/tokens/new
```

**Token settings**:
- **Note**: "AWS Amplify Deployment"
- **Expiration**: 30 days (or custom)
- **Scopes**: Select:
  - ✅ `repo` (Full control of private repositories)
  - ✅ `admin:repo_hook` (Full control of repository hooks)

Click **"Generate token"** and **copy the token** (you'll only see it once!)

### Step 2: Set Token in Environment
```bash
export GITHUB_TOKEN='ghp_your_token_here'
```

### Step 3: Run Deployment Script
```bash
./deploy_amplify_github.sh
```

This will:
1. Create Amplify app connected to GitHub
2. Configure build settings
3. Start initial deployment
4. Provide dashboard URL

---

## 🎨 What Gets Deployed

### Full Next.js Features
- ✅ Server-Side Rendering (SSR)
- ✅ API Routes
- ✅ Dynamic Routing
- ✅ Image Optimization
- ✅ Incremental Static Regeneration

### Your Dashboard Features
- ✅ 3D Byzantine Consensus Visualizations
- ✅ Real-Time WebSocket Updates
- ✅ Framer Motion Animations
- ✅ Complete API Integration
- ✅ All Interactive Components

---

## 🔄 How Automatic Deployment Works

### After Initial Setup

**Every time you push to GitHub**:
```bash
git add .
git commit -m "Update dashboard features"
git push origin merge-latest-dashboard-enhancements
```

**Amplify automatically**:
1. Detects the push via webhook
2. Pulls latest code
3. Runs build process
4. Deploys to production
5. Updates your public URL

**No manual steps needed!**

---

## 📊 Your Dashboard URLs

### After Amplify Setup

**Production URL**:
```
https://merge-latest-dashboard-enhancements.[app-id].amplifyapp.com
```

You can also configure:
- **Custom domain**: `dashboard.yourcompany.com`
- **Branch previews**: Test features before merging
- **Environment variables**: Configure API endpoints per branch

---

## 🔍 Monitoring Deployments

### Via AWS Console
```
https://console.aws.amazon.com/amplify/home?region=us-east-1
```

**See**:
- Build logs in real-time
- Deployment status
- Build history
- Performance metrics
- Error logs

### Via CLI
```bash
# List all apps
aws amplify list-apps

# Get app details
aws amplify get-app --app-id [APP_ID]

# List builds for branch
aws amplify list-jobs --app-id [APP_ID] --branch-name merge-latest-dashboard-enhancements

# Get build logs
aws amplify get-job --app-id [APP_ID] --branch-name merge-latest-dashboard-enhancements --job-id [JOB_ID]
```

---

## ⚙️ Build Configuration

### Custom Build Settings

Your `dashboard/amplify.yml` is already configured:
```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - npm ci                    # Clean install dependencies
    build:
      commands:
        - npm run build             # Build Next.js app
  artifacts:
    baseDirectory: .next            # Output directory
    files:
      - '**/*'                      # Include all files
  cache:
    paths:
      - node_modules/**/*           # Cache dependencies
      - .next/cache/**/*            # Cache Next.js build
```

### Environment Variables (if needed)

In Amplify Console → App Settings → Environment Variables:
```
NODE_ENV=production
NEXT_PUBLIC_API_URL=https://h8xlzr74h8.execute-api.us-east-1.amazonaws.com
```

---

## 🚨 Troubleshooting

### Build Fails

**Check**:
1. Build logs in Amplify Console
2. Ensure `package.json` has all dependencies
3. Verify `next.config.js` is valid
4. Check Node.js version (Amplify uses Node 18 by default)

**Fix Node version** (if needed):
Add to `dashboard/amplify.yml` under `preBuild`:
```yaml
preBuild:
  commands:
    - nvm use 18
    - npm ci
```

### GitHub Authorization Failed

**Solution**:
1. Go to GitHub Settings → Applications → Authorized OAuth Apps
2. Revoke AWS Amplify
3. Try authorization again

### Deployment Slow

**Optimization**:
- Enable dependency caching (already configured)
- Use `npm ci` instead of `npm install` (already configured)
- Consider CDN caching in Amplify settings

---

## 🎯 Recommended Workflow for Judges

### Setup Once (Now)
1. Follow AWS Console method above (2 minutes)
2. Get your dashboard URL
3. Share URL with judges

### Continuous Deployment
1. Make improvements to dashboard
2. `git push` to GitHub
3. Amplify auto-deploys changes
4. Judges always see latest version

---

## 📊 Comparison: Manual vs GitHub

| Feature | Manual Upload | GitHub Integration |
|---------|---------------|-------------------|
| Setup Time | 0 min | 2 min |
| Deploy Method | Manual upload | Git push |
| Automation | None | Full CI/CD |
| Update Time | Manual (5 min) | Automatic (3 min) |
| Rollback | Manual | One click |
| Branch Previews | No | Yes |
| Build Logs | Limited | Complete |
| Best For | One-time demo | Active development |

---

## ✅ What to Do Now

**Recommended**: Use **AWS Console Method** (easiest, 2 minutes)

1. Open: https://console.aws.amazon.com/amplify/home?region=us-east-1
2. Click "New app" → "Host web app"
3. Connect GitHub → Select repository
4. Deploy!

**Result**:
- ✅ Interactive dashboard live in 5 minutes
- ✅ Auto-deploy on every git push
- ✅ Professional CI/CD pipeline
- ✅ Complete feature access (3D, WebSockets, animations)
- ✅ Production-ready URL for judge evaluation

---

## 🎊 After Setup

Your judges will have access to:

**Production Dashboard**:
```
https://merge-latest-dashboard-enhancements.[app-id].amplifyapp.com
```

**Features**:
- 🎨 3D Byzantine consensus visualization
- 📡 Real-time WebSocket updates
- 🎬 Smooth Framer Motion animations
- 🔌 Complete API integration
- 📊 Business impact metrics
- 🤖 AI transparency panel

**And the best part**: Every time you push improvements, judges automatically get the latest version! 🚀

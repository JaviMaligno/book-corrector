# Frontend Deployment Guide - Render

Guide for deploying the React frontend to Render alongside the backend API.

## Overview

The frontend is configured as a **static site** on Render, deployed from the same repository as the backend. Both services auto-deploy from the `alternative-free-hosting` branch.

## Architecture

- **Backend**: [corrector-api](render.yaml#L7) - FastAPI Docker service
- **Frontend**: [corrector-web](render.yaml#L51) - React static site (Vite build)
- **Database**: PostgreSQL (free tier, 90 days)
- **Branch**: `alternative-free-hosting` (will be merged to `main` later)

## Prerequisites

- [x] Backend already deployed on Render
- [x] `render.yaml` updated with frontend service configuration
- [x] CORS configured in `server/main.py` to allow frontend domain
- [x] Changes committed to `alternative-free-hosting` branch

## Deployment Steps

### 1. Push Changes to GitHub

```bash
# Ensure you're on the correct branch
git checkout alternative-free-hosting

# Commit the updated configuration
git add render.yaml server/main.py
git commit -m "Add frontend static site deployment to Render"

# Push to GitHub
git push origin alternative-free-hosting
```

### 2. Render Auto-Deploys

Once you push, Render will detect the updated `render.yaml` and:

1. **Update backend service** (corrector-api)
   - Rebuilds with new CORS configuration
   - Takes ~5-10 minutes
   - Watch progress in Render dashboard

2. **Create frontend service** (corrector-web)
   - First-time setup and build
   - Takes ~3-5 minutes
   - Builds React app with Vite

### 3. Find Your Frontend URL

After deployment completes:

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click on **corrector-web** service
3. Find the URL at the top:
   ```
   https://corrector-web-xxx.onrender.com
   ```
4. Copy this URL - you'll need it for testing

### 4. Verify Deployment

Test the following:

#### a) Frontend Loads
```bash
# Visit your frontend URL
open https://corrector-web-xxx.onrender.com

# Should show login page
```

#### b) API Connection Works
```bash
# Check browser console (F12) for any CORS errors
# Try logging in with demo credentials
# Should successfully connect to backend
```

#### c) Full Workflow
1. Login with demo account
2. Create a project
3. Upload a document
4. Run correction
5. Download results

All should work without CORS errors.

## Configuration Details

### Environment Variables

The frontend gets its API URL automatically from the backend service:

```yaml
# In render.yaml (lines 69-74)
envVars:
  - key: VITE_API_URL
    fromService:
      type: web
      name: corrector-api
      envVarKey: RENDER_EXTERNAL_URL
```

This means:
- Frontend knows backend URL at build time
- No manual configuration needed
- Auto-updates if backend URL changes (requires rebuild)

### SPA Routing

All routes are rewritten to serve `index.html` for client-side routing:

```yaml
# In render.yaml (lines 62-66)
routes:
  - type: rewrite
    source: /*
    destination: /index.html
```

This allows React Router to handle routes like:
- `/login`
- `/projects`
- `/projects/123`
- `/runs/456`

### CORS Configuration

Backend allows requests from frontend domain via regex pattern:

```python
# In server/main.py (line 69)
allow_origin_regex=r"https://corrector-web.*\.onrender\.com"
```

This matches:
- `https://corrector-web.onrender.com` (custom domain)
- `https://corrector-web-abc123.onrender.com` (auto-generated URL)

## Troubleshooting

### Problem: CORS Error in Browser Console

**Symptoms:**
```
Access to XMLHttpRequest at 'https://corrector-api-xxx.onrender.com/...'
from origin 'https://corrector-web-xxx.onrender.com' has been blocked by CORS policy
```

**Solution:**
1. Check backend logs in Render dashboard (corrector-api → Logs)
2. Verify CORS regex pattern includes your frontend URL
3. Backend should log: "Allowed CORS origins: ..."
4. If missing, manually trigger backend redeploy

### Problem: 404 on Page Refresh

**Symptoms:**
- App works when navigating via links
- Direct URL access or refresh shows 404

**Solution:**
- This means SPA routing isn't configured
- Check `render.yaml` has the `routes` section (lines 62-66)
- Redeploy frontend if missing

### Problem: API Calls Go to Wrong URL

**Symptoms:**
- Frontend tries to call `http://localhost:8001` instead of production backend
- Network tab shows failed requests

**Solution:**
1. Check environment variable was set correctly:
   ```bash
   # In Render dashboard → corrector-web → Environment
   # Should show: VITE_API_URL = https://corrector-api-xxx.onrender.com
   ```
2. If missing or wrong, update and redeploy:
   - Edit environment variable in dashboard
   - Click **Manual Deploy** → **Clear build cache & deploy**

### Problem: Build Fails with "npm not found"

**Symptoms:**
```
/bin/sh: npm: not found
```

**Solution:**
- Render might be using wrong build environment
- Check `render.yaml` has `env: static` (line 53)
- Try changing `npm ci` to `npm install` in build command

### Problem: Build Fails with "ENOENT: no such file"

**Symptoms:**
```
Error: ENOENT: no such file or directory, open 'dist/index.html'
```

**Solution:**
1. Build command should be: `cd web && npm ci && npm run build`
2. Publish path should be: `./web/dist` (note the `./` prefix)
3. Check both in `render.yaml` (lines 59-60)

### Problem: Static Assets 404 (CSS/JS not loading)

**Symptoms:**
- Page loads but is unstyled
- Console shows 404 for `/assets/index-xxx.js`

**Solution:**
1. Check Vite base path in `vite.config.ts`
2. Should be `/` (default) not a subdirectory
3. Verify `staticPublishPath: ./web/dist` is correct
4. Check build output locally: `cd web && npm run build && ls -la dist/`

### Problem: Environment Variable Not Updating

**Symptoms:**
- Changed `VITE_API_URL` but frontend still uses old value

**Root Cause:**
- Vite bakes env vars into the JavaScript bundle at build time
- Changing env var doesn't update the code until rebuild

**Solution:**
1. After changing any `VITE_*` variable, trigger rebuild:
   - Render dashboard → corrector-web
   - **Manual Deploy** → **Clear build cache & deploy**
2. Or push a dummy commit to trigger auto-deploy

## Free Tier Limitations

### Static Sites (Frontend)
- ✅ **No sleep** (always available)
- ✅ **100 GB bandwidth/month**
- ✅ **Global CDN**
- ✅ **Automatic HTTPS**
- ⚠️ **No custom domain on free tier** (use Render subdomain)

### Web Services (Backend)
- ⚠️ **Sleep after 15 min inactivity** (50s wake-up time)
- ✅ **750 hours/month** (31+ days if always running)
- ✅ **512 MB RAM**

**Solution for sleep**: Use a keep-alive service (see [main deployment guide](RENDER_DEPLOYMENT.md#paso-5-configurar-keep-alive-anti-sleep))

## Upgrading to Paid Tier

If you need:
- No sleep for backend → **Starter plan** ($7/month)
- Custom domain → **Included in Starter**
- More bandwidth → **Higher tiers**

Upgrade in Render dashboard → Service → Settings → Plan

## Changing Branch to Main (Future)

When you merge `alternative-free-hosting` → `main`:

### Option A: Update in Dashboard
1. Render dashboard → Service → Settings
2. Change **Branch** from `alternative-free-hosting` to `main`
3. Click **Save** (triggers redeploy)
4. Repeat for both services (frontend + backend)

### Option B: Update render.yaml
1. Edit `render.yaml`:
   ```yaml
   # Change both services
   branch: main
   ```
2. Commit and push to `main`
3. Render auto-updates

## Monitoring

### View Logs
- Render dashboard → corrector-web → **Logs**
- Filter by time range
- Search for errors

### View Metrics
- Render dashboard → corrector-web → **Metrics**
- Bandwidth usage
- Request count
- Response time

### Check Build History
- Render dashboard → corrector-web → **Events**
- See all deployments
- Inspect failed builds

## Custom Domain (Optional)

To use your own domain (e.g., `app.mydomain.com`):

1. Render dashboard → corrector-web → Settings → **Custom Domain**
2. Add domain: `app.mydomain.com`
3. Add DNS record at your domain provider:
   ```
   Type: CNAME
   Name: app
   Value: corrector-web.onrender.com
   ```
4. Wait for DNS propagation (5-30 min)
5. Render auto-provisions SSL certificate

**Note**: Custom domains require paid plan ($7/month Starter minimum)

## Related Documentation

- [Backend Deployment Guide](RENDER_DEPLOYMENT.md) - Full Render setup
- [Render Docs - Static Sites](https://render.com/docs/static-sites)
- [Render Docs - Blueprint Spec](https://render.com/docs/blueprint-spec)

## Summary

After deployment:
- ✅ Frontend: `https://corrector-web-xxx.onrender.com`
- ✅ Backend: `https://corrector-api-xxx.onrender.com`
- ✅ Auto-deploy from `alternative-free-hosting` branch
- ✅ CORS configured (frontend ↔ backend)
- ✅ Static site (no sleep, fast CDN)
- ✅ Ready to merge to `main` when needed

**Next Steps**: Test the full workflow and verify all features work in production!

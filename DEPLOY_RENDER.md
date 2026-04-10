# Deploy to Render (Free Tier)

## Overview
Deploy Code Archaeologist to Render's free web service tier.

**Free Tier Limits:**
- 512MB RAM
- Shared CPU
- Sleeps after 15 min idle (wakes in ~30s on next request)
- Good for MVP/testing

## Step 1: Push to GitHub

1. Create GitHub repo (e.g., `code-archaeologist`)
2. Push your code:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/code-archaeologist.git
git push -u origin main
```

## Step 2: Sign Up on Render

1. Go to https://render.com
2. Sign up with GitHub
3. Click "New Web Service"
4. Select your GitHub repo

## Step 3: Configure Service

**Settings:**
- **Name:** `code-archaeologist-api`
- **Runtime:** Docker
- **Dockerfile Path:** `./Dockerfile`
- **Plan:** Free

**Environment Variables:**
```
SUPABASE_URL=https://xztxgwxvwgdmskhgqtdt.supabase.co
SUPABASE_KEY=sb_publishable_H4G7DfuwWnOQG1j3pMo-AA_miIHLB12
SUPABASE_SERVICE_KEY=xztxgwxvwgdmskhgqtdt
JWT_SECRET=your-production-secret-key
API_HOST=0.0.0.0
API_PORT=8000
```

**Health Check Path:** `/health`

Click **Create Web Service**

## Step 4: Wait for Deploy

- Build takes ~5-10 minutes
- Watch logs in Render dashboard
- Status shows "Live" when ready

## Step 5: Test

Your API will be at:
```
https://code-archaeologist-api.onrender.com
```

Test endpoints:
```bash
curl https://code-archaeologist-api.onrender.com/
curl https://code-archaeologist-api.onrender.com/health
curl https://code-archaeologist-api.onrender.com/docs
```

## Step 6: Update Streamlit

Edit `frontend/streamlit/app.py`:
```python
API_URL = "https://code-archaeologist-api.onrender.com"  # Replace localhost
```

## Troubleshooting

### Build fails
- Check Render logs
- Verify Dockerfile works locally: `docker build -t test .`

### Out of memory (512MB limit)
- Remove heavy dependencies
- Use smaller base image
- Upgrade to paid plan ($7/month)

### Slow cold start (30s delay)
- Normal for free tier
- Use uptime monitor to keep alive
- Upgrade to paid for always-on

## Next: Custom Domain (Optional)

1. In Render dashboard → Settings → Custom Domains
2. Add your domain (e.g., `api.codearchaeologist.com`)
3. Add CNAME record in DNS
4. Wait for SSL certificate (auto-provisioned)

## Files Created

- `Dockerfile` - Container definition
- `render.yaml` - Blueprint for Render (optional)
- `DEPLOY_RENDER.md` - This guide

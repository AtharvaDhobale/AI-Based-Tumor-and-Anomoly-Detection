# Vercel Deployment Guide

## Quick Start

### 1. Push to GitHub
```bash
git add .
git commit -m "Prepare for Vercel deployment"
git push origin main
```

### 2. Create PostgreSQL Database
Use one of these free options:
- **Railway**: https://railway.app
- **Render**: https://render.com
- **Supabase**: https://supabase.com
- **Heroku PostgreSQL** (soon to be paid)

Get your DATABASE_URL connection string.

### 3. Deploy on Vercel
1. Go to https://vercel.com
2. Click "Add New" → "Project"
3. Select your GitHub repository
4. Configure:
   - **Framework**: Other (monorepo)
   - **Root Directory**: ./
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Output Directory**: `frontend/dist`

### 4. Set Environment Variables in Vercel
In Vercel Dashboard → Settings → Environment Variables, add:

```
ENVIRONMENT=production
DATABASE_URL=postgresql://user:password@host:port/database
CORS_ORIGINS=https://your-project.vercel.app
JWT_SECRET=your-secret-key-here-min-32-chars
STORAGE_DIR=/tmp/storage
REPORTS_DIR=/tmp/storage/reports
LLM_API_KEY=your-openai-key-if-needed
```

### 5. Update Frontend Environment
In `frontend/.env.production`, update:
```
VITE_API_URL=https://your-project-name.vercel.app/api
```

### 6. Deploy
Click "Deploy" and wait for completion.

## Important Notes

- ⚠️ **SQLite won't work** on Vercel (no persistent filesystem). Use PostgreSQL.
- ⚠️ **File uploads** are temporary. Save to `/tmp` or external storage (S3).
- ⚠️ **ML model files** must be under 50MB. Move large models to external storage if needed.
- ⚠️ **Timeout**: Max 60s on Pro, 10s on Free tier. Async tasks may be needed.
- ⚠️ **Cold starts**: First request takes 10-30s (serverless limitation).

## Troubleshooting

### Build fails: "No such file or directory"
- Ensure `api/index.py` exists
- Check all import paths are correct

### "Database connection refused"
- Verify DATABASE_URL in environment variables
- Test connection string locally first

### Frontend can't reach backend
- Verify VITE_API_URL matches deployment URL
- Check CORS_ORIGINS in environment variables
- Ensure backend is healthy: `https://your-project.vercel.app/api/health`

### Large ML model timeout
- Reduce model size or use model quantization
- Consider lazy-loading models
- Use external storage for model files

## Optional: Custom Domain
In Vercel Dashboard:
1. Go to Settings → Domains
2. Add your custom domain
3. Update DNS records at your domain provider

# Vercel Deployment Checklist

## ✅ Files Created/Updated

- [x] `package.json` - Root package.json with build scripts
- [x] `vercel.json` - Vercel configuration
- [x] `api/index.py` - Serverless function entry point
- [x] `.env.example` - Environment variables template
- [x] `frontend/.env.production` - Frontend production config
- [x] `backend/app/core/config.py` - Updated to use environment variables
- [x] `backend/app/db/session.py` - Updated for PostgreSQL + NullPool
- [x] `runtime.txt` - Python 3.11 specification
- [x] `VERCEL_DEPLOYMENT.md` - Deployment guide

## 📋 Pre-Deployment Steps

### Step 1: Prepare Git Repository
```bash
# Make sure you're in the project root
cd c:\Users\athar\Downloads\AI-Based-Tumor-and-Anomoly-Detection-main\AI-Based-Tumor-and-Anomoly-Detection-main

# Initialize git if not done
git init

# Add all files
git add .

# Commit
git commit -m "Prepare for Vercel deployment"

# Push to GitHub (create repo first at github.com)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

### Step 2: Create PostgreSQL Database
Choose one (free tier available):

**Option A: Railway** (⭐ Recommended)
1. Go to https://railway.app
2. Sign up with GitHub
3. Create new project → Database → PostgreSQL
4. Copy DATABASE_URL

**Option B: Render**
1. Go to https://render.com
2. Sign up
3. Create new PostgreSQL database
4. Copy connection string

**Option C: Supabase**
1. Go to https://supabase.com
2. Create new project
3. Get connection string from settings

### Step 3: Prepare Environment Variables
You'll need these values:
- `DATABASE_URL` - from PostgreSQL setup above
- `JWT_SECRET` - generate: `openssl rand -hex 32`
- `CORS_ORIGINS` - leave as `https://your-project.vercel.app`
- `ENVIRONMENT` - set to `production`

### Step 4: Deploy to Vercel

1. **Go to Vercel**: https://vercel.com
2. **Sign in** with GitHub
3. **Import Project**:
   - Click "Add New" → "Project"
   - Select your GitHub repository
4. **Configure Build Settings**:
   - Root Directory: `./`
   - Build Command: `cd frontend && npm install && npm run build`
   - Output Directory: `frontend/dist`
   - Framework: `Other`
5. **Set Environment Variables**:
   - Click "Environment Variables"
   - Add each variable:
     ```
     ENVIRONMENT = production
     DATABASE_URL = postgresql://...
     CORS_ORIGINS = https://your-project.vercel.app
     JWT_SECRET = (your generated secret)
     STORAGE_DIR = /tmp/storage
     REPORTS_DIR = /tmp/storage/reports
     ```
6. **Deploy** - Click "Deploy" and wait ~5-10 minutes

## 🔍 Post-Deployment Verification

### Test Backend Health
```bash
# Replace with your Vercel URL
curl https://your-project-name.vercel.app/api/health
```

Expected response:
```json
{"ok":true,"env":"production"}
```

### Test Frontend
Visit: `https://your-project-name.vercel.app`

### Check Logs
In Vercel Dashboard:
- Go to "Deployments"
- Click your deployment
- View logs in "Function Logs" tab

## ⚠️ Important Limitations

| Limitation | Impact | Solution |
|-----------|--------|----------|
| No persistent filesystem | Files stored in `/tmp` are deleted between requests | Use external storage (AWS S3) or database |
| No SQLite | SQLite database resets | Use PostgreSQL |
| Max 60s execution (Pro) | Long inference times timeout | Use async processing or worker queue |
| Cold starts | First request takes 10-30s | Expected behavior |
| Model file size | Large models fail to deploy | Compress or store externally |

## 🚀 Custom Domain (Optional)

1. Go to Vercel Dashboard → Settings → Domains
2. Add your custom domain
3. Follow DNS setup instructions at your domain provider
4. Wait 10-30 minutes for propagation

## 📝 Updating Application

To deploy updates:
```bash
git add .
git commit -m "Update feature"
git push origin main
```

Vercel auto-deploys on every push to main!

## 🆘 Troubleshooting

### Error: "Module not found"
- Check `api/index.py` exists
- Verify Python import paths
- Check build logs in Vercel dashboard

### Error: "Database connection refused"
- Verify DATABASE_URL value in Vercel environment variables
- Test connection string locally first
- Check database is running and accessible

### Frontend shows blank page
- Check browser console for errors
- Verify VITE_API_URL is set correctly
- Check backend health endpoint

### Build takes too long
- Check frontend dependencies (remove unused packages)
- Split large models from code

## 📞 Support

For Vercel issues:
- Docs: https://vercel.com/docs
- Support: https://vercel.com/help

For FastAPI issues:
- Docs: https://fastapi.tiangolo.com
- GitHub: https://github.com/tiangolo/fastapi

# Quick Deployment Reference

## 1️⃣ PUSH TO GITHUB
```bash
git add .
git commit -m "Deploy to Vercel"
git push origin main
```

## 2️⃣ CREATE DATABASE
- Go to https://railway.app
- Create PostgreSQL database
- Copy CONNECTION_STRING (this is your DATABASE_URL)

## 3️⃣ DEPLOY ON VERCEL
- Go to https://vercel.com/new
- Import your GitHub repo
- Select framework: **Other**
- Root directory: **./frontend**
- Build command: `npm install && npm run build`
- Output: `dist`
- Set environment variables (see below)
- Click Deploy ✅

## 4️⃣ ENVIRONMENT VARIABLES (Set in Vercel Dashboard)

```
ENVIRONMENT=production
DATABASE_URL=postgresql://[user:password@host:port/database]
CORS_ORIGINS=https://your-project.vercel.app
JWT_SECRET=[generate: openssl rand -hex 32]
STORAGE_DIR=/tmp/storage
REPORTS_DIR=/tmp/storage/reports
```

## 5️⃣ VERIFY

```bash
# Test backend
curl https://your-project.vercel.app/api/health

# Open frontend
https://your-project.vercel.app
```

## 🔑 Generate JWT Secret
```bash
# On Windows PowerShell
[convert]::ToHexString((1..32 | ForEach-Object {[byte](Get-Random -Maximum 256)}))

# Or use online tool
https://www.uuidgenerator.net/
```

## 📊 Monitor Deployment
- Dashboard: https://vercel.com/dashboard
- Click your project
- Check "Deployments" tab
- View logs in "Functions"

## 🚨 Common Issues

**Frontend blank?**
→ Check VITE_API_URL in frontend/.env.production

**Backend 502 error?**
→ Check DATABASE_URL environment variable

**Can't upload files?**
→ Use /tmp storage or add S3 integration

---

⏱️ First deployment takes ~5-10 minutes. Subsequent updates deploy in ~1-2 minutes.

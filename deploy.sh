#!/bin/bash
set -e

echo "Building frontend..."
cd frontend
npm install
npm run build
cd ..

echo "Vercel deployment configured!"
echo ""
echo "Next steps:"
echo "1. Push to GitHub: git push origin main"
echo "2. Go to https://vercel.com and import your repository"
echo "3. Set environment variables in Vercel dashboard"
echo "4. Deploy!"

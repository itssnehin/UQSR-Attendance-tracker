# 🛠️ Netlify Deployment Troubleshooting

## ❌ Error: "Could not find a required file. Name: index.html"

### Problem
Netlify can't find the `index.html` file in the expected location.

### ✅ Solution 1: Use netlify.toml (Recommended)

1. **Make sure `netlify.toml` is in your repository ROOT** (not in frontend folder)
2. **In Netlify dashboard, set**:
   ```
   Base directory: (leave empty)
   Build command: (leave empty)
   Publish directory: (leave empty)
   ```
3. **Redeploy**

### ✅ Solution 2: Manual Configuration

1. **In Netlify dashboard, set**:
   ```
   Base directory: frontend
   Build command: npm run build
   Publish directory: frontend/build
   ```
2. **Redeploy**

### ✅ Solution 3: Alternative Build Command

If the above doesn't work, try:
```
Base directory: (leave empty)
Build command: cd frontend && npm install && npm run build
Publish directory: frontend/build
```

## 🔍 How to Check Your Setup

### 1. Verify File Structure
Your repository should look like:
```
UQSR-Attendance-tracker/
├── netlify.toml          ← Should be here (root)
├── frontend/
│   ├── public/
│   │   └── index.html    ← This file exists
│   ├── src/
│   ├── package.json
│   └── netlify.toml      ← Remove this if it exists
└── backend/
```

### 2. Check Build Logs
1. Go to Netlify dashboard
2. Click on your failed deployment
3. Check the build logs for specific errors

### 3. Test Local Build
```bash
cd frontend
npm install
npm run build
```
If this works locally, the issue is with Netlify configuration.

## 🚀 Quick Fix Steps

1. **Delete** `frontend/netlify.toml` if it exists
2. **Ensure** `netlify.toml` is in repository root
3. **In Netlify dashboard**:
   - Base directory: (empty)
   - Build command: (empty)
   - Publish directory: (empty)
4. **Add environment variable**:
   - `REACT_APP_API_URL` = `https://talented-intuition-production.up.railway.app`
5. **Redeploy**

## 📞 Still Having Issues?

### Check These Common Problems:

1. **Wrong repository selected** - Make sure you selected `UQSR-Attendance-tracker`
2. **Missing dependencies** - Netlify should run `npm install` automatically
3. **Node version** - netlify.toml specifies Node 18
4. **Environment variables** - Make sure `REACT_APP_API_URL` is set

### Alternative: Deploy from CLI

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login to Netlify
netlify login

# Deploy from frontend folder
cd frontend
npm run build
netlify deploy --prod --dir=build
```

## ✅ Success Indicators

When deployment works, you'll see:
- ✅ Build logs show "npm run build" completing successfully
- ✅ Site loads at your Netlify URL
- ✅ API calls work (check browser console)
- ✅ Admin panel accessible at `/admin`

## 🎯 Expected Build Output

Successful build should show:
```
9:48:48 PM: $ npm run build
9:48:48 PM: > runner-attendance-frontend@0.1.0 build
9:48:48 PM: > react-scripts build
9:48:49 PM: Creating an optimized production build...
9:48:52 PM: Compiled successfully.
9:48:52 PM: File sizes after gzip:
9:48:52 PM:   77.74 kB  build/static/js/main.5679b987.js
9:48:52 PM: The build folder is ready to be deployed.
```
# 🚀 Netlify Deployment Checklist

## ✅ Pre-deployment (DONE)

- [x] `netlify.toml` configuration file created
- [x] `.env.production` with correct API URL
- [x] Build script working (`npm run build`)
- [x] All files ready for deployment

## 🌐 Deploy to Netlify (DO THIS NOW)

### Step 1: Sign Up
1. Go to **[netlify.com](https://netlify.com)**
2. Click **"Sign up"**
3. Choose **"Sign up with GitHub"**
4. Authorize Netlify

### Step 2: Import Your Project
1. Click **"Add new site"** → **"Import an existing project"**
2. Choose **"Deploy with GitHub"**
3. Select your repository: **`UQSR-Attendance-tracker`**

### Step 3: Configure Build Settings

**Option 1 (Recommended)**: Use the netlify.toml file in your repo root
```
Base directory: (leave empty)
Build command: (leave empty - uses netlify.toml)
Publish directory: (leave empty - uses netlify.toml)
```

**Option 2**: Manual configuration
```
Base directory: frontend
Build command: npm run build
Publish directory: frontend/build
```

### Step 4: Deploy
1. Click **"Deploy site"**
2. Wait 2-3 minutes for build to complete
3. Get your live URL (e.g., `https://amazing-cupcake-123456.netlify.app`)

## 🔧 Post-deployment Setup

### Environment Variables (Important!)
1. Go to **Site settings** → **Environment variables**
2. Add this variable:
   ```
   REACT_APP_API_URL = https://talented-intuition-production.up.railway.app
   ```
3. **Redeploy** the site after adding variables

**Note**: Your app uses the same URL for both API calls and WebSocket connections, so you only need one environment variable!

### Test Your Site
1. **Visit your Netlify URL**
2. **Test registration**: Enter student number + session ID
3. **Test admin panel**: Go to `/admin`, login with `admin123`
4. **Verify API connection**: Check if data loads correctly

## 🎯 What You Get

### ✅ Benefits
- **FREE hosting** (save $240/year vs Vercel Pro)
- **100GB bandwidth** per month
- **300 build minutes** per month
- **Automatic deployments** from GitHub
- **Free SSL certificate**
- **Global CDN** for fast loading
- **Custom domain support** (free)

### 📊 Automatic Features
- **Branch previews** for pull requests
- **Deploy notifications** 
- **Build logs** for debugging
- **Analytics** dashboard
- **Form handling** (if needed later)

## 🔄 Future Updates

Every time you push to GitHub:
1. Netlify automatically detects changes
2. Builds your React app
3. Deploys the new version
4. Updates your live site

## 🆘 Troubleshooting

### Build Fails?
- Check deploy logs in Netlify dashboard
- Verify all dependencies are in `package.json`

### Site loads but API calls fail?
- Check environment variables are set
- Verify Railway backend is running

### 404 on page refresh?
- `netlify.toml` handles this (already configured)

## 📱 Share Your Site

Once deployed, share your Netlify URL with:
- Your running group members
- University social media
- QR code for easy access

## 🎉 You're Done!

Your attendance tracker is now:
- ✅ Live on the internet
- ✅ Automatically updating
- ✅ Free to host
- ✅ Fast and reliable
- ✅ Ready for 100+ users

**Next**: Test everything and start using it for your runs!
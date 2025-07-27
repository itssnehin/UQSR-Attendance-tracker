# Netlify Setup Guide - Step by Step

## 🚀 Quick Setup (5 minutes)

### Step 1: Prepare Your Repository

Your files are already configured! The `netlify.toml` file is ready and your `package.json` has the deploy script.

### Step 2: Sign Up for Netlify

1. Go to [netlify.com](https://netlify.com)
2. Click "Sign up" 
3. Choose "Sign up with GitHub" (easiest option)
4. Authorize Netlify to access your GitHub account

### Step 3: Deploy Your Site

1. **Click "Add new site" → "Import an existing project"**

2. **Choose GitHub** as your Git provider

3. **Select your repository**: `UQSR-Attendance-tracker`

4. **Configure build settings**:
   ```
   Base directory: frontend
   Build command: npm run build
   Publish directory: frontend/build
   ```

5. **Click "Deploy site"**

That's it! Netlify will:
- Install dependencies
- Build your React app
- Deploy it to a live URL

### Step 4: Get Your Live URL

After deployment (2-3 minutes), you'll get a URL like:
```
https://amazing-cupcake-123456.netlify.app
```

## 🔧 Advanced Configuration

### Environment Variables

1. Go to **Site settings** → **Environment variables**
2. Add your production variable:
   ```
   REACT_APP_API_URL = https://talented-intuition-production.up.railway.app
   ```
   
**Note**: Your app automatically handles both HTTP and WebSocket connections using this single URL!

### Custom Domain (Optional)

1. Go to **Domain settings**
2. Click "Add custom domain"
3. Enter your domain (e.g., `attendance.youruni.edu`)
4. Follow DNS setup instructions
5. Netlify provides free SSL automatically

### Branch Previews

Netlify automatically creates preview deployments for pull requests:
- Main branch → Production site
- Feature branches → Preview URLs

## 📱 Testing Your Deployment

1. **Visit your Netlify URL**
2. **Test registration flow**:
   - Go to registration page
   - Enter student number and session ID
   - Verify it connects to your Railway backend

3. **Test admin panel**:
   - Go to `/admin`
   - Login with password: `admin123`
   - Check calendar and attendance features

## 🔄 Automatic Deployments

Every time you push to GitHub:
1. Netlify detects the change
2. Automatically builds your app
3. Deploys the new version
4. Updates your live site

## 🛠️ Troubleshooting

### Build Fails?
Check the deploy log in Netlify dashboard for errors.

### Site loads but API calls fail?
Verify environment variables are set correctly.

### 404 on refresh?
The `netlify.toml` file handles this with redirects.

## 📊 Monitoring

Netlify provides:
- **Analytics**: Page views, unique visitors
- **Build logs**: Detailed deployment information  
- **Performance**: Core Web Vitals
- **Forms**: If you add contact forms later

## 💰 Cost Comparison

| Feature | Netlify Free | Vercel Free | Vercel Pro |
|---------|-------------|-------------|------------|
| Bandwidth | 100GB | 100GB | Unlimited |
| Build minutes | 300/month | Function limits | Unlimited |
| Sites | Unlimited | Unlimited | Unlimited |
| Team members | 1 | 1 | Unlimited |
| **Monthly cost** | **$0** | **$0** | **$20** |

## 🎯 Next Steps After Setup

1. **Update your documentation** with the new Netlify URL
2. **Share the link** with your running group
3. **Monitor usage** in Netlify dashboard
4. **Consider custom domain** if needed

## 🔗 Useful Links

- [Netlify Dashboard](https://app.netlify.com)
- [Netlify Docs](https://docs.netlify.com)
- [Custom Domain Setup](https://docs.netlify.com/domains-https/custom-domains/)
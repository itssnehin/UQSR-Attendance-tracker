# Frontend Deployment Guide - Vercel

## Prerequisites
- Vercel account (free tier available)
- GitHub repository connected to Vercel
- Backend deployed on Railway (for API endpoints)

## Environment Variables Setup

In your Vercel dashboard, configure the following environment variables:

### Required Environment Variables
```
REACT_APP_API_URL=https://your-backend-domain.railway.app
REACT_APP_WS_URL=https://your-backend-domain.railway.app
REACT_APP_ENVIRONMENT=production
```

### Setting Environment Variables in Vercel
1. Go to your project dashboard on Vercel
2. Navigate to Settings → Environment Variables
3. Add each variable with the appropriate value
4. Make sure to set them for Production, Preview, and Development environments

## Deployment Steps

### Automatic Deployment (Recommended)
1. Connect your GitHub repository to Vercel
2. Vercel will automatically deploy on every push to main branch
3. Configure environment variables as described above
4. Deployment will trigger automatically

### Manual Deployment
```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy from frontend directory
cd frontend
vercel --prod
```

## Build Configuration

The `vercel.json` file is already configured with:
- Static build optimization
- Proper caching headers for assets
- Security headers
- SPA routing support

## Post-Deployment Checklist

1. **Verify Environment Variables**: Check that API calls work correctly
2. **Test WebSocket Connection**: Ensure real-time updates function
3. **Check CORS Configuration**: Update backend CORS settings with your Vercel domain
4. **Test Mobile Responsiveness**: Verify mobile registration flow
5. **Performance Testing**: Check loading times and functionality

## Domain Configuration

### Custom Domain (Optional)
1. In Vercel dashboard, go to Settings → Domains
2. Add your custom domain
3. Configure DNS records as instructed
4. Update CORS settings in backend to include new domain

### SSL Certificate
- Vercel automatically provides SSL certificates
- No additional configuration needed

## Monitoring and Logs

- View deployment logs in Vercel dashboard
- Monitor performance with Vercel Analytics (optional)
- Set up error tracking with Sentry or similar service

## Troubleshooting

### Common Issues
1. **API calls failing**: Check REACT_APP_API_URL environment variable
2. **WebSocket not connecting**: Verify REACT_APP_WS_URL and backend CORS
3. **Build failures**: Check package.json dependencies and build scripts
4. **Routing issues**: Ensure vercel.json has proper SPA routing configuration

### Debug Commands
```bash
# Check build locally
npm run build

# Test production build locally
npx serve -s build

# Check environment variables
echo $REACT_APP_API_URL
```
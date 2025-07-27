#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🚀 Deploying to Netlify...\n');

// Check if netlify.toml exists
const netlifyConfig = path.join(__dirname, 'netlify.toml');
if (!fs.existsSync(netlifyConfig)) {
  console.error('❌ netlify.toml not found!');
  process.exit(1);
}

// Check if .env.production exists
const envFile = path.join(__dirname, '.env.production');
if (!fs.existsSync(envFile)) {
  console.error('❌ .env.production not found!');
  process.exit(1);
}

try {
  console.log('📦 Building React app...');
  execSync('npm run build', { stdio: 'inherit', cwd: __dirname });
  
  console.log('\n✅ Build completed successfully!');
  console.log('\n📋 Next steps:');
  console.log('1. Go to https://netlify.com');
  console.log('2. Sign up with GitHub');
  console.log('3. Import your repository');
  console.log('4. Set base directory to: frontend');
  console.log('5. Build command: npm run build');
  console.log('6. Publish directory: frontend/build');
  console.log('\n🎉 Your app will be live in 2-3 minutes!');
  
} catch (error) {
  console.error('❌ Build failed:', error.message);
  process.exit(1);
}
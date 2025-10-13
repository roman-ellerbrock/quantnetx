# Setup Guide

This guide will walk you through setting up QuantNetX and deploying the dashboard.

## Step 1: Move to Your Desired Location

```bash
# Move this folder to where you want it
mv /tmp/quantnetx ~/your-projects-folder/quantnetx
cd ~/your-projects-folder/quantnetx
```

## Step 2: Initialize Git (Already Done!)

Git is already initialized with your first commit. If you need to start fresh:

```bash
# Check current status
git status

# View commit history
git log
```

## Step 3: Create GitHub Repository

### Option A: Using GitHub CLI (recommended)

```bash
# Install GitHub CLI if you haven't: https://cli.github.com/
gh auth login

# Create repository and push
gh repo create quantnetx --public --source=. --push
```

### Option B: Using GitHub Web Interface

1. Go to https://github.com/new
2. Repository name: `quantnetx`
3. Description: "Quantitative analytics platform for cryptocurrency options and derivatives"
4. Choose Public or Private
5. Don't initialize with README (we already have one)
6. Click "Create repository"

Then connect your local repo:

```bash
git remote add origin https://github.com/YOUR_USERNAME/quantnetx.git
git branch -M main
git push -u origin main
```

## Step 4: Deploy (Choose One)

### Option A: GitHub Pages (Easiest)

1. Go to your repository on GitHub
2. Settings → Pages
3. Source: Deploy from a branch
4. Branch: `main` / `/ (root)`
5. Save

Your site will be at: `https://YOUR_USERNAME.github.io/quantnetx/`

### Option B: Vercel (Fast & Professional)

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? Your account
# - Link to existing project? No
# - Project name? quantnetx
# - Directory? ./
# - Override settings? No
```

Your site will be at: `https://quantnetx.vercel.app/`

### Option C: Netlify (Alternative)

**Method 1 - Drag & Drop:**
1. Go to https://app.netlify.com/drop
2. Drag the entire folder onto the page
3. Done!

**Method 2 - Git Integration:**
1. Go to https://app.netlify.com
2. Click "Add new site" → "Import an existing project"
3. Connect to GitHub
4. Select your repository
5. Click "Deploy site"

Your site will be at: `https://random-name.netlify.app/` (can customize)

### Option D: Use the Deploy Script

```bash
./deploy.sh
```

This interactive script will guide you through deployment options.

## Step 5: Custom Domain (Optional)

### For GitHub Pages:
1. Buy a domain (Namecheap, Google Domains, etc.)
2. Add CNAME file to repository with your domain
3. Configure DNS with your registrar:
   - Add CNAME record pointing to `YOUR_USERNAME.github.io`
4. Go to Settings → Pages → Custom domain

### For Vercel:
1. Go to project settings → Domains
2. Add your domain
3. Configure DNS as instructed

### For Netlify:
1. Go to Site settings → Domain management
2. Add custom domain
3. Configure DNS as instructed

## Updating the Dashboard

After making changes:

```bash
git add .
git commit -m "Description of your changes"
git push
```

- **GitHub Pages**: Automatically redeploys in ~1 minute
- **Vercel**: Automatically redeploys in ~30 seconds
- **Netlify**: Automatically redeploys in ~30 seconds

## Testing Locally

```bash
# Python
python3 -m http.server 8000

# Node.js
npx serve

# PHP
php -S localhost:8000
```

Then open: http://localhost:8000

## Adding New Features

QuantNetX is designed to grow. To add new analytics:

1. Create a new HTML file (e.g., `risk-metrics.html`)
2. Link to it from `index.html`
3. Reuse the shared styling and structure
4. Commit and push

## Troubleshooting

### Dashboard not loading
- Check browser console for errors (F12)
- Verify Deribit API is accessible (might be blocked in some regions)
- Try a different browser

### Git push fails
```bash
# If you need to force push (use carefully!)
git push -f origin main
```

### Deployment not updating
- Check deployment logs in your platform's dashboard
- Try clearing browser cache
- Verify git push was successful

## Next Steps

- ⭐ Star the repository
- 📝 Customize the dashboard for your needs
- 🐛 Report issues on GitHub
- 🚀 Share with others!
- 💡 Add new analytics features

## Support

For issues or questions:
1. Check the main README.md
2. Search existing GitHub issues
3. Create a new issue with details

---

Happy deploying! 🚀

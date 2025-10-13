#!/bin/bash

# Deploy script for QuantNetX
# This script helps you quickly deploy to various platforms

set -e

echo "=================================================="
echo "🚀 QuantNetX Deployment"
echo "=================================================="
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "❌ Git not initialized. Run: git init"
    exit 1
fi

# Check if we have commits
if ! git rev-parse HEAD > /dev/null 2>&1; then
    echo "❌ No commits found. Run: git commit -m 'Initial commit'"
    exit 1
fi

echo "Select deployment platform:"
echo "1) GitHub Pages"
echo "2) Vercel"
echo "3) Netlify"
echo "4) Just push to GitHub"
echo "5) Test locally"
echo ""
read -p "Enter choice (1-5): " choice

case $choice in
    1)
        echo ""
        echo "📄 GitHub Pages Deployment"
        echo "----------------------------"
        echo "1. Make sure you've pushed to GitHub"
        echo "2. Go to: https://github.com/YOUR_USERNAME/quantnetx/settings/pages"
        echo "3. Select: Deploy from branch → main → / (root)"
        echo "4. Save and wait ~1 minute"
        echo ""
        echo "Your site will be at:"
        echo "https://YOUR_USERNAME.github.io/quantnetx/"
        echo ""
        read -p "Push to GitHub now? (y/n): " push
        if [ "$push" = "y" ]; then
            git push origin main
            echo "✅ Pushed to GitHub!"
        fi
        ;;
    2)
        echo ""
        echo "⚡ Vercel Deployment"
        echo "-------------------"
        if ! command -v vercel &> /dev/null; then
            echo "Installing Vercel CLI..."
            npm install -g vercel
        fi
        echo "Deploying to Vercel..."
        vercel --prod
        ;;
    3)
        echo ""
        echo "🎯 Netlify Deployment"
        echo "--------------------"
        if ! command -v netlify &> /dev/null; then
            echo "Installing Netlify CLI..."
            npm install -g netlify-cli
        fi
        echo "Deploying to Netlify..."
        netlify deploy --prod
        ;;
    4)
        echo ""
        echo "📤 Pushing to GitHub"
        echo "-------------------"
        read -p "Enter GitHub username: " username
        read -p "Enter repository name [quantnetx]: " repo
        repo=${repo:-quantnetx}

        git remote remove origin 2>/dev/null || true
        git remote add origin "https://github.com/$username/$repo.git"
        git push -u origin main

        echo "✅ Pushed to GitHub!"
        echo "Repository: https://github.com/$username/$repo"
        ;;
    5)
        echo ""
        echo "🧪 Testing locally"
        echo "-----------------"
        echo "Starting server at http://localhost:8000"
        echo "Press Ctrl+C to stop"
        echo ""
        python3 -m http.server 8000
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "=================================================="
echo "✅ Done!"
echo "=================================================="

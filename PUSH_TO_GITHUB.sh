#!/bin/bash

# GitHub Push Script for LinkedIn Enricher
# Run this script to initialize git and push to GitHub

set -e

echo "=========================================="
echo "GitHub Setup for LinkedIn Enricher"
echo "=========================================="
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install git first."
    exit 1
fi

echo "✅ Git is installed"
echo ""

# Check if already a git repository
if [ -d ".git" ]; then
    echo "⚠️  Git repository already initialized"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "📦 Initializing git repository..."
    git init
    echo "✅ Git repository initialized"
fi

echo ""
echo "📝 Adding files to git..."
git add .

echo ""
echo "📋 Files to be committed:"
git status --short | head -20
echo ""

read -p "Review the files above. Continue with commit? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Aborted"
    exit 1
fi

echo ""
echo "💾 Creating initial commit..."
git commit -m "Initial commit: LinkedIn Profile Enricher

Features:
- CSV upload and processing with resume functionality
- Lead management (Raw Lead, Qualified, Contacted)
- LLM integration for lead analysis
- Automatic column detection and storage
- Database cleanup utilities
- React frontend with modern UI"

echo "✅ Commit created"
echo ""

echo "🔗 Next steps:"
echo "1. Create a new repository on GitHub (don't initialize with README)"
echo "2. Run the following commands (replace with your repo URL):"
echo ""
echo "   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "Or use SSH:"
echo "   git remote add origin git@github.com:YOUR_USERNAME/YOUR_REPO_NAME.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""

read -p "Do you want to add remote now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter your GitHub repository URL: " repo_url
    if [ ! -z "$repo_url" ]; then
        git remote add origin "$repo_url"
        echo "✅ Remote added: $repo_url"
        echo ""
        read -p "Push to GitHub now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git branch -M main
            echo "🚀 Pushing to GitHub..."
            git push -u origin main
            echo "✅ Successfully pushed to GitHub!"
        fi
    fi
fi

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="


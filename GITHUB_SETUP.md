# GitHub Setup Guide

This guide will help you push the LinkedIn Enricher code to GitHub.

## Prerequisites

1. **Git installed** - Check with: `git --version`
2. **GitHub account** - Create one at https://github.com if you don't have one
3. **GitHub repository** - Create a new repository on GitHub (don't initialize with README)

## Step-by-Step Instructions

### 1. Initialize Git Repository

```bash
cd /Users/pm/Documents/enricher
git init
```

### 2. Add All Files

```bash
git add .
```

### 3. Create Initial Commit

```bash
git commit -m "Initial commit: LinkedIn Profile Enricher with resume functionality"
```

### 4. Add Remote Repository

Replace `YOUR_USERNAME` and `YOUR_REPO_NAME` with your actual GitHub username and repository name:

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
```

Or if using SSH:
```bash
git remote add origin git@github.com:YOUR_USERNAME/YOUR_REPO_NAME.git
```

### 5. Push to GitHub

```bash
git branch -M main
git push -u origin main
```

## What's Included

The `.gitignore` file is configured to exclude:
- ✅ Database files (`*.db`, `*.sqlite`)
- ✅ Upload files (`uploads/`)
- ✅ Result files (`results/`)
- ✅ Python cache (`__pycache__/`)
- ✅ Node modules (`node_modules/`)
- ✅ Environment files (`.env`)
- ✅ OS files (`.DS_Store`)
- ✅ Build artifacts

## Important Notes

### Before Pushing

1. **Check for sensitive data:**
   - No API keys in code
   - No database files
   - No personal information in uploads/results

2. **Review what will be committed:**
   ```bash
   git status
   ```

3. **See what files will be added:**
   ```bash
   git ls-files
   ```

### After Pushing

1. **Add a README** (if not already present) with:
   - Project description
   - Installation instructions
   - Usage guide
   - License information

2. **Consider adding:**
   - `.github/workflows/` for CI/CD
   - `LICENSE` file
   - `CONTRIBUTING.md` if open source

## Troubleshooting

### If you get authentication errors:

1. **Use Personal Access Token:**
   - GitHub Settings → Developer settings → Personal access tokens
   - Generate new token with `repo` scope
   - Use token as password when pushing

2. **Or set up SSH keys:**
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   # Then add to GitHub Settings → SSH and GPG keys
   ```

### If you need to update .gitignore:

```bash
# Remove files from git cache (but keep locally)
git rm -r --cached uploads/
git rm --cached enricher.db

# Commit the changes
git add .gitignore
git commit -m "Update .gitignore to exclude database and uploads"
```

## Next Steps

1. ✅ Initialize git repository
2. ✅ Add and commit files
3. ✅ Create GitHub repository
4. ✅ Add remote and push
5. ✅ Add repository description and topics on GitHub
6. ✅ Consider adding GitHub Actions for automated testing

## Repository Structure

```
enricher/
├── admin_app.py          # Flask backend API
├── database.py           # Database models and operations
├── enricher/             # Core enrichment logic
├── frontend/             # React frontend
├── requirements.txt      # Python dependencies
├── README.md             # Main documentation
└── .gitignore           # Git ignore rules
```


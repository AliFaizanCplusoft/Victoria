# Git Repository Setup & Files to Exclude

## Git Repository Information

**Repository URL:** `https://github.com/AliFaizanCplusoft/Victoria.git`  
**Current Branch:** `main`  
**Remote Name:** `origin`

## Files That Should NOT Be Committed to GitHub

### 🔴 CRITICAL - Contains Sensitive Data (DO NOT COMMIT):
- `.env` - Contains API keys and secrets
- `responses.csv` - Contains personal data (emails, names, assessment responses)
- `data/` - Contains assessment data with personal information
- `output/reports/` - Generated reports may contain personal data

### 🟡 Environment & Configuration Files:
- `.venv/` - Python virtual environment (too large, regeneratable)
- `docker.env` - May contain secrets (keep `docker.env.example` instead)
- `env.prod` - May contain secrets (keep `env.prod.example` instead)

### 🟡 Logs & Temporary Files:
- `*.log` - All log files
- `logs/` - Log directory
- `api.log`
- `victoria_pipeline.log`
- `app/api/api.log`
- `app/api/logs/`
- `app/streamlit/logs/`

### 🟡 Python Cache & Build Files:
- `__pycache__/` - Python bytecode cache (all directories)
- `*.pyc`, `*.pyo`, `*.pyd` - Compiled Python files
- `.pytest_cache/` - Test cache

### 🟡 Generated Output Files:
- `output/` - Generated reports directory
- `output/reports/*.html` - Generated HTML reports

### 🟡 Temporary & Backup Files:
- `temp/` - Temporary files directory
- `*.backup` - Backup files
- `main.py.backup`
- `evictoria_pipeline.py` - Temporary/generated file

### 🟡 IDE & OS Files:
- `.vscode/`, `.idea/` - IDE settings
- `.claude/`, `.cursor/` - AI editor settings
- `.DS_Store`, `Thumbs.db` - OS files
- `.qodo/` - Qodo directory

### 🟡 SSL & Security:
- `ssl/` - SSL certificates
- `*.pem`, `*.key`, `*.crt` - Certificate files

### 🟡 Deployment Scripts (if they contain secrets):
- `deploy.sh` - May contain server credentials
- `deploy_now.ps1` - May contain server credentials
- `test_api_server.py` - Test script (may contain API keys)

### 🟡 Other Files:
- `check_api_key_quota.py` - May contain API keys
- `victoria/visualization/` - Unknown directory (check contents)

## Files That SHOULD Be Committed:

✅ Source code files (`.py` files in `victoria/`, `app/`)  
✅ Templates (`templates/html/vertria_comprehensive_report.html`)  
✅ Configuration files (`docker-compose.prod.yml`, `Dockerfile.prod`, `nginx.prod.conf`)  
✅ Documentation files (`README.md`, `DOCKER_README.md`)  
✅ Requirements (`requirements.txt`)  
✅ `.gitignore` file (created)  
✅ Example files (`docker.env.example`, `env.prod.example` - if you create them)

## Next Steps to Push Code:

1. **Review and commit the .gitignore file:**
   ```powershell
   git add .gitignore
   git commit -m "Add comprehensive .gitignore file"
   ```

2. **Remove sensitive files from git tracking (if already tracked):**
   ```powershell
   git rm --cached .env
   git rm --cached responses.csv
   git rm -r --cached output/
   git rm -r --cached logs/
   git rm -r --cached __pycache__/
   git rm -r --cached .venv/
   git rm -r --cached app/__pycache__/
   git rm -r --cached templates/__pycache__/
   git rm -r --cached victoria/__pycache__/
   git rm --cached *.log
   ```

3. **Stage your code changes:**
   ```powershell
   git add victoria/
   git add app/
   git add templates/
   git add Dockerfile.prod
   git add docker-compose.prod.yml
   git add nginx.prod.conf
   git add victoria_pipeline.py
   ```

4. **Commit your changes:**
   ```powershell
   git commit -m "Update visualization engine, report generator, and API endpoints"
   ```

5. **Push to GitHub:**
   ```powershell
   git push origin main
   ```

## Important Notes:

⚠️ **Before pushing, ensure:**
- No API keys or secrets are in committed files
- No personal data (emails, names) are in committed files
- All sensitive files are in `.gitignore`
- Review `git status` before committing

⚠️ **If you've already committed sensitive files:**
- They need to be removed from git history (use `git filter-branch` or BFG Repo-Cleaner)
- Change any exposed API keys immediately

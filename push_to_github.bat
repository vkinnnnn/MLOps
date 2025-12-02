@echo off
echo ========================================
echo GitHub Integration - Push to LoanQA-MLOps
echo ========================================
echo.

REM Change to the directory where this script lives (project root)
cd /d "%~dp0"

echo [1/4] Creating commit...
git commit -m "feat: Complete LoanQA integration with multi-LLM support and React frontend" -m "- Multi-LLM integration (OpenAI GPT-4o-mini, Anthropic Claude 3.5 Haiku, Kimi K2 Turbo)" -m "- Professional React/Next.js 14 frontend with dark theme" -m "- 7 reusable React components" -m "- 5 main views (Dashboard, Chat, Upload, Documents, History)" -m "- Multi-language support (10 languages)" -m "- ChromaDB vector store for semantic search" -m "- Document chunking service" -m "- 10 Docker services deployed and running" -m "- Complete documentation (v3.0.0)" -m "- Demo mode for offline functionality" -m "" -m "Co-authored-by: factory-droid[bot] <138933559+factory-droid[bot]@users.noreply.github.com>"

if %errorlevel% neq 0 (
    echo ERROR: Commit failed!
    pause
    exit /b 1
)

echo.
echo [2/4] Creating upload branch...
git checkout -b upload

if %errorlevel% neq 0 (
    echo ERROR: Branch creation failed!
    pause
    exit /b 1
)

echo.
echo [3/4] Pushing to LoanQA-MLOps repository...
git push loanqa upload

if %errorlevel% neq 0 (
    echo ERROR: Push failed!
    echo.
    echo You may need to authenticate with GitHub.
    echo Or the branch may already exist.
    echo.
    echo Try: git push loanqa upload --force
    pause
    exit /b 1
)

echo.
echo [4/4] Optionally pushing to origin repository...
git push origin upload

echo.
echo ========================================
echo SUCCESS! Integration pushed to GitHub!
echo ========================================
echo.
echo Repository: https://github.com/nkousik18/LoanQA-MLOps
echo Branch: upload
echo.
echo Next steps:
echo 1. Visit: https://github.com/nkousik18/LoanQA-MLOps/tree/upload
echo 2. Verify the code is there
echo 3. Create a Pull Request if needed
echo.
pause

@echo off
REM Student Loan Document Extractor - Project Startup Script (Windows Batch)
REM Launches the PowerShell startup script with progress indicators

echo.
echo ========================================
echo Starting LoanIQ Project...
echo ========================================
echo.

powershell.exe -ExecutionPolicy Bypass -File "%~dp0start_project.ps1"

pause










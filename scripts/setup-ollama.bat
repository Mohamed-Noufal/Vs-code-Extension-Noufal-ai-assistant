@echo off
REM Ollama Setup Script for Multi-Agent Development System (Windows)
REM This script helps set up Ollama on Windows

setlocal enabledelayedexpansion

echo 🚀 Ollama Setup Script for Multi-Agent Development System
echo ========================================================
echo.

REM Check if Ollama is already installed
where ollama >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Ollama is already installed
    goto :check_service
) else (
    echo ❌ Ollama is not installed
    echo.
    echo Please download and install Ollama from:
    echo   https://ollama.ai/download
    echo.
    echo After installation:
    echo 1. Restart your terminal
    echo 2. Run this script again
    echo.
    pause
    exit /b 1
)

:check_service
echo 🔍 Checking if Ollama service is running...

REM Try to connect to Ollama service
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Ollama service is already running
    goto :check_model
) else (
    echo ⚠️  Ollama service is not running
    echo 🔄 Starting Ollama service...
    
    REM Start Ollama in background
    start /b ollama serve
    
    REM Wait for service to start
    echo ⏳ Waiting for Ollama service to start...
    for /l %%i in (1,1,30) do (
        timeout /t 1 /nobreak >nul
        curl -s http://localhost:11434/api/tags >nul 2>&1
        if !errorlevel! equ 0 (
            echo ✅ Ollama service started successfully
            goto :check_model
        )
    )
    
    echo ❌ Failed to start Ollama service
    echo Please start Ollama manually with: ollama serve
    pause
    exit /b 1
)

:check_model
echo 🔍 Checking if Mistral model is available...

REM Check if model is already downloaded
ollama list | findstr "mistral:7b-instruct" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Mistral model is already available
    goto :verify_installation
) else (
    echo 📥 Downloading Mistral 7B Instruct model...
    echo This may take a while depending on your internet connection...
    
    ollama pull mistral:7b-instruct
    if %errorlevel% equ 0 (
        echo ✅ Mistral model downloaded successfully
    ) else (
        echo ❌ Failed to download Mistral model
        pause
        exit /b 1
    )
)

:verify_installation
echo 🔍 Verifying Ollama installation...

REM Check Ollama version
for /f "tokens=*" %%i in ('ollama --version') do set VERSION=%%i
echo ✅ Ollama version: !VERSION!

REM Check if service is running
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Ollama service is running
) else (
    echo ❌ Ollama service is not running
    pause
    exit /b 1
)

REM Check if model is available
ollama list | findstr "mistral:7b-instruct" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Mistral model is available
) else (
    echo ❌ Mistral model is not available
    pause
    exit /b 1
)

echo.
echo 🎉 Ollama setup completed successfully!
echo.
echo Next steps:
echo 1. Run 'make dev-setup' to set up the development environment
echo 2. Run 'make dev' to start the development servers
echo 3. Check OLLAMA_SETUP.md for more detailed information
echo.
pause

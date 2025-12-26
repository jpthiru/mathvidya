@echo off
REM Mathvidya Database Backup Script (Local) - Windows Version
REM
REM Creates a compressed backup of the PostgreSQL database and stores it locally.
REM
REM Usage: backup-local.bat [backup_dir]
REM
REM Examples:
REM   backup-local.bat
REM   backup-local.bat C:\backups\mathvidya

setlocal enabledelayedexpansion

REM Configuration
set CONTAINER_NAME=mathvidya-postgres
set DB_NAME=mathvidya
set DB_USER=mathvidya_user
set BACKUP_DIR=%~1
if "%BACKUP_DIR%"=="" set BACKUP_DIR=.\backups
set RETENTION_COUNT=7

REM Generate timestamp
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set TIMESTAMP=%datetime:~0,8%_%datetime:~8,6%
set BACKUP_FILE=mathvidya_backup_%TIMESTAMP%.sql

echo ========================================
echo   Mathvidya Database Backup (Local)
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not running
    exit /b 1
)

REM Check if container is running
docker ps --format "{{.Names}}" | findstr /C:"%CONTAINER_NAME%" >nul
if errorlevel 1 (
    echo Error: Container '%CONTAINER_NAME%' is not running
    echo Please ensure the database container is up:
    echo   docker-compose up -d postgres
    exit /b 1
)

REM Create backup directory
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"
echo Backup directory: %BACKUP_DIR%

REM Create the backup
echo Creating backup...
docker exec %CONTAINER_NAME% pg_dump -U %DB_USER% %DB_NAME% > "%BACKUP_DIR%\%BACKUP_FILE%"

REM Check if backup was created
if not exist "%BACKUP_DIR%\%BACKUP_FILE%" (
    echo Error: Backup file was not created
    exit /b 1
)

REM Get file size
for %%A in ("%BACKUP_DIR%\%BACKUP_FILE%") do set BACKUP_SIZE=%%~zA
echo Backup created successfully!
echo   File: %BACKUP_FILE%
echo   Size: %BACKUP_SIZE% bytes

REM Compress with gzip if available
where gzip >nul 2>&1
if not errorlevel 1 (
    echo Compressing backup...
    gzip "%BACKUP_DIR%\%BACKUP_FILE%"
    set BACKUP_FILE=%BACKUP_FILE%.gz
)

echo.
echo Current backups:
dir /b "%BACKUP_DIR%\mathvidya_backup_*"

echo.
echo Backup completed successfully!
echo To restore, use: restore.bat "%BACKUP_DIR%\%BACKUP_FILE%"

endlocal

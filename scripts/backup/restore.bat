@echo off
REM Mathvidya Database Restore Script - Windows Version
REM
REM Restores the PostgreSQL database from a backup file.
REM CAUTION: This will REPLACE all data in the current database!
REM
REM Usage: restore.bat <backup_file>
REM
REM Examples:
REM   restore.bat .\backups\mathvidya_backup_20241226_120000.sql
REM   restore.bat .\backups\mathvidya_backup_20241226_120000.sql.gz

setlocal enabledelayedexpansion

REM Configuration
set CONTAINER_NAME=mathvidya-postgres
set DB_NAME=mathvidya
set DB_USER=mathvidya_user

echo ========================================
echo   Mathvidya Database Restore
echo ========================================
echo.

REM Check arguments
if "%~1"=="" (
    echo Error: No backup file specified
    echo.
    echo Usage: restore.bat ^<backup_file^>
    echo.
    echo Available backups:
    dir /b .\backups\mathvidya_backup_* 2>nul || echo   No backups found in .\backups\
    exit /b 1
)

set BACKUP_FILE=%~1

REM Check if backup file exists
if not exist "%BACKUP_FILE%" (
    echo Error: Backup file not found: %BACKUP_FILE%
    exit /b 1
)

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

echo Backup file: %BACKUP_FILE%
echo.
echo WARNING: This will REPLACE ALL DATA in the database!
echo All current data will be lost!
echo.
set /p CONFIRM="Are you sure you want to continue? (type 'yes' to confirm): "

if not "%CONFIRM%"=="yes" (
    echo.
    echo Restore cancelled.
    exit /b 0
)

echo.
echo Starting restore process...

REM Step 1: Create pre-restore backup
echo.
echo Step 1: Creating pre-restore backup (safety)...
if not exist ".\backups" mkdir ".\backups"
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set PRE_TIMESTAMP=%datetime:~0,8%_%datetime:~8,6%
docker exec %CONTAINER_NAME% pg_dump -U %DB_USER% %DB_NAME% > ".\backups\pre_restore_%PRE_TIMESTAMP%.sql"
echo   Created: .\backups\pre_restore_%PRE_TIMESTAMP%.sql

REM Step 2: Drop and recreate database
echo.
echo Step 2: Preparing database...
docker exec %CONTAINER_NAME% psql -U %DB_USER% -d postgres -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '%DB_NAME%' AND pid ^<^> pg_backend_pid();" >nul 2>&1
docker exec %CONTAINER_NAME% psql -U %DB_USER% -d postgres -c "DROP DATABASE IF EXISTS %DB_NAME%;"
docker exec %CONTAINER_NAME% psql -U %DB_USER% -d postgres -c "CREATE DATABASE %DB_NAME% OWNER %DB_USER%;"
echo   Database recreated

REM Step 3: Restore from backup
echo.
echo Step 3: Restoring from backup...

REM Check if file is gzipped
echo %BACKUP_FILE% | findstr /C:".gz" >nul
if not errorlevel 1 (
    REM Decompress first if gzip is available
    where gzip >nul 2>&1
    if not errorlevel 1 (
        echo   Decompressing backup...
        gzip -dk "%BACKUP_FILE%"
        set BACKUP_FILE=%BACKUP_FILE:.gz=%
    ) else (
        echo Error: gzip not found. Please decompress the file manually.
        exit /b 1
    )
)

type "%BACKUP_FILE%" | docker exec -i %CONTAINER_NAME% psql -U %DB_USER% -d %DB_NAME%
echo   Restore completed

REM Step 4: Verify restore
echo.
echo Step 4: Verifying restore...
docker exec %CONTAINER_NAME% psql -U %DB_USER% -d %DB_NAME% -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"

echo.
echo ========================================
echo   Restore Complete!
echo ========================================
echo.
echo Pre-restore backup saved at: .\backups\pre_restore_%PRE_TIMESTAMP%.sql
echo.
echo Note: You may need to restart the backend service:
echo   docker-compose restart backend

endlocal

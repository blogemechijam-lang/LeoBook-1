# setup_windows_env.ps1
# PowerShell script to set up llama.cpp environment on Windows

param(
    [string]$ReleaseVersion = "b4458"
)

$MIND_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "Setting up Llama environment in: $MIND_DIR"

# 1. Construct download URL for Windows binaries
$DOWNLOAD_URL = "https://github.com/ggerganov/llama.cpp/releases/download/$ReleaseVersion/llama-$ReleaseVersion-bin-win-avx2-x64.zip"
Write-Host "Downloading from: $DOWNLOAD_URL"

# 2. Download the ZIP file
$ZIP_PATH = Join-Path $MIND_DIR "llama-windows.zip"
try {
    Invoke-WebRequest -Uri $DOWNLOAD_URL -OutFile $ZIP_PATH -UseBasicParsing
    Write-Host "Download completed successfully."
} catch {
    Write-Error "Failed to download file: $_"
    exit 1
}

# 3. Extract the ZIP file
$EXTRACT_PATH = Join-Path $MIND_DIR "temp_extract"
if (Test-Path $EXTRACT_PATH) {
    Remove-Item -Recurse -Force $EXTRACT_PATH
}

try {
    Expand-Archive -Path $ZIP_PATH -DestinationPath $EXTRACT_PATH -Force
    Write-Host "Extraction completed."
} catch {
    Write-Error "Failed to extract ZIP file: $_"
    exit 1
}

# 4. Find and copy the binaries
$SOURCE_DIR = $null

# Check for build/bin structure
$BUILD_BIN_PATH = Join-Path $EXTRACT_PATH "build\bin"
if (Test-Path (Join-Path $BUILD_BIN_PATH "llama-server.exe")) {
    $SOURCE_DIR = $BUILD_BIN_PATH
} elseif (Test-Path (Join-Path $EXTRACT_PATH "llama-server.exe")) {
    $SOURCE_DIR = $EXTRACT_PATH
}

if ($SOURCE_DIR) {
    Write-Host "Found binaries in: $SOURCE_DIR"

    # Copy the main executable
    $SERVER_SOURCE = Join-Path $SOURCE_DIR "llama-server.exe"
    $SERVER_DEST = Join-Path $MIND_DIR "llama-server.exe"
    if (Test-Path $SERVER_SOURCE) {
        Copy-Item -Path $SERVER_SOURCE -Destination $SERVER_DEST -Force
        Write-Host "Copied llama-server.exe"
    }

    # Copy all DLL files
    $DLL_FILES = Get-ChildItem -Path $SOURCE_DIR -Filter "*.dll" -File
    foreach ($dll in $DLL_FILES) {
        $DEST_PATH = Join-Path $MIND_DIR $dll.Name
        Copy-Item -Path $dll.FullName -Destination $DEST_PATH -Force
        Write-Host "Copied $($dll.Name)"
    }
} else {
    Write-Error "ERROR: Could not find llama-server.exe in extracted archive!"
    Get-ChildItem -Recurse $EXTRACT_PATH | Select-Object FullName
    exit 1
}

# 5. Cleanup
Remove-Item -Recurse -Force $EXTRACT_PATH -ErrorAction SilentlyContinue
Remove-Item -Force $ZIP_PATH -ErrorAction SilentlyContinue

Write-Host "========================================"
Write-Host "SUCCESS!"
Write-Host "llama-server.exe has been installed to: $MIND_DIR\llama-server.exe"
Write-Host "You can now run 'python Leo.py' in your project."
Write-Host "========================================"

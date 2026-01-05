#!/bin/bash
#setup_linux_env.sh

# Define extraction directory
MIND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Setting up Llama environment in: $MIND_DIR"

# 1. Hardcoded URL for latest stable release (b4458) to avoid API limit errors
LATEST_RELEASE_URL="https://github.com/ggerganov/llama.cpp/releases/download/b4458/llama-b4458-bin-ubuntu-x64.zip"

echo "Downloading from: $LATEST_RELEASE_URL"

# 2. Download the file
curl -L -o "$MIND_DIR/llama-linux.zip" "$LATEST_RELEASE_URL"

# 3. Unzip everything to get libraries (libllama.so, etc.)
echo "Extracting all files..."
unzip -o "$MIND_DIR/llama-linux.zip" -d "$MIND_DIR/temp_extract"

# Handle different ZIP structures (some have build/bin, some are flat)
SOURCE_DIR=""
if [ -f "$MIND_DIR/temp_extract/build/bin/llama-server" ]; then
    SOURCE_DIR="$MIND_DIR/temp_extract/build/bin"
elif [ -f "$MIND_DIR/temp_extract/llama-server" ]; then
    SOURCE_DIR="$MIND_DIR/temp_extract"
fi

if [ -n "$SOURCE_DIR" ]; then
    echo "Found binaries in: $SOURCE_DIR"
    echo "Moving binaries and libraries..."
    mv "$SOURCE_DIR/llama-server" "$MIND_DIR/llama-server"
    mv "$SOURCE_DIR"/*.so "$MIND_DIR/" 2>/dev/null || true
else
    echo "ERROR: Could not find llama-server in extracted archive!"
    ls -R "$MIND_DIR/temp_extract"
fi

# Cleanup
rm -rf "$MIND_DIR/temp_extract"

# 4. Cleanup
rm "$MIND_DIR/llama-linux.zip"

# 5. Make executable
chmod +x "$MIND_DIR/llama-server"

echo "========================================"
echo "SUCCESS!"
echo "llama-server has been installed to: $MIND_DIR/llama-server"
echo "You can now run 'python Leo.py' in your Codespace."
echo "========================================"

#!/bin/bash
# setup_codespaces_env.sh
# GitHub Codespaces setup script for llama.cpp environment

# Define extraction directory
MIND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Setting up Llama environment in Codespaces: $MIND_DIR"

# Check if we're in Codespaces
if [ -z "$CODESPACES" ]; then
    echo "Warning: CODESPACES environment variable not detected."
    echo "This script is optimized for GitHub Codespaces but will work in other Linux environments."
fi

# 1. Use a recent stable release that's known to work well
LATEST_RELEASE_URL="https://github.com/ggerganov/llama.cpp/releases/download/b4458/llama-b4458-bin-ubuntu-x64.zip"

echo "Downloading llama.cpp binaries from: $LATEST_RELEASE_URL"

# 2. Download with progress indicator
if command -v wget &> /dev/null; then
    wget -O "$MIND_DIR/llama-codespaces.zip" "$LATEST_RELEASE_URL"
else
    curl -L -o "$MIND_DIR/llama-codespaces.zip" "$LATEST_RELEASE_URL"
fi

# 3. Extract files
echo "Extracting files..."
unzip -o "$MIND_DIR/llama-codespaces.zip" -d "$MIND_DIR/temp_extract"

# Handle different ZIP structures
SOURCE_DIR=""
if [ -f "$MIND_DIR/temp_extract/build/bin/llama-server" ]; then
    SOURCE_DIR="$MIND_DIR/temp_extract/build/bin"
    echo "Found binaries in build/bin structure"
elif [ -f "$MIND_DIR/temp_extract/llama-server" ]; then
    SOURCE_DIR="$MIND_DIR/temp_extract"
    echo "Found binaries in flat structure"
fi

if [ -n "$SOURCE_DIR" ]; then
    echo "Copying files to Mind directory..."

    # Copy the server executable
    if [ -f "$SOURCE_DIR/llama-server" ]; then
        cp "$SOURCE_DIR/llama-server" "$MIND_DIR/llama-server"
        echo "✓ Copied llama-server"
    fi

    # Copy all shared libraries
    if ls "$SOURCE_DIR"/*.so 1> /dev/null 2>&1; then
        cp "$SOURCE_DIR"/*.so "$MIND_DIR/" 2>/dev/null
        echo "✓ Copied shared libraries"
    fi

    # Copy any additional runtime files
    if ls "$SOURCE_DIR"/*.so.* 1> /dev/null 2>&1; then
        cp "$SOURCE_DIR"/*.so.* "$MIND_DIR/" 2>/dev/null
        echo "✓ Copied versioned libraries"
    fi
else
    echo "ERROR: Could not find llama-server in extracted archive!"
    echo "Contents of extracted directory:"
    find "$MIND_DIR/temp_extract" -name "llama-server" 2>/dev/null || echo "llama-server not found"
    ls -la "$MIND_DIR/temp_extract"
    exit 1
fi

# Cleanup
echo "Cleaning up temporary files..."
rm -rf "$MIND_DIR/temp_extract"
rm -f "$MIND_DIR/llama-codespaces.zip"

# 4. Make executable and verify
chmod +x "$MIND_DIR/llama-server"

# Verify the installation
if [ -f "$MIND_DIR/llama-server" ]; then
    echo "✓ llama-server installed successfully"

    # Test library dependencies
    echo "Checking library dependencies..."
    if command -v ldd &> /dev/null; then
        MISSING_LIBS=$(ldd "$MIND_DIR/llama-server" 2>/dev/null | grep "not found" | wc -l)
        if [ "$MISSING_LIBS" -eq 0 ]; then
            echo "✓ All library dependencies satisfied"
        else
            echo "⚠ Some libraries may be missing (this is normal in Codespaces)"
        fi
    fi
else
    echo "ERROR: Failed to install llama-server!"
    exit 1
fi

echo ""
echo "========================================"
echo "🎉 SUCCESS!"
echo "llama-server has been installed to: $MIND_DIR/llama-server"
echo ""
echo "Next steps:"
echo "1. Run: python Leo.py"
echo "2. The system will automatically start the AI server"
echo "========================================"

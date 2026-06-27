#!/bin/bash

# Test script for generate-image.js

echo "🧪 Testing Image Generation Tool"
echo "================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_PROMPT="$SCRIPT_DIR/test-prompt.md"
TEST_OUTPUT="/tmp/test-architecture-diagram.png"

# Test 1: Check dependencies
echo "Test 1: Checking dependencies..."
echo ""

if command -v node >/dev/null 2>&1; then
    echo "✅ Node.js: $(node --version)"
else
    echo "❌ Node.js not found"
    exit 1
fi

if command -v codex >/dev/null 2>&1; then
    echo "✅ codex-cli available"
    HAS_CODEX=true
else
    echo "⚠️  codex-cli not available"
    HAS_CODEX=false
fi

if command -v agy >/dev/null 2>&1; then
    echo "✅ agy (Antigravity CLI) available"
    HAS_AGY=true
else
    echo "⚠️  agy not available"
    HAS_AGY=false
fi

echo ""

if [ "$HAS_CODEX" = false ] && [ "$HAS_AGY" = false ]; then
    echo "❌ No image generation backend available!"
    echo "   Please install either codex-cli or agy (Antigravity CLI)"
    exit 1
fi

# Test 2: Check test files
echo "Test 2: Checking test files..."
echo ""

if [ -f "$TEST_PROMPT" ]; then
    echo "✅ Test prompt file exists: $TEST_PROMPT"
else
    echo "❌ Test prompt file not found: $TEST_PROMPT"
    exit 1
fi

if [ -f "$SCRIPT_DIR/generate-image.js" ]; then
    echo "✅ Generator script exists"
else
    echo "❌ Generator script not found"
    exit 1
fi

echo ""

# Test 3: Test with auto-detect
echo "Test 3: Running with auto-detect..."
echo ""

node "$SCRIPT_DIR/generate-image.js" \
  --prompt-file "$TEST_PROMPT" \
  --output "$TEST_OUTPUT" \
  --aspect-ratio 16:9

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Test 3 passed: Auto-detect successful"
else
    echo ""
    echo "❌ Test 3 failed: Auto-detect failed"
    TEST3_FAILED=true
fi

echo ""

# Test 4: Test with explicit gemini if available
if [ "$HAS_AGY" = true ]; then
    echo "Test 4: Running with explicit gemini provider..."
    echo ""

    node "$SCRIPT_DIR/generate-image.js" \
      --provider gemini \
      --prompt-file "$TEST_PROMPT" \
      --output "/tmp/test-gemini-output.png"

    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Test 4 passed: Gemini generation successful"
    else
        echo ""
        echo "❌ Test 4 failed: Gemini generation failed"
    fi
else
    echo "Test 4: Skipped (agy not available)"
fi

echo ""

# Test 5: Test with explicit codex if available
if [ "$HAS_CODEX" = true ]; then
    echo "Test 5: Running with explicit codex provider..."
    echo ""

    node "$SCRIPT_DIR/generate-image.js" \
      --provider codex \
      --prompt-file "$TEST_PROMPT" \
      --output "/tmp/test-codex-output.png"

    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Test 5 passed: Codex generation successful"
    else
        echo ""
        echo "⚠️  Test 5 failed: Codex generation failed (may need config fix)"
    fi
else
    echo "Test 5: Skipped (codex not available)"
fi

echo ""
echo "================================"
echo "🎉 Testing complete!"
echo ""
echo "Generated files (if successful):"
ls -lh /tmp/test-*.png 2>/dev/null || echo "No images generated"

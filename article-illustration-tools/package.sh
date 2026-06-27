#!/bin/bash

# Package article-illustration-tools skill

SKILL_NAME="article-illustration-tools"
VERSION="1.0.0"
OUTPUT_DIR="dist"
PACKAGE_NAME="${SKILL_NAME}-${VERSION}.tar.gz"

echo "📦 Packaging ${SKILL_NAME} v${VERSION}"
echo "================================"
echo ""

# Clean previous builds
if [ -d "$OUTPUT_DIR" ]; then
    echo "Cleaning previous build..."
    rm -rf "$OUTPUT_DIR"
fi

mkdir -p "$OUTPUT_DIR"

# Create temporary directory for packaging
TEMP_DIR=$(mktemp -d)
PACKAGE_DIR="$TEMP_DIR/$SKILL_NAME"
mkdir -p "$PACKAGE_DIR"

echo "Creating package structure..."

# Copy files
cp SKILL.md "$PACKAGE_DIR/"
cp README.md "$PACKAGE_DIR/"
cp skill.json "$PACKAGE_DIR/"

# Copy scripts
mkdir -p "$PACKAGE_DIR/scripts"
cp scripts/generate-image.js "$PACKAGE_DIR/scripts/"
cp scripts/README.md "$PACKAGE_DIR/scripts/"
cp scripts/test-prompt.md "$PACKAGE_DIR/scripts/"
cp scripts/test.sh "$PACKAGE_DIR/scripts/"

# Copy references
mkdir -p "$PACKAGE_DIR/references"
cp references/description-optimization.md "$PACKAGE_DIR/references/"

# Copy evals (optional, for documentation)
mkdir -p "$PACKAGE_DIR/evals"
cp evals/evals.json "$PACKAGE_DIR/evals/"
cp evals/test-article-1.md "$PACKAGE_DIR/evals/"
cp evals/test-article-2.md "$PACKAGE_DIR/evals/"

echo "Creating tarball..."
cd "$TEMP_DIR"
tar -czf "$PACKAGE_NAME" "$SKILL_NAME"

# Move to output directory
mv "$PACKAGE_NAME" "$OLDPWD/$OUTPUT_DIR/"

echo ""
echo "✅ Package created: $OUTPUT_DIR/$PACKAGE_NAME"

# Generate checksum
cd "$OLDPWD"
shasum -a 256 "$OUTPUT_DIR/$PACKAGE_NAME" > "$OUTPUT_DIR/$PACKAGE_NAME.sha256"

echo "✅ Checksum created: $OUTPUT_DIR/$PACKAGE_NAME.sha256"
echo ""

# Show package contents
echo "Package contents:"
tar -tzf "$OUTPUT_DIR/$PACKAGE_NAME" | head -20
echo ""

# Show package size
PACKAGE_SIZE=$(du -h "$OUTPUT_DIR/$PACKAGE_NAME" | cut -f1)
echo "Package size: $PACKAGE_SIZE"

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo "================================"
echo "🎉 Packaging complete!"
echo ""
echo "To install:"
echo "  tar -xzf $OUTPUT_DIR/$PACKAGE_NAME -C ~/.claude/skills/"
echo ""
echo "Or manually:"
echo "  mkdir -p ~/.claude/skills/$SKILL_NAME"
echo "  tar -xzf $OUTPUT_DIR/$PACKAGE_NAME -C ~/.claude/skills/ --strip-components=1"

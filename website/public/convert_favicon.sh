#!/bin/bash

# Favicon Conversion Script
# Converts vibethon.jpg to various favicon formats

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Input and output paths
INPUT_IMAGE="vibethon.jpg"
OUTPUT_DIR="."

echo -e "${YELLOW}🚀 Starting favicon conversion...${NC}"

# Check if input image exists
if [ ! -f "$INPUT_IMAGE" ]; then
    echo -e "${RED}❌ Error: $INPUT_IMAGE not found!${NC}"
    exit 1
fi


echo -e "${GREEN}✅ Input image found: $INPUT_IMAGE${NC}"
echo -e "${GREEN}✅ ImageMagick detected${NC}"

# Create favicon.ico (multiple sizes in one file)
echo -e "${YELLOW}📦 Creating favicon.ico with multiple sizes...${NC}"
convert "$INPUT_IMAGE" \
    -resize 16x16 \
    -resize 32x32 \
    -resize 48x48 \
    -resize 64x64 \
    -resize 128x128 \
    "$OUTPUT_DIR/favicon.ico"

# Create individual PNG files for different purposes
echo -e "${YELLOW}🖼️  Creating individual PNG favicons...${NC}"

# Standard favicon sizes
convert "$INPUT_IMAGE" -resize 16x16 "$OUTPUT_DIR/favicon-16x16.png"
convert "$INPUT_IMAGE" -resize 32x32 "$OUTPUT_DIR/favicon-32x32.png"
convert "$INPUT_IMAGE" -resize 48x48 "$OUTPUT_DIR/favicon-48x48.png"
convert "$INPUT_IMAGE" -resize 96x96 "$OUTPUT_DIR/favicon-96x96.png"

# Apple Touch Icon (for iOS devices)
convert "$INPUT_IMAGE" -resize 180x180 "$OUTPUT_DIR/apple-touch-icon.png"

# Android Chrome icons
convert "$INPUT_IMAGE" -resize 192x192 "$OUTPUT_DIR/android-chrome-192x192.png"
convert "$INPUT_IMAGE" -resize 512x512 "$OUTPUT_DIR/android-chrome-512x512.png"

# Microsoft Tile icon
convert "$INPUT_IMAGE" -resize 150x150 "$OUTPUT_DIR/mstile-150x150.png"

echo -e "${GREEN}✅ Favicon conversion completed!${NC}"
echo ""
echo -e "${YELLOW}📋 Generated files:${NC}"
echo "  • favicon.ico (multi-size ICO file)"
echo "  • favicon-16x16.png"
echo "  • favicon-32x32.png" 
echo "  • favicon-48x48.png"
echo "  • favicon-96x96.png"
echo "  • apple-touch-icon.png (180x180)"
echo "  • android-chrome-192x192.png"
echo "  • android-chrome-512x512.png"
echo "  • mstile-150x150.png"
echo ""
echo -e "${YELLOW}💡 HTML usage examples:${NC}"
echo '<link rel="icon" type="image/x-icon" href="/favicon.ico">'
echo '<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">'
echo '<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">'
echo '<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">'
echo '<link rel="manifest" href="/site.webmanifest">'
echo ""
echo -e "${GREEN}🎉 All done! Your favicons are ready to use.${NC}" 
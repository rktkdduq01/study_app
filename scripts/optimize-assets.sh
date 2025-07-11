#!/bin/bash

# Asset Optimization and CDN Management Script
# Usage: ./scripts/optimize-assets.sh [command] [options]
# Example: ./scripts/optimize-assets.sh build --env production

set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_DIR="$PROJECT_ROOT/backend"
ASSETS_OUTPUT="$PROJECT_ROOT/dist"
LOG_DIR="$PROJECT_ROOT/logs/optimization"

# Command and options
COMMAND=${1:-build}
ENVIRONMENT=${2:-development}
FORCE=${3:-false}

# Logging
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/asset-optimization-$(date +%Y%m%d_%H%M%S).log"

log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

log "${BLUE}🚀 Asset Optimization Script${NC}"
log "${BLUE}Command: $COMMAND${NC}"
log "${BLUE}Environment: $ENVIRONMENT${NC}"
log "${BLUE}Log File: $LOG_FILE${NC}"
log ""

# Load environment configuration
load_environment() {
    if [ -f "$PROJECT_ROOT/scripts/load-env.sh" ]; then
        source "$PROJECT_ROOT/scripts/load-env.sh" "$ENVIRONMENT"
    fi
    
    # Set optimization flags based on environment
    case $ENVIRONMENT in
        "production")
            OPTIMIZE_IMAGES=true
            COMPRESS_ASSETS=true
            GENERATE_SOURCE_MAPS=false
            MINIFY_CODE=true
            ENABLE_CDN=true
            ;;
        "staging")
            OPTIMIZE_IMAGES=true
            COMPRESS_ASSETS=true
            GENERATE_SOURCE_MAPS=true
            MINIFY_CODE=true
            ENABLE_CDN=true
            ;;
        "development")
            OPTIMIZE_IMAGES=false
            COMPRESS_ASSETS=false
            GENERATE_SOURCE_MAPS=true
            MINIFY_CODE=false
            ENABLE_CDN=false
            ;;
    esac
}

# Build frontend assets
build_frontend() {
    log "${YELLOW}📦 Building Frontend Assets${NC}"
    
    if [ ! -d "$FRONTEND_DIR" ]; then
        log "${RED}❌ Frontend directory not found: $FRONTEND_DIR${NC}"
        return 1
    fi
    
    cd "$FRONTEND_DIR"
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ] || [ "$FORCE" = "--force" ]; then
        log "Installing frontend dependencies..."
        npm ci --silent
    fi
    
    # Build assets
    log "Building frontend assets for $ENVIRONMENT..."
    
    if [ "$ENVIRONMENT" = "production" ]; then
        # Production build with optimizations
        VITE_BUILD_TARGET=production \
        VITE_MINIFY=true \
        VITE_SOURCE_MAP=false \
        npm run build -- --mode production >> "$LOG_FILE" 2>&1
    elif [ "$ENVIRONMENT" = "staging" ]; then
        # Staging build
        VITE_BUILD_TARGET=staging \
        VITE_MINIFY=true \
        VITE_SOURCE_MAP=true \
        npm run build -- --mode staging >> "$LOG_FILE" 2>&1
    else
        # Development build
        npm run build -- --mode development >> "$LOG_FILE" 2>&1
    fi
    
    if [ $? -eq 0 ]; then
        log "${GREEN}✅ Frontend build completed${NC}"
    else
        log "${RED}❌ Frontend build failed${NC}"
        return 1
    fi
    
    cd "$PROJECT_ROOT"
}

# Optimize images
optimize_images() {
    log "${YELLOW}🖼️  Optimizing Images${NC}"
    
    if [ "$OPTIMIZE_IMAGES" != "true" ]; then
        log "Image optimization disabled for $ENVIRONMENT"
        return 0
    fi
    
    # Find image optimization tools
    IMAGEMIN_AVAILABLE=false
    SHARP_AVAILABLE=false
    
    if command -v imagemin &> /dev/null; then
        IMAGEMIN_AVAILABLE=true
    fi
    
    if command -v sharp &> /dev/null; then
        SHARP_AVAILABLE=true
    fi
    
    # Optimize with available tools
    if [ "$IMAGEMIN_AVAILABLE" = "true" ]; then
        log "Using imagemin for optimization..."
        
        # Create optimization script
        cat > /tmp/optimize_images.js << EOF
const imagemin = require('imagemin');
const imageminMozjpeg = require('imagemin-mozjpeg');
const imageminPngquant = require('imagemin-pngquant');
const imageminSvgo = require('imagemin-svgo');

(async () => {
    const files = await imagemin(['$ASSETS_OUTPUT/**/*.{jpg,jpeg,png,svg}'], {
        destination: '$ASSETS_OUTPUT/optimized',
        plugins: [
            imageminMozjpeg({quality: 85}),
            imageminPngquant({quality: [0.6, 0.8]}),
            imageminSvgo({
                plugins: [
                    {removeViewBox: false},
                    {cleanupIDs: false}
                ]
            })
        ]
    });
    
    console.log('Optimized', files.length, 'images');
})();
EOF
        
        node /tmp/optimize_images.js >> "$LOG_FILE" 2>&1
        rm -f /tmp/optimize_images.js
        
    elif [ "$SHARP_AVAILABLE" = "true" ]; then
        log "Using sharp for optimization..."
        
        # Use sharp for basic optimization
        find "$ASSETS_OUTPUT" -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" | while read -r img; do
            if [ -f "$img" ]; then
                sharp "$img" --quality 85 --output "${img%.???}_optimized.${img##*.}" >> "$LOG_FILE" 2>&1
                mv "${img%.???}_optimized.${img##*.}" "$img"
            fi
        done
        
    else
        log "${YELLOW}⚠️  No image optimization tools found. Install imagemin or sharp for better optimization.${NC}"
    fi
    
    log "${GREEN}✅ Image optimization completed${NC}"
}

# Compress assets
compress_assets() {
    log "${YELLOW}🗜️  Compressing Assets${NC}"
    
    if [ "$COMPRESS_ASSETS" != "true" ]; then
        log "Asset compression disabled for $ENVIRONMENT"
        return 0
    fi
    
    # Create compressed versions of text assets
    find "$ASSETS_OUTPUT" -type f \( -name "*.css" -o -name "*.js" -o -name "*.html" -o -name "*.svg" -o -name "*.json" \) | while read -r file; do
        if [ -f "$file" ]; then
            # Gzip compression
            gzip -c "$file" > "${file}.gz"
            
            # Brotli compression (if available)
            if command -v brotli &> /dev/null; then
                brotli -c "$file" > "${file}.br"
            fi
            
            log "Compressed: $(basename "$file")"
        fi
    done
    
    log "${GREEN}✅ Asset compression completed${NC}"
}

# Generate asset manifest
generate_manifest() {
    log "${YELLOW}📋 Generating Asset Manifest${NC}"
    
    cd "$BACKEND_DIR"
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d "venv_backend" ]; then
        source venv_backend/bin/activate
    fi
    
    # Generate manifest using Python script
    python << EOF
import sys
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.getcwd())

try:
    from app.core.cdn_optimizer import asset_optimizer, initialize_asset_optimization
    import asyncio
    
    async def generate_manifest():
        print("Initializing asset optimization...")
        await initialize_asset_optimization()
        
        print("Generating asset manifest...")
        manifest = await asset_optimizer.generate_asset_manifest()
        
        # Write manifest to file
        manifest_path = "../dist/asset-manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"Asset manifest written to: {manifest_path}")
        print(f"Total assets: {len(manifest.get('assets', {}))}")
        
        # Generate optimization report
        stats = asset_optimizer.get_optimization_stats()
        report_path = "../dist/optimization-report.json"
        with open(report_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"Optimization report written to: {report_path}")
        return True
    
    # Run async function
    success = asyncio.run(generate_manifest())
    sys.exit(0 if success else 1)
    
except ImportError as e:
    print(f"❌ Failed to import asset optimization modules: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Manifest generation failed: {e}")
    sys.exit(1)
EOF

    if [ $? -eq 0 ]; then
        log "${GREEN}✅ Asset manifest generated${NC}"
    else
        log "${RED}❌ Asset manifest generation failed${NC}"
        return 1
    fi
    
    cd "$PROJECT_ROOT"
}

# Upload to CDN
upload_to_cdn() {
    log "${YELLOW}☁️  Uploading to CDN${NC}"
    
    if [ "$ENABLE_CDN" != "true" ]; then
        log "CDN upload disabled for $ENVIRONMENT"
        return 0
    fi
    
    # This would integrate with actual CDN services
    # For now, simulate the upload process
    
    case $CDN_PROVIDER in
        "cloudflare")
            upload_to_cloudflare
            ;;
        "aws")
            upload_to_aws_cloudfront
            ;;
        "azure")
            upload_to_azure_cdn
            ;;
        *)
            log "${YELLOW}⚠️  CDN provider not configured or not supported${NC}"
            ;;
    esac
}

# Upload to CloudFlare (placeholder)
upload_to_cloudflare() {
    log "Uploading to CloudFlare..."
    
    if [ -z "$CLOUDFLARE_API_TOKEN" ] || [ -z "$CLOUDFLARE_ZONE_ID" ]; then
        log "${RED}❌ CloudFlare credentials not configured${NC}"
        return 1
    fi
    
    # This would use CloudFlare API
    log "${YELLOW}📤 Would upload assets to CloudFlare CDN${NC}"
    log "Assets directory: $ASSETS_OUTPUT"
    log "Total files: $(find "$ASSETS_OUTPUT" -type f | wc -l)"
}

# Upload to AWS CloudFront (placeholder)
upload_to_aws_cloudfront() {
    log "Uploading to AWS CloudFront..."
    
    if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ] || [ -z "$AWS_S3_BUCKET" ]; then
        log "${RED}❌ AWS credentials not configured${NC}"
        return 1
    fi
    
    # This would use AWS CLI
    log "${YELLOW}📤 Would upload assets to AWS S3/CloudFront${NC}"
    log "S3 Bucket: $AWS_S3_BUCKET"
    log "Distribution: $AWS_CLOUDFRONT_DISTRIBUTION_ID"
}

# Invalidate CDN cache
invalidate_cdn_cache() {
    log "${YELLOW}🔄 Invalidating CDN Cache${NC}"
    
    if [ "$ENABLE_CDN" != "true" ]; then
        return 0
    fi
    
    case $CDN_PROVIDER in
        "cloudflare")
            # CloudFlare cache purge
            if [ -n "$CLOUDFLARE_API_TOKEN" ] && [ -n "$CLOUDFLARE_ZONE_ID" ]; then
                curl -X POST "https://api.cloudflare.com/client/v4/zones/$CLOUDFLARE_ZONE_ID/purge_cache" \
                     -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
                     -H "Content-Type: application/json" \
                     --data '{"purge_everything":true}' >> "$LOG_FILE" 2>&1
                
                if [ $? -eq 0 ]; then
                    log "${GREEN}✅ CloudFlare cache invalidated${NC}"
                else
                    log "${RED}❌ CloudFlare cache invalidation failed${NC}"
                fi
            fi
            ;;
        "aws")
            # AWS CloudFront invalidation
            if [ -n "$AWS_CLOUDFRONT_DISTRIBUTION_ID" ]; then
                aws cloudfront create-invalidation \
                    --distribution-id "$AWS_CLOUDFRONT_DISTRIBUTION_ID" \
                    --paths "/*" >> "$LOG_FILE" 2>&1
                
                if [ $? -eq 0 ]; then
                    log "${GREEN}✅ CloudFront cache invalidated${NC}"
                else
                    log "${RED}❌ CloudFront cache invalidation failed${NC}"
                fi
            fi
            ;;
    esac
}

# Performance analysis
analyze_performance() {
    log "${YELLOW}📊 Analyzing Performance${NC}"
    
    # Calculate asset sizes
    if [ -d "$ASSETS_OUTPUT" ]; then
        total_size=$(du -sb "$ASSETS_OUTPUT" | cut -f1)
        total_files=$(find "$ASSETS_OUTPUT" -type f | wc -l)
        
        # Calculate compression savings
        original_size=0
        compressed_size=0
        
        find "$ASSETS_OUTPUT" -name "*.gz" | while read -r gz_file; do
            original_file="${gz_file%.gz}"
            if [ -f "$original_file" ]; then
                orig_size=$(stat -f%z "$original_file" 2>/dev/null || stat -c%s "$original_file" 2>/dev/null || echo 0)
                comp_size=$(stat -f%z "$gz_file" 2>/dev/null || stat -c%s "$gz_file" 2>/dev/null || echo 0)
                
                original_size=$((original_size + orig_size))
                compressed_size=$((compressed_size + comp_size))
            fi
        done
        
        # Generate performance report
        cat > "$ASSETS_OUTPUT/performance-report.json" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "environment": "$ENVIRONMENT",
    "total_files": $total_files,
    "total_size_bytes": $total_size,
    "total_size_human": "$(numfmt --to=iec-i --suffix=B $total_size)",
    "compression": {
        "original_size": $original_size,
        "compressed_size": $compressed_size,
        "savings_bytes": $((original_size - compressed_size)),
        "savings_percent": $([ $original_size -gt 0 ] && echo "scale=2; ($original_size - $compressed_size) * 100 / $original_size" | bc || echo 0)
    },
    "optimizations": {
        "images_optimized": $(find "$ASSETS_OUTPUT" -name "*.jpg" -o -name "*.png" | wc -l),
        "css_minified": $(find "$ASSETS_OUTPUT" -name "*.css" | wc -l),
        "js_minified": $(find "$ASSETS_OUTPUT" -name "*.js" | wc -l),
        "gzip_files": $(find "$ASSETS_OUTPUT" -name "*.gz" | wc -l),
        "brotli_files": $(find "$ASSETS_OUTPUT" -name "*.br" | wc -l)
    }
}
EOF
        
        log "${GREEN}✅ Performance analysis completed${NC}"
        log "Total assets: $total_files"
        log "Total size: $(numfmt --to=iec-i --suffix=B $total_size)"
        
        if [ $original_size -gt 0 ]; then
            savings_percent=$(echo "scale=1; ($original_size - $compressed_size) * 100 / $original_size" | bc)
            log "Compression savings: ${savings_percent}%"
        fi
    fi
}

# Clean build artifacts
clean_build() {
    log "${YELLOW}🧹 Cleaning Build Artifacts${NC}"
    
    # Remove old builds
    if [ -d "$ASSETS_OUTPUT" ]; then
        rm -rf "$ASSETS_OUTPUT"
        log "Removed: $ASSETS_OUTPUT"
    fi
    
    # Clean frontend build
    if [ -d "$FRONTEND_DIR/dist" ]; then
        rm -rf "$FRONTEND_DIR/dist"
        log "Removed: $FRONTEND_DIR/dist"
    fi
    
    # Clean node_modules if force clean
    if [ "$FORCE" = "--force" ]; then
        if [ -d "$FRONTEND_DIR/node_modules" ]; then
            rm -rf "$FRONTEND_DIR/node_modules"
            log "Removed: $FRONTEND_DIR/node_modules"
        fi
    fi
    
    log "${GREEN}✅ Cleanup completed${NC}"
}

# Main execution
main() {
    load_environment
    
    case $COMMAND in
        "build")
            log "🚀 Starting full asset optimization pipeline..."
            build_frontend && \
            optimize_images && \
            compress_assets && \
            generate_manifest && \
            analyze_performance && \
            upload_to_cdn
            ;;
            
        "frontend")
            build_frontend
            ;;
            
        "optimize")
            optimize_images && \
            compress_assets
            ;;
            
        "manifest")
            generate_manifest
            ;;
            
        "upload")
            upload_to_cdn
            ;;
            
        "invalidate")
            invalidate_cdn_cache
            ;;
            
        "analyze")
            analyze_performance
            ;;
            
        "clean")
            clean_build
            ;;
            
        "help"|"-h"|"--help")
            cat << EOF

Asset Optimization Script

Usage: $0 [command] [environment] [options]

Commands:
  build        Full optimization pipeline (default)
  frontend     Build frontend assets only
  optimize     Optimize images and compress assets
  manifest     Generate asset manifest
  upload       Upload assets to CDN
  invalidate   Invalidate CDN cache
  analyze      Analyze performance metrics
  clean        Clean build artifacts
  help         Show this help message

Environments:
  development  Development build (minimal optimization)
  staging      Staging build (full optimization + source maps)
  production   Production build (maximum optimization)

Options:
  --force      Force clean rebuild

Examples:
  $0 build production
  $0 optimize staging
  $0 clean --force
  $0 upload production
  $0 invalidate

Environment Variables:
  CDN_PROVIDER              CDN service (cloudflare, aws, azure)
  CLOUDFLARE_API_TOKEN      CloudFlare API token
  CLOUDFLARE_ZONE_ID        CloudFlare zone ID
  AWS_ACCESS_KEY_ID         AWS access key
  AWS_SECRET_ACCESS_KEY     AWS secret key
  AWS_S3_BUCKET            S3 bucket for assets
  AWS_CLOUDFRONT_DISTRIBUTION_ID  CloudFront distribution ID

EOF
            ;;
            
        *)
            log "${RED}❌ Unknown command: $COMMAND${NC}"
            log "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Execute main function
if main; then
    log ""
    log "${GREEN}✅ Asset optimization completed successfully${NC}"
    log "${BLUE}📄 Log file: $LOG_FILE${NC}"
    exit 0
else
    log ""
    log "${RED}❌ Asset optimization failed${NC}"
    log "${BLUE}📄 Check log file: $LOG_FILE${NC}"
    exit 1
fi
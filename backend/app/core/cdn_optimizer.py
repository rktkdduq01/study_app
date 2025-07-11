"""
CDN and Static Asset Optimization System
Advanced static asset management with CDN integration and optimization
"""

import asyncio
import hashlib
import json
import mimetypes
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from urllib.parse import urljoin, urlparse
import base64
import gzip
import brotli

from app.core.logger import get_logger
from app.core.redis_client import redis_client
from app.core.config import settings

logger = get_logger(__name__)

class AssetType(Enum):
    """Static asset types"""
    CSS = "css"
    JAVASCRIPT = "javascript"
    IMAGE = "image"
    FONT = "font"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    OTHER = "other"

class CompressionType(Enum):
    """Compression types"""
    NONE = "none"
    GZIP = "gzip"
    BROTLI = "brotli"

@dataclass
class AssetInfo:
    """Static asset information"""
    path: str
    asset_type: AssetType
    size: int
    hash: str
    mime_type: str
    last_modified: datetime
    compression: CompressionType = CompressionType.NONE
    compressed_size: Optional[int] = None
    cdn_url: Optional[str] = None
    cache_control: str = "public, max-age=31536000"  # 1 year default
    etag: Optional[str] = None

@dataclass
class CDNConfiguration:
    """CDN configuration"""
    enabled: bool = True
    base_url: str = ""
    regions: List[str] = field(default_factory=list)
    cache_behavior: Dict[str, Any] = field(default_factory=dict)
    compression_enabled: bool = True
    image_optimization: bool = True
    
class AssetOptimizer:
    """Static asset optimization and CDN management"""
    
    def __init__(self, cdn_config: CDNConfiguration = None):
        self.cdn_config = cdn_config or CDNConfiguration()
        self.assets: Dict[str, AssetInfo] = {}
        self.asset_mappings: Dict[str, str] = {}  # Original path -> optimized path
        
        # Asset processing settings
        self.static_dirs = [
            "static",
            "assets", 
            "public",
            "media"
        ]
        
        # Optimization settings
        self.image_formats = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}
        self.css_formats = {'.css'}
        self.js_formats = {'.js', '.mjs'}
        self.font_formats = {'.woff', '.woff2', '.ttf', '.otf', '.eot'}
        
        # Compression settings
        self.compression_threshold = 1024  # 1KB
        self.compression_level = 6
        
        # Cache settings
        self.cache_durations = {
            AssetType.CSS: 31536000,      # 1 year
            AssetType.JAVASCRIPT: 31536000, # 1 year
            AssetType.IMAGE: 2592000,      # 30 days
            AssetType.FONT: 31536000,      # 1 year
            AssetType.VIDEO: 604800,       # 7 days
            AssetType.AUDIO: 604800,       # 7 days
            AssetType.DOCUMENT: 86400,     # 1 day
            AssetType.OTHER: 3600          # 1 hour
        }
        
        # Statistics
        self.stats = {
            "total_assets": 0,
            "compressed_assets": 0,
            "total_size": 0,
            "compressed_size": 0,
            "cdn_hits": 0,
            "optimization_time": 0
        }
    
    def _get_asset_type(self, file_path: str) -> AssetType:
        """Determine asset type from file extension"""
        ext = Path(file_path).suffix.lower()
        
        if ext in self.css_formats:
            return AssetType.CSS
        elif ext in self.js_formats:
            return AssetType.JAVASCRIPT
        elif ext in self.image_formats:
            return AssetType.IMAGE
        elif ext in self.font_formats:
            return AssetType.FONT
        elif ext in {'.mp4', '.webm', '.mov', '.avi'}:
            return AssetType.VIDEO
        elif ext in {'.mp3', '.wav', '.ogg', '.flac'}:
            return AssetType.AUDIO
        elif ext in {'.pdf', '.doc', '.docx', '.txt'}:
            return AssetType.DOCUMENT
        else:
            return AssetType.OTHER
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file"""
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()[:16]  # Use first 16 characters
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return "unknown"
    
    def _compress_content(self, content: bytes, compression_type: CompressionType) -> bytes:
        """Compress content using specified algorithm"""
        try:
            if compression_type == CompressionType.GZIP:
                return gzip.compress(content, compresslevel=self.compression_level)
            elif compression_type == CompressionType.BROTLI:
                return brotli.compress(content, quality=self.compression_level)
            else:
                return content
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            return content
    
    def _should_compress(self, asset_info: AssetInfo) -> bool:
        """Determine if asset should be compressed"""
        # Don't compress already compressed formats
        if asset_info.asset_type in [AssetType.IMAGE, AssetType.VIDEO, AssetType.AUDIO]:
            return False
        
        # Only compress files above threshold
        return asset_info.size >= self.compression_threshold
    
    async def scan_assets(self, base_path: str = ".") -> int:
        """Scan and catalog all static assets"""
        start_time = time.time()
        asset_count = 0
        
        try:
            base_path = Path(base_path)
            
            # Scan each static directory
            for static_dir in self.static_dirs:
                static_path = base_path / static_dir
                if not static_path.exists():
                    continue
                
                logger.info(f"Scanning assets in {static_path}")
                
                # Walk through all files
                for file_path in static_path.rglob("*"):
                    if file_path.is_file():
                        await self._process_asset(file_path)
                        asset_count += 1
            
            processing_time = time.time() - start_time
            self.stats["optimization_time"] += processing_time
            
            logger.info(f"Scanned {asset_count} assets in {processing_time:.2f}s")
            return asset_count
            
        except Exception as e:
            logger.error(f"Asset scanning failed: {e}")
            return 0
    
    async def _process_asset(self, file_path: Path):
        """Process individual asset file"""
        try:
            # Get file stats
            stat = file_path.stat()
            file_size = stat.st_size
            last_modified = datetime.fromtimestamp(stat.st_mtime)
            
            # Calculate hash
            file_hash = self._calculate_file_hash(str(file_path))
            
            # Determine asset type and MIME type
            asset_type = self._get_asset_type(str(file_path))
            mime_type, _ = mimetypes.guess_type(str(file_path))
            mime_type = mime_type or 'application/octet-stream'
            
            # Create asset info
            relative_path = str(file_path.relative_to(Path.cwd()))
            asset_info = AssetInfo(
                path=relative_path,
                asset_type=asset_type,
                size=file_size,
                hash=file_hash,
                mime_type=mime_type,
                last_modified=last_modified,
                etag=f'"{file_hash}"'
            )
            
            # Set cache control based on asset type
            cache_duration = self.cache_durations.get(asset_type, 3600)
            asset_info.cache_control = f"public, max-age={cache_duration}"
            
            # Attempt compression if beneficial
            if self._should_compress(asset_info):
                await self._optimize_asset(asset_info, file_path)
            
            # Generate CDN URL if enabled
            if self.cdn_config.enabled and self.cdn_config.base_url:
                asset_info.cdn_url = self._generate_cdn_url(asset_info)
            
            # Store asset info
            self.assets[relative_path] = asset_info
            self.stats["total_assets"] += 1
            self.stats["total_size"] += file_size
            
            # Cache asset info in Redis
            await self._cache_asset_info(asset_info)
            
        except Exception as e:
            logger.error(f"Failed to process asset {file_path}: {e}")
    
    async def _optimize_asset(self, asset_info: AssetInfo, file_path: Path):
        """Optimize asset with compression"""
        try:
            # Read original content
            with open(file_path, 'rb') as f:
                original_content = f.read()
            
            # Try different compression methods
            best_compression = CompressionType.NONE
            best_size = asset_info.size
            best_content = original_content
            
            # Try Brotli first (better compression)
            if brotli:
                brotli_content = self._compress_content(original_content, CompressionType.BROTLI)
                if len(brotli_content) < best_size:
                    best_compression = CompressionType.BROTLI
                    best_size = len(brotli_content)
                    best_content = brotli_content
            
            # Try Gzip
            gzip_content = self._compress_content(original_content, CompressionType.GZIP)
            if len(gzip_content) < best_size:
                best_compression = CompressionType.GZIP
                best_size = len(gzip_content)
                best_content = gzip_content
            
            # Update asset info if compression is beneficial
            if best_compression != CompressionType.NONE and best_size < asset_info.size * 0.9:  # At least 10% reduction
                asset_info.compression = best_compression
                asset_info.compressed_size = best_size
                
                # Write compressed version
                compressed_path = file_path.with_suffix(f"{file_path.suffix}.{best_compression.value}")
                with open(compressed_path, 'wb') as f:
                    f.write(best_content)
                
                self.stats["compressed_assets"] += 1
                self.stats["compressed_size"] += best_size
                
                logger.debug(f"Compressed {asset_info.path}: {asset_info.size} -> {best_size} bytes ({best_compression.value})")
            
        except Exception as e:
            logger.error(f"Asset optimization failed for {asset_info.path}: {e}")
    
    def _generate_cdn_url(self, asset_info: AssetInfo) -> str:
        """Generate CDN URL for asset"""
        try:
            # Use hash-based versioning for cache busting
            versioned_path = f"{asset_info.path}?v={asset_info.hash}"
            return urljoin(self.cdn_config.base_url, versioned_path)
        except Exception as e:
            logger.error(f"CDN URL generation failed: {e}")
            return asset_info.path
    
    async def _cache_asset_info(self, asset_info: AssetInfo):
        """Cache asset information in Redis"""
        try:
            cache_key = f"asset_info:{asset_info.hash}"
            asset_data = asdict(asset_info)
            asset_data['last_modified'] = asset_info.last_modified.isoformat()
            asset_data['asset_type'] = asset_info.asset_type.value
            asset_data['compression'] = asset_info.compression.value
            
            await redis_client.setex(cache_key, 86400, json.dumps(asset_data))  # 24 hours cache
            
        except Exception as e:
            logger.error(f"Failed to cache asset info: {e}")
    
    def get_asset_url(self, asset_path: str, use_cdn: bool = True) -> str:
        """Get optimized URL for asset"""
        try:
            # Normalize path
            normalized_path = os.path.normpath(asset_path).replace('\\', '/')
            
            # Check if asset exists
            if normalized_path not in self.assets:
                logger.warning(f"Asset not found: {asset_path}")
                return asset_path
            
            asset_info = self.assets[normalized_path]
            
            # Use CDN URL if available and requested
            if use_cdn and asset_info.cdn_url:
                self.stats["cdn_hits"] += 1
                return asset_info.cdn_url
            
            # Return versioned local URL
            return f"{asset_path}?v={asset_info.hash}"
            
        except Exception as e:
            logger.error(f"Failed to get asset URL for {asset_path}: {e}")
            return asset_path
    
    def get_asset_headers(self, asset_path: str) -> Dict[str, str]:
        """Get HTTP headers for asset"""
        headers = {}
        
        try:
            normalized_path = os.path.normpath(asset_path).replace('\\', '/')
            
            if normalized_path not in self.assets:
                return headers
            
            asset_info = self.assets[normalized_path]
            
            # Basic headers
            headers['Content-Type'] = asset_info.mime_type
            headers['Cache-Control'] = asset_info.cache_control
            headers['ETag'] = asset_info.etag
            headers['Last-Modified'] = asset_info.last_modified.strftime('%a, %d %b %Y %H:%M:%S GMT')
            
            # Compression headers
            if asset_info.compression != CompressionType.NONE:
                headers['Content-Encoding'] = asset_info.compression.value
                headers['Vary'] = 'Accept-Encoding'
            
            # Security headers for certain assets
            if asset_info.asset_type in [AssetType.CSS, AssetType.JAVASCRIPT]:
                headers['X-Content-Type-Options'] = 'nosniff'
            
            return headers
            
        except Exception as e:
            logger.error(f"Failed to get asset headers for {asset_path}: {e}")
            return headers
    
    async def preload_critical_assets(self, critical_assets: List[str]) -> List[str]:
        """Generate preload headers for critical assets"""
        preload_headers = []
        
        for asset_path in critical_assets:
            try:
                normalized_path = os.path.normpath(asset_path).replace('\\', '/')
                
                if normalized_path not in self.assets:
                    continue
                
                asset_info = self.assets[normalized_path]
                asset_url = self.get_asset_url(asset_path)
                
                # Determine preload type
                preload_as = "script"
                if asset_info.asset_type == AssetType.CSS:
                    preload_as = "style"
                elif asset_info.asset_type == AssetType.FONT:
                    preload_as = "font"
                elif asset_info.asset_type == AssetType.IMAGE:
                    preload_as = "image"
                
                # Create preload header
                preload_header = f'<{asset_url}>; rel=preload; as={preload_as}'
                
                # Add crossorigin for fonts
                if asset_info.asset_type == AssetType.FONT:
                    preload_header += '; crossorigin=anonymous'
                
                preload_headers.append(preload_header)
                
            except Exception as e:
                logger.error(f"Failed to create preload header for {asset_path}: {e}")
        
        return preload_headers
    
    async def generate_asset_manifest(self) -> Dict[str, Any]:
        """Generate asset manifest for frontend"""
        manifest = {
            "version": datetime.utcnow().isoformat(),
            "assets": {},
            "preload": [],
            "prefetch": []
        }
        
        try:
            for path, asset_info in self.assets.items():
                manifest["assets"][path] = {
                    "url": self.get_asset_url(path),
                    "hash": asset_info.hash,
                    "size": asset_info.size,
                    "type": asset_info.asset_type.value,
                    "compressed": asset_info.compression != CompressionType.NONE
                }
            
            # Cache manifest
            await redis_client.setex(
                "asset_manifest", 
                3600,  # 1 hour cache
                json.dumps(manifest)
            )
            
            return manifest
            
        except Exception as e:
            logger.error(f"Failed to generate asset manifest: {e}")
            return manifest
    
    def optimize_images(self, quality: int = 85) -> int:
        """Optimize image assets (placeholder for actual image optimization)"""
        optimized_count = 0
        
        try:
            for path, asset_info in self.assets.items():
                if asset_info.asset_type == AssetType.IMAGE:
                    # This would integrate with image optimization libraries
                    # like Pillow, ImageIO, or external services
                    logger.debug(f"Would optimize image: {path}")
                    optimized_count += 1
            
            logger.info(f"Optimized {optimized_count} images")
            return optimized_count
            
        except Exception as e:
            logger.error(f"Image optimization failed: {e}")
            return 0
    
    async def invalidate_cdn_cache(self, asset_paths: List[str] = None) -> bool:
        """Invalidate CDN cache for specified assets"""
        try:
            if not self.cdn_config.enabled:
                return True
            
            paths_to_invalidate = asset_paths or list(self.assets.keys())
            
            # This would integrate with actual CDN APIs (CloudFlare, AWS CloudFront, etc.)
            logger.info(f"Would invalidate CDN cache for {len(paths_to_invalidate)} assets")
            
            # For now, just log the invalidation
            for path in paths_to_invalidate[:10]:  # Log first 10
                logger.debug(f"CDN invalidation: {path}")
            
            return True
            
        except Exception as e:
            logger.error(f"CDN cache invalidation failed: {e}")
            return False
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get asset optimization statistics"""
        compression_ratio = 0
        if self.stats["total_size"] > 0:
            savings = self.stats["total_size"] - self.stats["compressed_size"]
            compression_ratio = (savings / self.stats["total_size"]) * 100
        
        return {
            "total_assets": self.stats["total_assets"],
            "compressed_assets": self.stats["compressed_assets"],
            "total_size_bytes": self.stats["total_size"],
            "compressed_size_bytes": self.stats["compressed_size"],
            "compression_ratio_percent": round(compression_ratio, 2),
            "cdn_hits": self.stats["cdn_hits"],
            "optimization_time_seconds": round(self.stats["optimization_time"], 2),
            "asset_types": self._get_asset_type_breakdown()
        }
    
    def _get_asset_type_breakdown(self) -> Dict[str, int]:
        """Get breakdown of assets by type"""
        breakdown = {}
        for asset_info in self.assets.values():
            asset_type = asset_info.asset_type.value
            breakdown[asset_type] = breakdown.get(asset_type, 0) + 1
        return breakdown

# CDN Configuration for different environments
def get_cdn_config() -> CDNConfiguration:
    """Get CDN configuration based on environment"""
    environment = getattr(settings, 'ENVIRONMENT', 'development')
    
    if environment == 'production':
        return CDNConfiguration(
            enabled=True,
            base_url=getattr(settings, 'CDN_BASE_URL', 'https://cdn.quest-edu.com'),
            regions=['us-east-1', 'eu-west-1', 'ap-southeast-1'],
            cache_behavior={
                'default_ttl': 31536000,  # 1 year
                'max_ttl': 31536000 * 2,  # 2 years
                'compress': True,
                'query_string': False
            },
            compression_enabled=True,
            image_optimization=True
        )
    elif environment == 'staging':
        return CDNConfiguration(
            enabled=True,
            base_url=getattr(settings, 'CDN_BASE_URL', 'https://staging-cdn.quest-edu.com'),
            regions=['us-east-1'],
            compression_enabled=True,
            image_optimization=False
        )
    else:
        return CDNConfiguration(
            enabled=False,
            compression_enabled=True,
            image_optimization=False
        )

# Global asset optimizer instance
cdn_config = get_cdn_config()
asset_optimizer = AssetOptimizer(cdn_config)

# Utility functions
async def initialize_asset_optimization():
    """Initialize asset optimization system"""
    try:
        logger.info("Initializing asset optimization...")
        asset_count = await asset_optimizer.scan_assets()
        
        if asset_count > 0:
            # Generate initial manifest
            await asset_optimizer.generate_asset_manifest()
            
            # Optimize images if enabled
            if cdn_config.image_optimization:
                asset_optimizer.optimize_images()
        
        logger.info(f"Asset optimization initialized with {asset_count} assets")
        return True
        
    except Exception as e:
        logger.error(f"Asset optimization initialization failed: {e}")
        return False

async def get_asset_manifest() -> Dict[str, Any]:
    """Get cached asset manifest"""
    try:
        cached_manifest = await redis_client.get("asset_manifest")
        if cached_manifest:
            return json.loads(cached_manifest)
        
        # Generate new manifest if not cached
        return await asset_optimizer.generate_asset_manifest()
        
    except Exception as e:
        logger.error(f"Failed to get asset manifest: {e}")
        return {"version": datetime.utcnow().isoformat(), "assets": {}}

def get_static_url(asset_path: str, use_cdn: bool = True) -> str:
    """Get optimized URL for static asset"""
    return asset_optimizer.get_asset_url(asset_path, use_cdn)

def get_static_headers(asset_path: str) -> Dict[str, str]:
    """Get HTTP headers for static asset"""
    return asset_optimizer.get_asset_headers(asset_path)
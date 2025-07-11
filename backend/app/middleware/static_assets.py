"""
Static Assets Middleware
High-performance static asset serving with optimization and caching
"""

import asyncio
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import mimetypes

from fastapi import Request, Response
from fastapi.responses import FileResponse, Response as FastAPIResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from app.core.logger import get_logger
from app.core.cdn_optimizer import asset_optimizer, get_static_url, get_static_headers
from app.core.redis_client import redis_client

logger = get_logger(__name__)

class StaticAssetsMiddleware(BaseHTTPMiddleware):
    """High-performance static assets middleware"""
    
    def __init__(self, app, static_url_path: str = "/static", static_directory: str = "static"):
        super().__init__(app)
        self.static_url_path = static_url_path.rstrip('/')
        self.static_directory = Path(static_directory)
        
        # Performance settings
        self.enable_etag = True
        self.enable_last_modified = True
        self.enable_compression = True
        self.enable_range_requests = True
        self.max_age = 31536000  # 1 year default
        
        # Cache settings
        self.memory_cache = {}
        self.memory_cache_size = 100 * 1024 * 1024  # 100MB
        self.current_cache_size = 0
        
        # Statistics
        self.stats = {
            "requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "bytes_served": 0,
            "compression_hits": 0
        }
    
    async def dispatch(self, request: Request, call_next):
        """Handle static asset requests"""
        # Check if this is a static asset request
        if not request.url.path.startswith(self.static_url_path):
            return await call_next(request)
        
        start_time = time.time()
        self.stats["requests"] += 1
        
        try:
            # Extract relative path
            relative_path = request.url.path[len(self.static_url_path):].lstrip('/')
            if not relative_path:
                return await call_next(request)
            
            # Serve the static file
            response = await self._serve_static_file(request, relative_path)
            
            # Update statistics
            processing_time = time.time() - start_time
            if hasattr(response, 'headers') and 'content-length' in response.headers:
                self.stats["bytes_served"] += int(response.headers['content-length'])
            
            # Add performance headers
            response.headers["X-Static-Processing-Time"] = f"{processing_time:.3f}s"
            
            return response
            
        except Exception as e:
            logger.error(f"Static asset serving error: {e}")
            return await call_next(request)
    
    async def _serve_static_file(self, request: Request, relative_path: str) -> Response:
        """Serve static file with optimization"""
        try:
            # Construct file path
            file_path = self.static_directory / relative_path
            
            # Security check - prevent directory traversal
            try:
                file_path.resolve().relative_to(self.static_directory.resolve())
            except ValueError:
                return self._create_error_response(403, "Forbidden")
            
            # Check if file exists
            if not file_path.exists() or not file_path.is_file():
                return self._create_error_response(404, "Not Found")
            
            # Get file stats
            stat = file_path.stat()
            file_size = stat.st_size
            last_modified = datetime.fromtimestamp(stat.st_mtime)
            
            # Check conditional requests
            if self._check_not_modified(request, last_modified, str(file_path)):
                return self._create_not_modified_response(last_modified)
            
            # Handle range requests
            range_header = request.headers.get('range')
            if range_header and self.enable_range_requests:
                return await self._serve_range_request(file_path, range_header, last_modified)
            
            # Check memory cache first
            cache_key = f"static:{relative_path}:{stat.st_mtime}"
            cached_content = await self._get_from_cache(cache_key)
            
            if cached_content:
                self.stats["cache_hits"] += 1
                return self._create_response_from_cache(
                    cached_content, relative_path, last_modified
                )
            
            # Read and serve file
            self.stats["cache_misses"] += 1
            return await self._serve_file_content(file_path, relative_path, last_modified, cache_key)
            
        except Exception as e:
            logger.error(f"Error serving static file {relative_path}: {e}")
            return self._create_error_response(500, "Internal Server Error")
    
    def _check_not_modified(self, request: Request, last_modified: datetime, file_path: str) -> bool:
        """Check if file was modified since last request"""
        if not self.enable_etag and not self.enable_last_modified:
            return False
        
        # Check If-Modified-Since header
        if self.enable_last_modified:
            if_modified_since = request.headers.get('if-modified-since')
            if if_modified_since:
                try:
                    ims_date = datetime.strptime(if_modified_since, '%a, %d %b %Y %H:%M:%S GMT')
                    if last_modified.replace(microsecond=0) <= ims_date:
                        return True
                except ValueError:
                    pass
        
        # Check If-None-Match header (ETag)
        if self.enable_etag:
            if_none_match = request.headers.get('if-none-match')
            if if_none_match:
                etag = self._generate_etag(file_path, last_modified)
                if etag in if_none_match:
                    return True
        
        return False
    
    def _generate_etag(self, file_path: str, last_modified: datetime) -> str:
        """Generate ETag for file"""
        import hashlib
        content = f"{file_path}:{last_modified.timestamp()}"
        return f'"{hashlib.md5(content.encode()).hexdigest()}"'
    
    def _create_not_modified_response(self, last_modified: datetime) -> Response:
        """Create 304 Not Modified response"""
        response = Response(status_code=304)
        
        if self.enable_last_modified:
            response.headers["Last-Modified"] = last_modified.strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        response.headers["Cache-Control"] = f"public, max-age={self.max_age}"
        return response
    
    async def _serve_range_request(self, file_path: Path, range_header: str, 
                                 last_modified: datetime) -> Response:
        """Handle HTTP range requests for partial content"""
        try:
            # Parse range header
            range_match = range_header.replace('bytes=', '').split('-')
            if len(range_match) != 2:
                return self._create_error_response(416, "Range Not Satisfiable")
            
            start_str, end_str = range_match
            file_size = file_path.stat().st_size
            
            start = int(start_str) if start_str else 0
            end = int(end_str) if end_str else file_size - 1
            
            # Validate range
            if start >= file_size or end >= file_size or start > end:
                return self._create_error_response(416, "Range Not Satisfiable")
            
            # Read partial content
            with open(file_path, 'rb') as f:
                f.seek(start)
                content = f.read(end - start + 1)
            
            # Create partial content response
            response = Response(
                content=content,
                status_code=206,
                headers={
                    "Content-Range": f"bytes {start}-{end}/{file_size}",
                    "Content-Length": str(len(content)),
                    "Accept-Ranges": "bytes"
                }
            )
            
            self._add_common_headers(response, str(file_path), last_modified)
            return response
            
        except Exception as e:
            logger.error(f"Range request error: {e}")
            return self._create_error_response(416, "Range Not Satisfiable")
    
    async def _get_from_cache(self, cache_key: str) -> Optional[bytes]:
        """Get content from memory cache"""
        try:
            # Check memory cache first
            if cache_key in self.memory_cache:
                return self.memory_cache[cache_key]
            
            # Check Redis cache
            cached_data = await redis_client.get(f"static_cache:{cache_key}")
            if cached_data:
                return cached_data
            
            return None
            
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
            return None
    
    async def _serve_file_content(self, file_path: Path, relative_path: str, 
                                last_modified: datetime, cache_key: str) -> Response:
        """Serve file content with caching"""
        try:
            # Read file content
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Check if compression is beneficial
            compressed_content = None
            content_encoding = None
            
            if self.enable_compression and self._should_compress(file_path, len(content)):
                # Try compression
                compressed_content, content_encoding = await self._compress_content(content)
                if compressed_content and len(compressed_content) < len(content) * 0.9:
                    content = compressed_content
                    self.stats["compression_hits"] += 1
                else:
                    content_encoding = None
            
            # Cache content if it's not too large
            if len(content) < 1024 * 1024:  # Cache files smaller than 1MB
                await self._cache_content(cache_key, content)
            
            # Create response
            response = Response(content=content)
            
            # Add headers
            self._add_common_headers(response, str(file_path), last_modified)
            
            if content_encoding:
                response.headers["Content-Encoding"] = content_encoding
                response.headers["Vary"] = "Accept-Encoding"
            
            # Add optimized asset headers if available
            optimized_headers = get_static_headers(relative_path)
            for key, value in optimized_headers.items():
                response.headers[key] = value
            
            return response
            
        except Exception as e:
            logger.error(f"Error serving file content: {e}")
            return self._create_error_response(500, "Internal Server Error")
    
    def _should_compress(self, file_path: Path, content_size: int) -> bool:
        """Determine if content should be compressed"""
        # Only compress text-based files
        compressible_extensions = {'.css', '.js', '.html', '.xml', '.json', '.svg', '.txt'}
        if file_path.suffix.lower() not in compressible_extensions:
            return False
        
        # Only compress files larger than 1KB
        return content_size >= 1024
    
    async def _compress_content(self, content: bytes) -> Tuple[Optional[bytes], Optional[str]]:
        """Compress content using gzip"""
        try:
            import gzip
            compressed = gzip.compress(content, compresslevel=6)
            return compressed, "gzip"
        except Exception as e:
            logger.error(f"Compression error: {e}")
            return None, None
    
    async def _cache_content(self, cache_key: str, content: bytes):
        """Cache content in memory and Redis"""
        try:
            # Memory cache (with size limit)
            if self.current_cache_size + len(content) <= self.memory_cache_size:
                self.memory_cache[cache_key] = content
                self.current_cache_size += len(content)
            
            # Redis cache (with TTL)
            await redis_client.setex(f"static_cache:{cache_key}", 3600, content)  # 1 hour
            
        except Exception as e:
            logger.error(f"Caching error: {e}")
    
    def _create_response_from_cache(self, content: bytes, relative_path: str, 
                                  last_modified: datetime) -> Response:
        """Create response from cached content"""
        response = Response(content=content)
        
        # Add basic headers
        mime_type, _ = mimetypes.guess_type(relative_path)
        if mime_type:
            response.headers["Content-Type"] = mime_type
        
        self._add_common_headers(response, relative_path, last_modified)
        
        # Add optimized asset headers
        optimized_headers = get_static_headers(relative_path)
        for key, value in optimized_headers.items():
            response.headers[key] = value
        
        return response
    
    def _add_common_headers(self, response: Response, file_path: str, last_modified: datetime):
        """Add common headers to response"""
        # Cache headers
        response.headers["Cache-Control"] = f"public, max-age={self.max_age}"
        
        # Last-Modified header
        if self.enable_last_modified:
            response.headers["Last-Modified"] = last_modified.strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        # ETag header
        if self.enable_etag:
            response.headers["ETag"] = self._generate_etag(file_path, last_modified)
        
        # Content-Type header
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            response.headers["Content-Type"] = mime_type
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # CORS headers for assets
        if any(file_path.endswith(ext) for ext in ['.css', '.js', '.woff', '.woff2']):
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
            response.headers["Access-Control-Max-Age"] = "86400"
    
    def _create_error_response(self, status_code: int, message: str) -> Response:
        """Create error response"""
        return Response(
            content=message,
            status_code=status_code,
            headers={"Content-Type": "text/plain"}
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get middleware statistics"""
        cache_hit_rate = 0
        if self.stats["requests"] > 0:
            cache_hit_rate = (self.stats["cache_hits"] / self.stats["requests"]) * 100
        
        return {
            "requests": self.stats["requests"],
            "cache_hits": self.stats["cache_hits"],
            "cache_misses": self.stats["cache_misses"],
            "cache_hit_rate_percent": round(cache_hit_rate, 2),
            "bytes_served": self.stats["bytes_served"],
            "compression_hits": self.stats["compression_hits"],
            "memory_cache_size": self.current_cache_size,
            "memory_cache_entries": len(self.memory_cache)
        }

class AssetPreloadMiddleware(BaseHTTPMiddleware):
    """Middleware for adding asset preload headers"""
    
    def __init__(self, app, critical_assets: list = None):
        super().__init__(app)
        self.critical_assets = critical_assets or []
    
    async def dispatch(self, request: Request, call_next):
        """Add preload headers to HTML responses"""
        response = await call_next(request)
        
        # Only add preload headers to HTML responses
        if (response.headers.get('content-type', '').startswith('text/html') and 
            self.critical_assets):
            
            try:
                # Generate preload headers
                preload_headers = []
                for asset_path in self.critical_assets:
                    asset_url = get_static_url(asset_path)
                    
                    # Determine asset type
                    if asset_path.endswith('.css'):
                        preload_as = 'style'
                    elif asset_path.endswith('.js'):
                        preload_as = 'script'
                    elif asset_path.endswith(('.woff', '.woff2')):
                        preload_as = 'font'
                    elif asset_path.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                        preload_as = 'image'
                    else:
                        continue
                    
                    preload_header = f'<{asset_url}>; rel=preload; as={preload_as}'
                    
                    # Add crossorigin for fonts
                    if preload_as == 'font':
                        preload_header += '; crossorigin=anonymous'
                    
                    preload_headers.append(preload_header)
                
                # Add Link header
                if preload_headers:
                    response.headers["Link"] = ', '.join(preload_headers)
                    
            except Exception as e:
                logger.error(f"Preload header generation error: {e}")
        
        return response

# Global middleware instances
static_assets_middleware = StaticAssetsMiddleware
asset_preload_middleware = AssetPreloadMiddleware
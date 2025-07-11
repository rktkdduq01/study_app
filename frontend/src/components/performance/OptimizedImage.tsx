/**
 * Optimized image component with lazy loading and responsive images
 */
import React, { useState, useEffect, useRef } from 'react';
import { useLazyLoad } from '../../hooks/usePerformance';

interface OptimizedImageProps {
  src: string;
  alt: string;
  className?: string;
  width?: number;
  height?: number;
  loading?: 'lazy' | 'eager';
  placeholder?: string;
  srcSet?: string;
  sizes?: string;
  onLoad?: () => void;
  onError?: () => void;
  quality?: number;
  format?: 'webp' | 'jpeg' | 'png';
}

/**
 * OptimizedImage component with:
 * - Lazy loading with Intersection Observer
 * - Placeholder while loading
 * - Error handling with fallback
 * - WebP format with fallback
 * - Responsive images support
 * - Progressive loading
 */
export const OptimizedImage: React.FC<OptimizedImageProps> = ({
  src,
  alt,
  className = '',
  width,
  height,
  loading = 'lazy',
  placeholder = '/images/placeholder.svg',
  srcSet,
  sizes,
  onLoad,
  onError,
  quality = 85,
  format = 'webp'
}) => {
  const [imageSrc, setImageSrc] = useState<string>(placeholder);
  const [imageError, setImageError] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const { ref, isVisible } = useLazyLoad({ threshold: 0.01 });
  const imageRef = useRef<HTMLImageElement>(null);

  // Generate optimized image URLs
  const generateOptimizedUrl = (url: string, params: Record<string, any>) => {
    // This would integrate with your image CDN or optimization service
    const urlObj = new URL(url, window.location.origin);
    Object.entries(params).forEach(([key, value]) => {
      urlObj.searchParams.set(key, String(value));
    });
    return urlObj.toString();
  };

  // Generate srcSet for responsive images
  const generateSrcSet = () => {
    if (srcSet) return srcSet;
    
    const widths = [320, 640, 768, 1024, 1280, 1920];
    return widths
      .map(w => {
        const optimizedUrl = generateOptimizedUrl(src, {
          w,
          q: quality,
          fm: format
        });
        return `${optimizedUrl} ${w}w`;
      })
      .join(', ');
  };

  // Preload image when visible
  useEffect(() => {
    if (isVisible && loading === 'lazy') {
      const img = new Image();
      
      img.onload = () => {
        setImageSrc(src);
        setIsLoading(false);
        onLoad?.();
      };
      
      img.onerror = () => {
        setImageError(true);
        setIsLoading(false);
        onError?.();
      };
      
      // Set srcset for preloading
      if (srcSet || width) {
        img.srcset = generateSrcSet();
      }
      
      img.src = src;
    } else if (loading === 'eager') {
      setImageSrc(src);
      setIsLoading(false);
    }
  }, [isVisible, src, loading, srcSet, onLoad, onError, quality, format]);

  // Handle image error
  const handleError = () => {
    setImageError(true);
    setImageSrc('/images/error-placeholder.svg');
    onError?.();
  };

  // Blur-up effect styles
  const blurUpStyles = isLoading ? {
    filter: 'blur(5px)',
    transform: 'scale(1.1)',
    transition: 'filter 0.3s, transform 0.3s'
  } : {
    filter: 'blur(0)',
    transform: 'scale(1)',
    transition: 'filter 0.3s, transform 0.3s'
  };

  return (
    <div 
      ref={ref as any}
      className={`optimized-image-wrapper ${className}`}
      style={{ position: 'relative', overflow: 'hidden' }}
    >
      <picture>
        {/* WebP format with fallback */}
        {format === 'webp' && !imageError && (
          <>
            <source
              type="image/webp"
              srcSet={generateSrcSet()}
              sizes={sizes}
            />
            <source
              type="image/jpeg"
              srcSet={generateSrcSet().replace(/fm=webp/g, 'fm=jpeg')}
              sizes={sizes}
            />
          </>
        )}
        
        <img
          ref={imageRef}
          src={imageSrc}
          alt={alt}
          width={width}
          height={height}
          loading={loading === 'eager' ? 'eager' : 'lazy'}
          onError={handleError}
          onLoad={() => {
            setIsLoading(false);
            onLoad?.();
          }}
          style={{
            width: '100%',
            height: 'auto',
            ...blurUpStyles
          }}
          className={`optimized-image ${imageError ? 'error' : ''}`}
        />
      </picture>

      {/* Loading skeleton */}
      {isLoading && (
        <div 
          className="image-skeleton"
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            background: 'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)',
            backgroundSize: '200% 100%',
            animation: 'shimmer 1.5s infinite'
          }}
        />
      )}
    </div>
  );
};

/**
 * Optimized background image component
 */
interface OptimizedBackgroundProps {
  src: string;
  className?: string;
  children?: React.ReactNode;
  parallax?: boolean;
  overlay?: boolean;
  overlayOpacity?: number;
}

export const OptimizedBackground: React.FC<OptimizedBackgroundProps> = ({
  src,
  className = '',
  children,
  parallax = false,
  overlay = false,
  overlayOpacity = 0.5
}) => {
  const [offset, setOffset] = useState(0);
  const { ref, isVisible } = useLazyLoad();

  useEffect(() => {
    if (parallax && isVisible) {
      const handleScroll = () => {
        const scrolled = window.scrollY;
        setOffset(scrolled * 0.5);
      };

      window.addEventListener('scroll', handleScroll, { passive: true });
      return () => window.removeEventListener('scroll', handleScroll);
    }
  }, [parallax, isVisible]);

  const backgroundStyle: React.CSSProperties = {
    backgroundImage: isVisible ? `url(${src})` : 'none',
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    transform: parallax ? `translateY(${offset}px)` : 'none',
    transition: 'transform 0.5s ease-out',
    position: 'relative',
    overflow: 'hidden'
  };

  return (
    <div 
      ref={ref as any}
      className={`optimized-background ${className}`}
      style={backgroundStyle}
    >
      {overlay && (
        <div 
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            backgroundColor: `rgba(0, 0, 0, ${overlayOpacity})`,
            pointerEvents: 'none'
          }}
        />
      )}
      {children}
    </div>
  );
};

// CSS for shimmer effect
const shimmerCSS = `
@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}
`;

// Add CSS to document
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = shimmerCSS;
  document.head.appendChild(style);
}
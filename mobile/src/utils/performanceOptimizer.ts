/**
 * Performance optimization utilities for React Native
 */
import { InteractionManager, Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import FastImage from 'react-native-fast-image';
import { logger } from './logger';

/**
 * Performance metrics collector
 */
class PerformanceMetrics {
  private metrics: Map<string, any> = new Map();
  private timers: Map<string, number> = new Map();

  startTimer(key: string) {
    this.timers.set(key, Date.now());
  }

  endTimer(key: string): number {
    const startTime = this.timers.get(key);
    if (!startTime) {
      logger.warn(`Timer ${key} was not started`);
      return 0;
    }

    const duration = Date.now() - startTime;
    this.timers.delete(key);

    // Track metric
    const metrics = this.metrics.get(key) || { count: 0, totalTime: 0, avgTime: 0 };
    metrics.count += 1;
    metrics.totalTime += duration;
    metrics.avgTime = metrics.totalTime / metrics.count;
    this.metrics.set(key, metrics);

    // Log slow operations
    if (duration > 1000) {
      logger.warn(`Slow operation detected: ${key} took ${duration}ms`);
    }

    return duration;
  }

  getMetrics() {
    return Object.fromEntries(this.metrics);
  }

  reset() {
    this.metrics.clear();
    this.timers.clear();
  }
}

export const performanceMetrics = new PerformanceMetrics();

/**
 * Defer heavy operations until after interactions
 */
export const deferOperation = (operation: () => void | Promise<void>) => {
  InteractionManager.runAfterInteractions(() => {
    operation();
  });
};

/**
 * Batch multiple operations for better performance
 */
export class BatchProcessor<T> {
  private queue: T[] = [];
  private processing = false;
  private batchSize: number;
  private processDelay: number;
  private processor: (batch: T[]) => Promise<void>;

  constructor(
    processor: (batch: T[]) => Promise<void>,
    batchSize = 50,
    processDelay = 100
  ) {
    this.processor = processor;
    this.batchSize = batchSize;
    this.processDelay = processDelay;
  }

  add(item: T) {
    this.queue.push(item);
    this.processQueue();
  }

  addBatch(items: T[]) {
    this.queue.push(...items);
    this.processQueue();
  }

  private async processQueue() {
    if (this.processing || this.queue.length === 0) return;

    this.processing = true;

    // Wait for delay to batch more items
    await new Promise(resolve => setTimeout(resolve, this.processDelay));

    while (this.queue.length > 0) {
      const batch = this.queue.splice(0, this.batchSize);
      
      try {
        await this.processor(batch);
      } catch (error) {
        logger.error('Batch processing error:', error);
      }
    }

    this.processing = false;
  }
}

/**
 * Image cache manager for React Native
 */
export class ImageCacheManager {
  private static instance: ImageCacheManager;
  private cacheSize = 0;
  private maxCacheSize = 200 * 1024 * 1024; // 200MB

  static getInstance(): ImageCacheManager {
    if (!ImageCacheManager.instance) {
      ImageCacheManager.instance = new ImageCacheManager();
    }
    return ImageCacheManager.instance;
  }

  /**
   * Preload images for better performance
   */
  async preloadImages(urls: string[]) {
    performanceMetrics.startTimer('image_preload');

    const preloadPromises = urls.map(url => 
      FastImage.preload([{ uri: url }])
    );

    try {
      await Promise.all(preloadPromises);
      logger.info(`Preloaded ${urls.length} images`);
    } catch (error) {
      logger.error('Image preload error:', error);
    }

    performanceMetrics.endTimer('image_preload');
  }

  /**
   * Clear image cache
   */
  async clearCache() {
    try {
      await FastImage.clearMemoryCache();
      await FastImage.clearDiskCache();
      this.cacheSize = 0;
      logger.info('Image cache cleared');
    } catch (error) {
      logger.error('Failed to clear image cache:', error);
    }
  }

  /**
   * Get optimized image source with caching
   */
  getOptimizedSource(url: string, options?: {
    width?: number;
    height?: number;
    quality?: number;
  }) {
    const { width = 800, height = 600, quality = 85 } = options || {};

    // Add CDN parameters for optimization
    const optimizedUrl = `${url}?w=${width}&h=${height}&q=${quality}&fm=webp`;

    return {
      uri: optimizedUrl,
      priority: FastImage.priority.normal,
      cache: FastImage.cacheControl.immutable,
    };
  }
}

/**
 * Memory optimizer for React Native
 */
export class MemoryOptimizer {
  private listeners: Array<() => void> = [];

  constructor() {
    // Listen for memory warnings
    if (Platform.OS === 'ios') {
      // iOS memory warning handling would go here
    }
  }

  /**
   * Register cleanup callback for memory pressure
   */
  onMemoryWarning(callback: () => void) {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter(cb => cb !== callback);
    };
  }

  /**
   * Trigger memory cleanup
   */
  cleanup() {
    logger.info('Running memory cleanup');
    
    // Clear caches
    ImageCacheManager.getInstance().clearCache();
    
    // Run registered cleanup callbacks
    this.listeners.forEach(callback => {
      try {
        callback();
      } catch (error) {
        logger.error('Memory cleanup callback error:', error);
      }
    });

    // Force garbage collection if available
    if (global.gc) {
      global.gc();
    }
  }
}

/**
 * List optimization with recycling
 */
export interface VirtualizedListConfig<T> {
  data: T[];
  renderItem: (item: T, index: number) => React.ReactElement;
  getItemLayout?: (data: T[] | null | undefined, index: number) => {
    length: number;
    offset: number;
    index: number;
  };
  keyExtractor: (item: T, index: number) => string;
  initialNumToRender?: number;
  maxToRenderPerBatch?: number;
  windowSize?: number;
  removeClippedSubviews?: boolean;
}

export const getOptimizedListProps = <T>(
  config: VirtualizedListConfig<T>
) => {
  return {
    data: config.data,
    renderItem: config.renderItem,
    keyExtractor: config.keyExtractor,
    getItemLayout: config.getItemLayout,
    
    // Performance optimizations
    initialNumToRender: config.initialNumToRender || 10,
    maxToRenderPerBatch: config.maxToRenderPerBatch || 10,
    windowSize: config.windowSize || 10,
    removeClippedSubviews: config.removeClippedSubviews ?? true,
    
    // Additional optimizations
    updateCellsBatchingPeriod: 50,
    legacyImplementation: false,
    
    // Scroll optimizations
    scrollEventThrottle: 16,
    decelerationRate: 'fast',
    
    // Memory optimizations
    maintainVisibleContentPosition: {
      minIndexForVisible: 0,
    },
  };
};

/**
 * Storage optimization utilities
 */
export class StorageOptimizer {
  private static readonly CACHE_PREFIX = '@cache:';
  private static readonly MAX_CACHE_AGE = 7 * 24 * 60 * 60 * 1000; // 7 days

  /**
   * Set data with automatic expiration
   */
  static async setCached(key: string, data: any, ttl?: number) {
    const cacheKey = `${this.CACHE_PREFIX}${key}`;
    const expiresAt = Date.now() + (ttl || this.MAX_CACHE_AGE);
    
    const cacheData = {
      data,
      expiresAt,
      timestamp: Date.now()
    };

    try {
      await AsyncStorage.setItem(cacheKey, JSON.stringify(cacheData));
    } catch (error) {
      logger.error('Cache write error:', error);
    }
  }

  /**
   * Get cached data if not expired
   */
  static async getCached<T>(key: string): Promise<T | null> {
    const cacheKey = `${this.CACHE_PREFIX}${key}`;
    
    try {
      const cached = await AsyncStorage.getItem(cacheKey);
      if (!cached) return null;

      const cacheData = JSON.parse(cached);
      
      // Check expiration
      if (Date.now() > cacheData.expiresAt) {
        await AsyncStorage.removeItem(cacheKey);
        return null;
      }

      return cacheData.data as T;
    } catch (error) {
      logger.error('Cache read error:', error);
      return null;
    }
  }

  /**
   * Clean expired cache entries
   */
  static async cleanExpiredCache() {
    performanceMetrics.startTimer('cache_cleanup');
    
    try {
      const keys = await AsyncStorage.getAllKeys();
      const cacheKeys = keys.filter(key => key.startsWith(this.CACHE_PREFIX));
      
      const promises = cacheKeys.map(async (key) => {
        try {
          const cached = await AsyncStorage.getItem(key);
          if (!cached) return;
          
          const cacheData = JSON.parse(cached);
          if (Date.now() > cacheData.expiresAt) {
            await AsyncStorage.removeItem(key);
          }
        } catch (error) {
          // Remove corrupted cache entries
          await AsyncStorage.removeItem(key);
        }
      });

      await Promise.all(promises);
      logger.info(`Cleaned ${promises.length} cache entries`);
    } catch (error) {
      logger.error('Cache cleanup error:', error);
    }

    performanceMetrics.endTimer('cache_cleanup');
  }

  /**
   * Get storage info
   */
  static async getStorageInfo() {
    try {
      const keys = await AsyncStorage.getAllKeys();
      let totalSize = 0;
      const sizeByPrefix: Record<string, number> = {};

      for (const key of keys) {
        const value = await AsyncStorage.getItem(key);
        if (value) {
          const size = new Blob([value]).size;
          totalSize += size;

          const prefix = key.split(':')[0];
          sizeByPrefix[prefix] = (sizeByPrefix[prefix] || 0) + size;
        }
      }

      return {
        totalKeys: keys.length,
        totalSizeMB: totalSize / 1024 / 1024,
        sizeByPrefix: Object.entries(sizeByPrefix).map(([prefix, size]) => ({
          prefix,
          sizeMB: size / 1024 / 1024
        }))
      };
    } catch (error) {
      logger.error('Storage info error:', error);
      return null;
    }
  }
}

/**
 * Performance monitoring decorator
 */
export function measurePerformance(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
  const originalMethod = descriptor.value;

  descriptor.value = async function (...args: any[]) {
    const timerKey = `${target.constructor.name}.${propertyKey}`;
    performanceMetrics.startTimer(timerKey);
    
    try {
      const result = await originalMethod.apply(this, args);
      performanceMetrics.endTimer(timerKey);
      return result;
    } catch (error) {
      performanceMetrics.endTimer(timerKey);
      throw error;
    }
  };

  return descriptor;
}

// Export singleton instances
export const memoryOptimizer = new MemoryOptimizer();
export const imageCache = ImageCacheManager.getInstance();
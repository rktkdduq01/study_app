# Performance Monitoring and Optimization Guide

## Overview

This guide documents the performance monitoring and optimization strategies implemented across the Quest Educational Platform.

## Performance Monitoring

### 1. Backend Monitoring

#### Middleware Setup
```python
# In main.py
from app.middleware.performance import PerformanceMiddleware

app.add_middleware(
    PerformanceMiddleware,
    slow_request_threshold=1.0,  # 1 second
    enable_profiling=settings.ENABLE_PROFILING
)
```

#### Metrics Collected
- **Request Metrics**
  - Request count by endpoint and status
  - Response time (p50, p95, p99)
  - Active concurrent requests
  - Slow request tracking (>1s)

- **System Metrics**
  - CPU usage percentage
  - Memory usage (RSS, available)
  - Disk I/O and usage
  - Network connections

- **Database Metrics**
  - Query execution time
  - Slow query logging (>500ms)
  - Connection pool status
  - Index usage analysis

#### Prometheus Integration
Access metrics at `/api/v1/performance/metrics/prometheus` for Grafana dashboards.

### 2. Frontend Monitoring

#### React Performance Hooks
```typescript
// Component performance monitoring
const metrics = usePerformanceMonitor('MyComponent', {
  slowRenderThreshold: 16, // 60fps
  enableLogging: true
});

// Web Vitals tracking
useWebVitals((metric) => {
  analytics.track('web_vital', metric);
});
```

#### Metrics Tracked
- Component render times
- Re-render frequency
- Interaction delays
- Bundle size impact
- Memory leaks

### 3. Mobile App Monitoring

#### Performance Metrics Collection
```typescript
import { performanceMetrics } from '@/utils/performanceOptimizer';

// Track operation timing
performanceMetrics.startTimer('data_fetch');
const data = await fetchData();
const duration = performanceMetrics.endTimer('data_fetch');
```

## Optimization Strategies

### 1. Database Optimizations

#### Query Optimization
```python
from app.db.query_optimizer import QueryOptimizer

# Prevent N+1 queries
query = QueryOptimizer.optimize_relationship_loading(
    db.query(User),
    ['character', 'quests.progress'],
    strategy='selectin'
)

# Batch loading
users = QueryOptimizer.batch_load(db, User, user_ids, batch_size=500)
```

#### Index Recommendations
Run index analysis:
```bash
GET /api/v1/performance/optimize/indexes
```

Recommended indexes:
- `users`: email, username, created_at
- `quests`: (type, difficulty), (subject, min_level)
- `quest_progress`: (user_id, status), completed_at
- `multiplayer_sessions`: session_code, (type, is_public)

#### Connection Pooling
```python
# In database config
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 20,
    "max_overflow": 40,
    "pool_pre_ping": True,
    "pool_recycle": 3600
}
```

### 2. Caching Strategies

#### Query Result Caching
```python
@QueryCache.cache("user_profile", ttl=300)
def get_user_profile(user_id: int):
    return db.query(User).filter(User.id == user_id).first()
```

#### Redis Caching
- User sessions: 15 minute TTL
- Quest data: 5 minute TTL
- Leaderboards: 1 minute TTL
- Static content: 1 hour TTL

### 3. Frontend Optimizations

#### Code Splitting
```typescript
// Lazy load heavy components
const HeavyComponent = lazy(() => import('./HeavyComponent'));

// Route-based splitting
const QuestPage = lazy(() => import('./pages/QuestPage'));
```

#### Image Optimization
```tsx
// Use optimized image component
<OptimizedImage
  src="/images/hero.jpg"
  alt="Hero"
  loading="lazy"
  format="webp"
  quality={85}
  sizes="(max-width: 768px) 100vw, 50vw"
/>
```

#### List Virtualization
```typescript
// Virtual scrolling for large lists
const { visibleItems, containerProps } = useVirtualScroll({
  items: largeArray,
  itemHeight: 50,
  containerHeight: 500
});
```

### 4. Mobile Optimizations

#### Image Caching
```typescript
// Preload critical images
await imageCache.preloadImages([
  '/images/logo.png',
  '/images/characters/default.png'
]);

// Get optimized source
const source = imageCache.getOptimizedSource(url, {
  width: 400,
  height: 300,
  quality: 80
});
```

#### Batch Processing
```typescript
// Batch API calls
const batchProcessor = new BatchProcessor(
  async (items) => {
    await api.batchUpdate(items);
  },
  50, // batch size
  100  // delay ms
);
```

#### Memory Management
```typescript
// Register cleanup handlers
memoryOptimizer.onMemoryWarning(() => {
  // Clear non-critical caches
  temporaryCache.clear();
  imageCache.clearCache();
});
```

## Performance Targets

### Response Time SLAs
- API Endpoints: p95 < 200ms, p99 < 500ms
- Database Queries: p95 < 100ms
- WebSocket Events: < 50ms
- Page Load: < 3s on 3G

### Resource Usage Limits
- Memory: < 80% utilization
- CPU: < 70% sustained
- Database Connections: < 80% of pool
- Disk I/O: < 1000 IOPS

## Monitoring Dashboard

### Key Metrics to Track
1. **Golden Signals**
   - Latency (response times)
   - Traffic (requests per second)
   - Errors (error rate)
   - Saturation (resource usage)

2. **Business Metrics**
   - Active users
   - Quest completion rate
   - Average session duration
   - Revenue per user

### Alert Thresholds
- Response time > 1s for 5 minutes
- Error rate > 1% for 5 minutes
- CPU > 80% for 10 minutes
- Memory > 85% for 5 minutes
- Disk space < 10GB

## Performance Testing

### Load Testing
```bash
# Using locust
locust -f tests/load/locustfile.py --host=https://api.quest-edu.com
```

Target: 10,000 concurrent users with <500ms p95 response time

### Stress Testing
Gradually increase load to find breaking point:
- Start: 1,000 users
- Increment: 1,000 users/minute
- Stop: System failure or 20,000 users

## Best Practices

### 1. Development
- Profile before optimizing
- Measure impact of changes
- Set performance budgets
- Regular performance reviews

### 2. Code Reviews
- Check for N+1 queries
- Verify proper indexing
- Review caching strategy
- Assess bundle size impact

### 3. Deployment
- Gradual rollouts
- Monitor key metrics
- Have rollback plan
- Load test new features

### 4. Database
- Regular VACUUM/ANALYZE
- Monitor slow query log
- Update statistics
- Archive old data

## Troubleshooting

### High Response Times
1. Check slow query log
2. Review cache hit rates
3. Analyze CPU/memory usage
4. Check network latency

### Memory Leaks
1. Monitor heap usage over time
2. Check for uncleared timers
3. Review event listener cleanup
4. Analyze object retention

### Database Performance
1. Run EXPLAIN ANALYZE
2. Check index usage
3. Review connection pool
4. Analyze lock contention

## Tools and Resources

### Monitoring Tools
- **Prometheus + Grafana**: Metrics visualization
- **Sentry**: Error tracking
- **New Relic**: APM (if applicable)
- **pgBadger**: PostgreSQL log analysis

### Performance Tools
- **Chrome DevTools**: Frontend profiling
- **React DevTools**: Component profiling
- **Lighthouse**: Web performance audit
- **WebPageTest**: Real-world performance testing

### Load Testing
- **Locust**: Python-based load testing
- **K6**: Modern load testing tool
- **Apache JMeter**: Comprehensive testing
- **Artillery**: Quick performance tests

## Future Improvements

1. **Implement APM Solution**
   - Distributed tracing
   - Code-level insights
   - Automatic anomaly detection

2. **Advanced Caching**
   - GraphQL query caching
   - Edge caching with CDN
   - Predictive cache warming

3. **Database Optimization**
   - Read replicas for analytics
   - Partitioning for large tables
   - Query result materialization

4. **Frontend Optimization**
   - Service Worker caching
   - WebAssembly for compute
   - Progressive enhancement

5. **Infrastructure**
   - Auto-scaling policies
   - Geographic distribution
   - Container optimization
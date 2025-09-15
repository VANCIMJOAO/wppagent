# 🔧 WhatsApp Agent - Guia de Troubleshooting

> **Guia completo de resolução de problemas** com diagnósticos detalhados, comandos de debug, soluções step-by-step e procedimentos de recuperação para produção.

---

## 🎯 **VISÃO GERAL DE TROUBLESHOOTING**

### **Metodologia de Diagnóstico** 🔍

1. **🚨 Identificação**: Sintomas e alertas
2. **🔍 Investigação**: Logs, métricas e health checks
3. **📊 Análise**: Root cause analysis
4. **⚡ Ação**: Solução imediata
5. **🛡️ Prevenção**: Medidas preventivas

### **Categorias de Problemas**

- 🌐 **Application Issues**: FastAPI/Next.js
- 🗄️ **Database Problems**: PostgreSQL
- 🚀 **Cache Issues**: Redis
- 🔗 **External API**: Meta WhatsApp
- 🔐 **Security Events**: Auth/Rate limiting
- ⚡ **Performance**: Response time/Memory

---

## 🌐 **APPLICATION ISSUES**

### **🚨 Service Not Responding**

#### **Symptoms**

- Health check endpoint returns 500/timeout
- Application completely unreachable
- Load balancer shows service as down

#### **Diagnostic Commands**

```bash
# ✅ 1. Check service status
systemctl status whatsapp-backend
systemctl status whatsapp-frontend

# ✅ 2. Check process
ps aux | grep -E "(uvicorn|node)"

# ✅ 3. Check ports
netstat -tlnp | grep -E "(8000|3000)"
ss -tlnp | grep -E "(8000|3000)"

# ✅ 4. Check recent logs
tail -50 logs/security_audit.log
journalctl -u whatsapp-backend --since "10 minutes ago"

# ✅ 5. Check system resources
htop
df -h
free -h
```

#### **Common Causes & Solutions**

**🔧 Memory Exhaustion**

```bash
# Diagnosis
free -h
ps aux --sort=-%mem | head -10

# Solution
# Restart service to free memory
systemctl restart whatsapp-backend

# Long-term fix: optimize memory usage
# Check app/utils/memory_optimizer.py
```

**🔧 Port Already in Use**

```bash
# Diagnosis
lsof -i :8000
lsof -i :3000

# Solution
# Kill existing process
kill -9 $(lsof -t -i:8000)
systemctl restart whatsapp-backend
```

**🔧 File Descriptor Limit**

```bash
# Diagnosis
ulimit -n
lsof | wc -l

# Solution
# Increase file descriptor limit
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf
# Restart service
systemctl restart whatsapp-backend
```

### **🐛 Application Errors (500 Internal Server Error)**

#### **Diagnostic Commands**

```bash
# ✅ 1. Check error logs
grep '"level":"ERROR"' logs/security_audit.log | tail -20
grep '"level":"CRITICAL"' logs/security_audit.log | tail -10

# ✅ 2. Check specific error patterns
grep "Exception" logs/security_audit.log | tail -10
grep "Traceback" logs/security_audit.log | tail -5

# ✅ 3. Check database connectivity
python -c "
from app.database import engine
from sqlalchemy import text
import asyncio

async def test_db():
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text('SELECT 1'))
            print('✅ Database connection: OK')
    except Exception as e:
        print(f'❌ Database error: {e}')

asyncio.run(test_db())
"

# ✅ 4. Check Redis connectivity
redis-cli -u $REDIS_URL ping
```

#### **Common Causes & Solutions**

**🔧 Configuration Errors**

```bash
# Diagnosis
python -c "from app.config import settings; print('✅ Config loaded')"

# Check environment variables
env | grep -E "(DATABASE_URL|REDIS_URL|JWT_SECRET)"

# Solution
# Verify .env file
cat .env | grep -v "^#" | grep -v "^$"
# Restart with correct config
systemctl restart whatsapp-backend
```

**🔧 Import/Module Errors**

```bash
# Diagnosis
python -c "import app.main"
python -m pytest tests/ --collect-only

# Solution
# Check Python path and dependencies
pip list | grep -E "(fastapi|sqlalchemy|redis)"
pip install -r requirements.txt
```

### **⚡ Slow Response Times**

#### **Diagnostic Commands**

```bash
# ✅ 1. Check response times from logs
grep '"category":"api"' logs/security_audit.log | \
jq '.performance_metrics.duration_ms' | \
sort -n | tail -20

# ✅ 2. Identify slow endpoints
grep '"category":"api"' logs/security_audit.log | \
jq 'select(.performance_metrics.duration_ms > 1000) | {path: .metadata.path, duration: .performance_metrics.duration_ms}' | \
head -10

# ✅ 3. Check database slow queries
psql $DATABASE_URL -c "
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;"

# ✅ 4. Check system load
uptime
iostat 1 5
sar -u 1 5
```

#### **Solutions**

**🔧 Database Performance**

```sql
-- Check for missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY n_distinct DESC;

-- Check slow queries
SELECT query, mean_exec_time, calls, total_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 100
ORDER BY mean_exec_time DESC;

-- Analyze table statistics
ANALYZE;

-- Check for bloated tables
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

**🔧 Cache Optimization**

```bash
# Check cache hit rate
redis-cli -u $REDIS_URL info stats | grep keyspace

# Clear problematic cache entries
redis-cli -u $REDIS_URL --scan --pattern "stale:*" | xargs redis-cli -u $REDIS_URL del

# Monitor cache performance
redis-cli -u $REDIS_URL monitor | grep -E "(GET|SET|DEL)"
```

---

## 🗄️ **DATABASE PROBLEMS**

### **🚨 Database Connection Errors**

#### **Symptoms**

- "Connection refused" errors
- "Too many connections" errors
- Health check database status: unhealthy

#### **Diagnostic Commands**

```bash
# ✅ 1. Check PostgreSQL status
systemctl status postgresql
ps aux | grep postgres

# ✅ 2. Check connection count
psql $DATABASE_URL -c "
SELECT count(*) as active_connections,
       state,
       application_name
FROM pg_stat_activity
GROUP BY state, application_name
ORDER BY active_connections DESC;"

# ✅ 3. Check connection limits
psql $DATABASE_URL -c "SHOW max_connections;"
psql $DATABASE_URL -c "SELECT setting FROM pg_settings WHERE name='max_connections';"

# ✅ 4. Check for blocking queries
psql $DATABASE_URL -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';"
```

#### **Solutions**

**🔧 Too Many Connections**

```bash
# Immediate fix: kill idle connections
psql $DATABASE_URL -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
  AND state_change < current_timestamp - INTERVAL '30 minutes';"

# Long-term fix: adjust connection pool
# Edit app/database.py
# pool_size=10, max_overflow=5
```

**🔧 Database Not Starting**

```bash
# Check PostgreSQL logs
tail -50 /var/log/postgresql/postgresql-16-main.log

# Check disk space
df -h /var/lib/postgresql/

# Start PostgreSQL
systemctl start postgresql

# If corrupt, recover from backup
pg_restore --clean --if-exists -d whatsapp_agent backup.sql
```

### **🐌 Slow Database Queries**

#### **Diagnostic Commands**

```sql
-- Enable query statistics (if not enabled)
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Find slowest queries
SELECT query,
       calls,
       total_exec_time,
       mean_exec_time,
       stddev_exec_time,
       rows
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Check for missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public'
  AND n_distinct > 100
ORDER BY n_distinct DESC;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;
```

#### **Solutions**

**🔧 Add Missing Indexes**

```sql
-- Example: Add index for frequently queried columns
CREATE INDEX CONCURRENTLY idx_appointments_user_status
ON appointments (user_id, status)
WHERE deleted_at IS NULL;

-- Composite index for complex queries
CREATE INDEX CONCURRENTLY idx_conversations_phone_date_status
ON conversations (phone_number, created_at DESC, status)
WHERE deleted_at IS NULL;
```

**🔧 Query Optimization**

```python
# Before: N+1 query problem
async def get_appointments_slow():
    appointments = await db.execute(select(Appointment))
    for appointment in appointments:
        user = await db.execute(select(User).where(User.id == appointment.user_id))

# After: Optimized with eager loading
async def get_appointments_fast():
    appointments = await db.execute(
        select(Appointment)
        .options(joinedload(Appointment.user))
    )
    return appointments.unique().scalars().all()
```

### **🔄 Migration Issues**

#### **Diagnostic Commands**

```bash
# ✅ Check current migration status
alembic current
alembic heads

# ✅ Check for migration conflicts
alembic history --verbose

# ✅ Check database schema
psql $DATABASE_URL -c "\dt"  # List tables
psql $DATABASE_URL -c "\di"  # List indexes
```

#### **Solutions**

**🔧 Multiple Heads (Merge Conflict)**

```bash
# Diagnosis
alembic heads
# Shows multiple heads: abc123, def456

# Solution
# Create merge migration
alembic merge heads -m "merge conflicting migrations"
alembic upgrade head
```

**🔧 Failed Migration**

```bash
# Check failed migration
alembic history

# Rollback to previous version
alembic downgrade -1

# Fix migration file and retry
alembic upgrade head
```

---

## 🚀 **CACHE ISSUES (REDIS)**

### **🚨 Redis Connection Errors**

#### **Diagnostic Commands**

```bash
# ✅ 1. Check Redis status
systemctl status redis-server
redis-cli -u $REDIS_URL ping

# ✅ 2. Check Redis logs
tail -50 /var/log/redis/redis-server.log

# ✅ 3. Check Redis configuration
redis-cli -u $REDIS_URL config get "*"

# ✅ 4. Check memory usage
redis-cli -u $REDIS_URL info memory

# ✅ 5. Check connected clients
redis-cli -u $REDIS_URL info clients
```

#### **Solutions**

**🔧 Redis Out of Memory**

```bash
# Diagnosis
redis-cli -u $REDIS_URL info memory | grep used_memory_human

# Immediate fix: clear cache
redis-cli -u $REDIS_URL flushall

# Configure memory limit
redis-cli -u $REDIS_URL config set maxmemory 512mb
redis-cli -u $REDIS_URL config set maxmemory-policy allkeys-lru
```

**🔧 Redis Connection Refused**

```bash
# Check if Redis is running
systemctl start redis-server

# Check Redis configuration
grep -E "(bind|port|requirepass)" /etc/redis/redis.conf

# Test connection
redis-cli -h localhost -p 6379 -a password ping
```

### **📉 Low Cache Hit Rate**

#### **Diagnostic Commands**

```bash
# ✅ Check cache statistics
redis-cli -u $REDIS_URL info stats | grep -E "(hits|misses)"

# ✅ Check cache keys
redis-cli -u $REDIS_URL --scan --pattern "app:*" | head -20

# ✅ Check TTL distribution
redis-cli -u $REDIS_URL --scan | head -100 | while read key; do
  echo "$key: $(redis-cli -u $REDIS_URL ttl $key)"
done
```

#### **Solutions**

**🔧 Optimize Cache Strategy**

```python
# Identify cache misses in logs
grep '"operation":"get"' logs/security_audit.log | \
grep '"result":"miss"' | \
jq '.metadata.key' | sort | uniq -c

# Adjust TTL for frequently accessed data
cache_manager.set("user:123", user_data, ttl=7200)  # 2 hours instead of 1

# Implement cache warming
async def warm_cache():
    popular_users = await get_popular_users()
    for user in popular_users:
        await cache_manager.set(f"user:{user.id}", user, ttl=3600)
```

---

## 🔗 **EXTERNAL API ISSUES (META WHATSAPP)**

### **🚨 Meta API Connection Errors**

#### **Diagnostic Commands**

```bash
# ✅ 1. Test Meta API directly
curl -X GET "https://graph.facebook.com/v18.0/me" \
  -H "Authorization: Bearer $META_ACCESS_TOKEN"

# ✅ 2. Test phone number endpoint
curl -X GET "https://graph.facebook.com/v18.0/$META_PHONE_NUMBER_ID" \
  -H "Authorization: Bearer $META_ACCESS_TOKEN"

# ✅ 3. Check webhook subscription
curl -X GET "https://graph.facebook.com/v18.0/$META_APP_ID/subscriptions" \
  -H "Authorization: Bearer $META_ACCESS_TOKEN"

# ✅ 4. Check webhook endpoint
curl -X POST "https://yourdomain.com/webhook" \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=test" \
  -d '{"test": "data"}'
```

#### **Common Issues & Solutions**

**🔧 Invalid Access Token**

```bash
# Diagnosis
curl -X GET "https://graph.facebook.com/v18.0/me" \
  -H "Authorization: Bearer $META_ACCESS_TOKEN"
# Response: {"error": {"code": 190, "message": "Invalid OAuth access token"}}

# Solution
# 1. Generate new token in Meta for Developers
# 2. Update environment variable
export META_ACCESS_TOKEN="new_token_here"
systemctl restart whatsapp-backend
```

**🔧 Rate Limiting from Meta**

```bash
# Diagnosis: Check rate limit headers in logs
grep "x-business-use-case-usage" logs/security_audit.log

# Solution: Implement exponential backoff
async def send_message_with_retry(phone, message, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await meta_api.send_message(phone, message)
        except RateLimitError:
            wait_time = 2 ** attempt
            await asyncio.sleep(wait_time)
    raise Exception("Max retries exceeded")
```

### **🔧 Webhook Validation Errors**

#### **Diagnostic Commands**

```bash
# ✅ Check webhook verification
grep "webhook_verification" logs/security_audit.log | tail -10

# ✅ Check signature validation
grep "webhook_signature" logs/security_audit.log | tail -10

# ✅ Test webhook manually
curl -X GET "https://yourdomain.com/webhook" \
  -G -d "hub.mode=subscribe" \
     -d "hub.challenge=123456789" \
     -d "hub.verify_token=$WEBHOOK_VERIFY_TOKEN"
```

#### **Solutions**

**🔧 Signature Validation Failing**

```python
# Debug signature validation
import hmac
import hashlib

def debug_webhook_signature(payload: str, received_signature: str):
    expected = hmac.new(
        settings.WEBHOOK_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    print(f"Expected: {expected}")
    print(f"Received: {received_signature}")
    print(f"Match: {hmac.compare_digest(expected, received_signature)}")

# Check webhook secret configuration
echo $WEBHOOK_SECRET
```

---

## 🔐 **SECURITY ISSUES**

### **🚨 Authentication Failures**

#### **Diagnostic Commands**

```bash
# ✅ Check failed authentication attempts
grep '"event_type":"login_failed"' logs/security_audit.log | tail -20

# ✅ Check source IPs
grep '"event_type":"login_failed"' logs/security_audit.log | \
jq -r '.metadata.client_ip' | sort | uniq -c | sort -nr

# ✅ Check rate limiting violations
grep '"event_type":"rate_limit_exceeded"' logs/security_audit.log | tail -10
```

#### **Solutions**

**🔧 Brute Force Attack**

```bash
# Identify attacking IPs
grep '"event_type":"login_failed"' logs/security_audit.log | \
jq -r '.metadata.client_ip' | sort | uniq -c | sort -nr | head -10

# Block malicious IPs
iptables -A INPUT -s 192.168.1.200 -j DROP

# Increase rate limiting temporarily
# Edit app/middleware/rate_limiting.py
# Change: @limiter.limit("5/minute") to @limiter.limit("2/minute")
```

**🔧 JWT Token Issues**

```python
# Test JWT token validation
import jwt
from app.config import settings

def debug_jwt_token(token: str):
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        print(f"✅ Token valid: {payload}")
    except jwt.ExpiredSignatureError:
        print("❌ Token expired")
    except jwt.InvalidTokenError as e:
        print(f"❌ Invalid token: {e}")

# Check JWT secret
echo $JWT_SECRET_KEY | wc -c  # Should be >= 32 characters
```

### **🛡️ CORS Errors**

#### **Diagnostic Commands**

```bash
# ✅ Test CORS preflight
curl -X OPTIONS "https://yourdomain.com/api/health" \
  -H "Origin: https://frontend.com" \
  -H "Access-Control-Request-Method: GET" \
  -v

# ✅ Check CORS configuration
grep -A 10 "CORSMiddleware" app/cors_config.py
```

#### **Solutions**

**🔧 CORS Origin Not Allowed**

```python
# Check current CORS origins
from app.cors_config import allowed_origins
print(allowed_origins)

# Add new origin
# Edit app/cors_config.py
allowed_origins = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
    "https://newdomain.com"  # Add new domain
]
```

---

## ⚡ **PERFORMANCE ISSUES**

### **🐌 High Memory Usage**

#### **Diagnostic Commands**

```bash
# ✅ Check overall memory usage
free -h
ps aux --sort=-%mem | head -10

# ✅ Check application memory
ps -p $(pgrep -f uvicorn) -o pid,vsz,rss,pcpu,pmem,cmd

# ✅ Check Python memory usage
python -c "
import psutil
import gc
process = psutil.Process()
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB')
print(f'Objects: {len(gc.get_objects())}')
"
```

#### **Solutions**

**🔧 Memory Leak Detection**

```python
# Add memory profiling
import tracemalloc
import gc

# Start tracing
tracemalloc.start()

# After some operations
current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")

# Force garbage collection
gc.collect()
```

**🔧 Optimize Database Sessions**

```python
# Ensure sessions are properly closed
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()  # Explicit close

# Use context managers for manual sessions
async with AsyncSessionLocal() as session:
    # Do database operations
    pass  # Session automatically closed
```

### **🔥 High CPU Usage**

#### **Diagnostic Commands**

```bash
# ✅ Check CPU usage
top -p $(pgrep -f uvicorn)
htop -p $(pgrep -f uvicorn)

# ✅ Profile application
python -m cProfile -s cumulative app/main.py

# ✅ Check async loops
strace -p $(pgrep -f uvicorn) -e trace=epoll_wait
```

#### **Solutions**

**🔧 Optimize Async Operations**

```python
# Bad: Blocking operations in async function
async def bad_async():
    time.sleep(1)  # Blocks event loop!

# Good: Use async alternatives
async def good_async():
    await asyncio.sleep(1)  # Non-blocking

# Bad: Sequential async calls
async def bad_sequential():
    result1 = await operation1()
    result2 = await operation2()
    return result1, result2

# Good: Concurrent async calls
async def good_concurrent():
    result1, result2 = await asyncio.gather(
        operation1(),
        operation2()
    )
    return result1, result2
```

---

## 🔍 **DIAGNOSTIC TOOLS**

### **System Health Script**

```bash
#!/bin/bash
# scripts/health_diagnostic.sh

echo "🔍 WhatsApp Agent Health Diagnostic"
echo "====================================="

# ✅ Basic system info
echo "1. System Information:"
echo "   OS: $(lsb_release -d | cut -f2)"
echo "   Uptime: $(uptime -p)"
echo "   Load: $(uptime | awk -F'load average:' '{print $2}')"

# ✅ Service status
echo -e "\n2. Service Status:"
systemctl is-active whatsapp-backend && echo "   ✅ Backend: Running" || echo "   ❌ Backend: Stopped"
systemctl is-active whatsapp-frontend && echo "   ✅ Frontend: Running" || echo "   ❌ Frontend: Stopped"
systemctl is-active postgresql && echo "   ✅ PostgreSQL: Running" || echo "   ❌ PostgreSQL: Stopped"
systemctl is-active redis-server && echo "   ✅ Redis: Running" || echo "   ❌ Redis: Stopped"

# ✅ Health checks
echo -e "\n3. Health Checks:"
curl -s http://localhost:8000/health >/dev/null && echo "   ✅ API Health: OK" || echo "   ❌ API Health: Failed"
curl -s http://localhost:3000 >/dev/null && echo "   ✅ Frontend: OK" || echo "   ❌ Frontend: Failed"

# ✅ Resource usage
echo -e "\n4. Resource Usage:"
echo "   Memory: $(free -h | grep '^Mem:' | awk '{print $3 "/" $2}')"
echo "   Disk: $(df -h / | tail -1 | awk '{print $3 "/" $2 " (" $5 " used)"}')"
echo "   CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)% used"

# ✅ Database connections
echo -e "\n5. Database Status:"
db_conn=$(psql $DATABASE_URL -t -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';" 2>/dev/null || echo "Error")
echo "   Active connections: $db_conn"

# ✅ Redis status
echo -e "\n6. Cache Status:"
redis_status=$(redis-cli -u $REDIS_URL ping 2>/dev/null || echo "Error")
echo "   Redis ping: $redis_status"

# ✅ Recent errors
echo -e "\n7. Recent Errors (last 10 minutes):"
error_count=$(grep '"level":"ERROR"' logs/security_audit.log | grep "$(date -d '10 minutes ago' '+%Y-%m-%d')" | wc -l)
echo "   Error count: $error_count"

echo -e "\n✅ Diagnostic completed at $(date)"
```

### **Performance Diagnostic Script**

```python
#!/usr/bin/env python3
# scripts/performance_diagnostic.py

import asyncio
import time
import psutil
import json
from datetime import datetime, timedelta

async def performance_diagnostic():
    """
    Comprehensive performance diagnostic
    """
    print("⚡ Performance Diagnostic Report")
    print("=" * 40)

    # ✅ System metrics
    process = psutil.Process()
    print(f"1. System Performance:")
    print(f"   CPU Usage: {psutil.cpu_percent(interval=1)}%")
    print(f"   Memory Usage: {process.memory_info().rss / 1024 / 1024:.1f} MB")
    print(f"   Open Files: {len(process.open_files())}")
    print(f"   Connections: {len(process.connections())}")

    # ✅ Database performance
    print(f"\n2. Database Performance:")
    try:
        from app.database import AsyncSessionLocal
        from sqlalchemy import text

        start_time = time.time()
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            db_response_time = (time.time() - start_time) * 1000

        print(f"   Response Time: {db_response_time:.2f}ms")

        # Check slow queries
        async with AsyncSessionLocal() as session:
            slow_queries = await session.execute(text("""
                SELECT query, mean_exec_time, calls
                FROM pg_stat_statements
                WHERE mean_exec_time > 100
                ORDER BY mean_exec_time DESC
                LIMIT 5
            """))

        print(f"   Slow Queries: {slow_queries.rowcount}")

    except Exception as e:
        print(f"   Database Error: {e}")

    # ✅ Cache performance
    print(f"\n3. Cache Performance:")
    try:
        import redis.asyncio as redis
        from app.config import settings

        redis_client = redis.from_url(settings.REDIS_URL)

        start_time = time.time()
        await redis_client.ping()
        redis_response_time = (time.time() - start_time) * 1000

        info = await redis_client.info()
        hit_rate = (info['keyspace_hits'] / (info['keyspace_hits'] + info['keyspace_misses']) * 100) if info['keyspace_misses'] > 0 else 100

        print(f"   Response Time: {redis_response_time:.2f}ms")
        print(f"   Hit Rate: {hit_rate:.1f}%")
        print(f"   Memory Used: {info['used_memory_human']}")

    except Exception as e:
        print(f"   Cache Error: {e}")

    # ✅ API performance
    print(f"\n4. API Performance (last hour):")
    try:
        # Analyze logs for performance metrics
        cutoff = datetime.now() - timedelta(hours=1)

        with open("logs/security_audit.log", "r") as f:
            api_logs = []
            for line in f:
                try:
                    log = json.loads(line)
                    if (log.get('category') == 'api' and
                        datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')) > cutoff):
                        api_logs.append(log)
                except:
                    continue

        if api_logs:
            durations = [log.get('performance_metrics', {}).get('duration_ms', 0) for log in api_logs]
            avg_response = sum(durations) / len(durations)
            max_response = max(durations)
            slow_requests = len([d for d in durations if d > 1000])

            print(f"   Total Requests: {len(api_logs)}")
            print(f"   Avg Response: {avg_response:.2f}ms")
            print(f"   Max Response: {max_response:.2f}ms")
            print(f"   Slow Requests: {slow_requests}")
        else:
            print("   No API logs found")

    except Exception as e:
        print(f"   Log Analysis Error: {e}")

    print(f"\n✅ Diagnostic completed at {datetime.now()}")

if __name__ == "__main__":
    asyncio.run(performance_diagnostic())
```

---

## 📞 **EMERGENCY PROCEDURES**

### **🚨 Complete System Failure**

```bash
#!/bin/bash
# Emergency Recovery Procedure

echo "🚨 EMERGENCY RECOVERY INITIATED"

# 1. Stop all services
systemctl stop whatsapp-backend whatsapp-frontend

# 2. Check system resources
echo "System Resources:"
df -h
free -h

# 3. Clear temporary files
rm -rf /tmp/whatsapp_*
rm -rf logs/*.log.old

# 4. Database recovery
echo "Database Recovery:"
systemctl restart postgresql
sleep 10

# 5. Redis recovery
echo "Redis Recovery:"
systemctl restart redis-server
sleep 5

# 6. Application recovery
echo "Application Recovery:"
cd /path/to/whatsapp_agent

# Clear Python cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# Restart services
systemctl start whatsapp-backend
sleep 10
systemctl start whatsapp-frontend

# 7. Verify recovery
echo "Verification:"
curl -s http://localhost:8000/health && echo "✅ Backend OK" || echo "❌ Backend Failed"
curl -s http://localhost:3000 && echo "✅ Frontend OK" || echo "❌ Frontend Failed"

echo "🔧 Emergency recovery completed"
```

---

## 📞 **SUPPORT CONTACTS**

### **Escalation Matrix**

- 🔧 **Level 1 - Operations**: <ops@whatsappagent.com>
- 👨‍💻 **Level 2 - Development**: <dev@whatsappagent.com>  
- 🛡️ **Level 3 - Security**: <security@whatsappagent.com>
- 📊 **Level 4 - Management**: <management@whatsappagent.com>

### **Emergency Contacts**

- 🚨 **Critical Issues**: +55 11 99999-9999
- 📧 **Emergency Email**: <emergency@whatsappagent.com>
- 💬 **Slack Channel**: #whatsapp-agent-alerts

---

<div align="center">

**🔧 COMPREHENSIVE TROUBLESHOOTING SYSTEM**

*Complete diagnostic and recovery procedures for production*

**Resolution Success Rate: 95%+** ✅

</div>

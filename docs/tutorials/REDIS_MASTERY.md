# 🔴 Redis Mastery - Complete Guide

**From Zero to Hero with Redis**

---

## 📚 Table of Contents

1. [What is Redis?](#what-is-redis)
2. [Why Redis?](#why-redis)
3. [Redis Basics](#redis-basics)
4. [Data Types](#data-types)
5. [Common Operations](#common-operations)
6. [Caching Strategies](#caching-strategies)
7. [Pub/Sub](#pubsub)
8. [Redis with Python](#redis-with-python)
9. [Performance Tips](#performance-tips)
10. [Production Best Practices](#production-best-practices)

---

## 🎯 What is Redis?

**Redis** = **RE**mote **DI**ctionary **S**erver

It's an **in-memory data store** that's ridiculously fast.

### Simple Analogy

Think of Redis as **RAM with superpowers**:
- Your database (PostgreSQL) = Hard drive (slow, persistent)
- Redis = RAM (super fast, temporary)
- But Redis can also persist to disk!

### Key Features

- ⚡ **Blazing Fast** - Sub-millisecond response times
- 📦 **Multiple Data Types** - Strings, lists, sets, hashes, sorted sets
- 💾 **Persistence Options** - Can save to disk
- 🔄 **Pub/Sub** - Real-time messaging
- 🔁 **Replication** - Master-slave setup
- 🎯 **Atomic Operations** - Thread-safe by default

---

## 🤔 Why Redis?

### Redis vs Others

| Feature | Redis | Memcached | PostgreSQL | In-Memory Dict |
|---------|-------|-----------|------------|----------------|
| **Speed** | ⚡⚡⚡ | ⚡⚡⚡ | ⚡ | ⚡⚡⚡ |
| **Data Types** | 5+ types | Key-value only | Tables | Dict only |
| **Persistence** | ✅ Optional | ❌ No | ✅ Yes | ❌ Lost on restart |
| **Distributed** | ✅ Yes | ✅ Yes | ⚠️ Complex | ❌ Single process |
| **Pub/Sub** | ✅ Yes | ❌ No | ✅ LISTEN/NOTIFY | ❌ No |
| **Atomic Ops** | ✅ Yes | ⚠️ Limited | ✅ Yes | ❌ Need locks |

### When to Use Redis

✅ **Perfect for:**
- Caching database queries
- Session storage
- Rate limiting
- Real-time analytics
- Leaderboards
- Message queues
- Pub/Sub messaging

❌ **Not good for:**
- Primary data storage (use PostgreSQL)
- Large blobs (> 512MB)
- Complex queries (use database)
- Data that must never be lost

---

## 🏗️ Redis Basics

### Architecture

```
┌─────────────────────────────────┐
│     Client (Your App)            │
└──────────────┬──────────────────┘
               │ TCP (Port 6379)
               ▼
┌─────────────────────────────────┐
│       Redis Server               │
│  ┌───────────────────────────┐  │
│  │   Command Processor       │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │   In-Memory Data          │  │
│  │   (All in RAM!)           │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │   Persistence (Optional)  │  │
│  │   - RDB (Snapshots)       │  │
│  │   - AOF (Append-only log) │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

### Key Concepts

**Key-Value Store**
```
Key: "user:123:email"
Value: "user@example.com"
```

**Everything is a Key**
```redis
SET user:123:name "John Doe"
GET user:123:name
# Returns: "John Doe"
```

**Keys Can Expire**
```redis
SET session:abc123 "data" EX 3600  # Expires in 1 hour
```

**Single-Threaded (but fast!)**
- One command at a time
- No race conditions
- No locks needed
- Still handles 100k+ ops/sec

---

## 📦 Data Types

### 1. Strings

The most basic type. Can store anything: text, numbers, JSON, binary data.

```redis
# Set
SET user:123:email "user@example.com"

# Get
GET user:123:email
# Returns: "user@example.com"

# Set with expiration (3600 seconds = 1 hour)
SETEX session:abc123 3600 "session_data"

# Set only if doesn't exist
SETNX lock:resource1 "locked"

# Increment (atomic)
INCR views:page:home
INCRBY views:page:home 5

# Decrement
DECR stock:product:123

# Multiple get/set
MSET user:1:name "Alice" user:2:name "Bob"
MGET user:1:name user:2:name
```

**Use cases:**
- Caching HTML/JSON
- Counters (views, likes)
- Session storage
- Rate limiting

---

### 2. Hashes

Like Python dictionaries. Perfect for objects.

```redis
# Set field
HSET user:123 email "user@example.com"
HSET user:123 name "John Doe"

# Get field
HGET user:123 email
# Returns: "user@example.com"

# Get all fields
HGETALL user:123
# Returns: {email: "user@example.com", name: "John Doe"}

# Set multiple fields
HMSET user:123 email "user@example.com" name "John" age 30

# Get multiple fields
HMGET user:123 email name

# Check if field exists
HEXISTS user:123 email

# Delete field
HDEL user:123 age

# Increment field
HINCRBY user:123 login_count 1
```

**Use cases:**
- User profiles
- Product details
- Configuration objects

---

### 3. Lists

Ordered collections. Like Python lists.

```redis
# Push to end
RPUSH queue:jobs "job1"
RPUSH queue:jobs "job2"

# Push to beginning
LPUSH queue:priority "urgent_job"

# Pop from end
RPOP queue:jobs
# Returns: "job2"

# Pop from beginning
LPOP queue:jobs
# Returns: "job1"

# Get range
LRANGE queue:jobs 0 10  # First 10 items

# Get length
LLEN queue:jobs

# Trim (keep only range)
LTRIM queue:jobs 0 99  # Keep only 100 items

# Blocking pop (wait for item)
BLPOP queue:jobs 5  # Wait up to 5 seconds
```

**Use cases:**
- Task queues
- Activity feeds
- Recent items

---

### 4. Sets

Unordered unique collections. Like Python sets.

```redis
# Add members
SADD tags:post:123 "python" "fastapi" "tutorial"

# Get all members
SMEMBERS tags:post:123
# Returns: ["python", "fastapi", "tutorial"]

# Check membership
SISMEMBER tags:post:123 "python"
# Returns: 1 (true)

# Remove member
SREM tags:post:123 "tutorial"

# Get count
SCARD tags:post:123

# Random member
SRANDMEMBER tags:post:123

# Pop random member
SPOP tags:post:123

# Set operations
SADD set1 "a" "b" "c"
SADD set2 "b" "c" "d"

SINTER set1 set2        # Intersection: ["b", "c"]
SUNION set1 set2        # Union: ["a", "b", "c", "d"]
SDIFF set1 set2         # Difference: ["a"]
```

**Use cases:**
- Tags
- Unique visitors
- Followers/Following
- Permissions

---

### 5. Sorted Sets (ZSets)

Sets with scores. Automatically sorted.

```redis
# Add with score
ZADD leaderboard 100 "alice"
ZADD leaderboard 200 "bob"
ZADD leaderboard 150 "charlie"

# Get rank (0-based)
ZRANK leaderboard "alice"
# Returns: 0 (lowest score)

# Get top N
ZREVRANGE leaderboard 0 9  # Top 10
# Returns: ["bob", "charlie", "alice"]

# Get with scores
ZREVRANGE leaderboard 0 9 WITHSCORES

# Get score
ZSCORE leaderboard "bob"
# Returns: 200

# Increment score
ZINCRBY leaderboard 50 "alice"

# Get by score range
ZRANGEBYSCORE leaderboard 100 200

# Count in range
ZCOUNT leaderboard 100 200

# Remove
ZREM leaderboard "alice"

# Remove by rank
ZREMRANGEBYRANK leaderboard 0 0  # Remove lowest
```

**Use cases:**
- Leaderboards
- Priority queues
- Time-series data
- Rate limiting (sorted by timestamp)

---

## 🔨 Common Operations

### Key Management

```redis
# Check if key exists
EXISTS user:123
# Returns: 1 (exists) or 0 (doesn't exist)

# Delete key
DEL user:123

# Delete multiple
DEL user:1 user:2 user:3

# Set expiration (seconds)
EXPIRE user:123 3600

# Set expiration (milliseconds)
PEXPIRE user:123 3600000

# Set expiration at timestamp
EXPIREAT user:123 1735660800

# Get time to live
TTL user:123
# Returns: seconds remaining, or -1 (no expiration), -2 (doesn't exist)

# Remove expiration
PERSIST user:123

# Rename key
RENAME old_key new_key

# Get all keys matching pattern
KEYS user:*  # WARNING: Slow, don't use in production!

# Better: Scan
SCAN 0 MATCH user:* COUNT 100

# Get key type
TYPE user:123
# Returns: string, hash, list, set, zset, or none
```

### Database Management

```redis
# Select database (0-15)
SELECT 1

# Get current database size
DBSIZE

# Flush current database
FLUSHDB

# Flush all databases
FLUSHALL

# Get server info
INFO

# Get stats
INFO stats
```

---

## 💾 Caching Strategies

### 1. Cache-Aside (Lazy Loading)

**Most common pattern.**

```python
def get_user(user_id):
    # Try cache first
    cached = redis.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)
    
    # Cache miss - query database
    user = db.query(User).filter(User.id == user_id).first()
    
    # Store in cache for 1 hour
    redis.setex(
        f"user:{user_id}",
        3600,
        json.dumps(user)
    )
    
    return user
```

**Pros:**
- ✅ Only cache what's needed
- ✅ Cache doesn't become stale easily

**Cons:**
- ❌ Cache miss penalty (slower first request)

---

### 2. Write-Through

**Update cache when writing to database.**

```python
def update_user(user_id, data):
    # Update database
    db.query(User).filter(User.id == user_id).update(data)
    db.commit()
    
    # Update cache
    user = db.query(User).filter(User.id == user_id).first()
    redis.setex(
        f"user:{user_id}",
        3600,
        json.dumps(user)
    )
```

**Pros:**
- ✅ Cache always up-to-date

**Cons:**
- ❌ Write penalty (slower writes)
- ❌ Wasted writes if data never read

---

### 3. Write-Behind (Write-Back)

**Write to cache first, sync to database later.**

```python
def update_user(user_id, data):
    # Update cache immediately
    redis.hset(f"user:{user_id}", mapping=data)
    
    # Queue for database write
    redis.rpush("write_queue", json.dumps({
        "user_id": user_id,
        "data": data
    }))
    
    # Background worker syncs to database
```

**Pros:**
- ✅ Super fast writes

**Cons:**
- ❌ Risk of data loss
- ❌ Complex to implement

---

### 4. Refresh-Ahead

**Refresh popular data before it expires.**

```python
def get_user(user_id):
    cached = redis.get(f"user:{user_id}")
    ttl = redis.ttl(f"user:{user_id}")
    
    # If expiring soon, refresh
    if ttl < 300:  # Less than 5 minutes
        # Async refresh
        queue_refresh(user_id)
    
    return json.loads(cached)
```

**Pros:**
- ✅ No cache miss penalty for hot data

**Cons:**
- ❌ Complex logic

---

### Cache Invalidation

**3 Strategies:**

**1. TTL (Time-based)**
```python
# Simple: Expire after 1 hour
redis.setex("user:123", 3600, data)
```

**2. Event-based**
```python
# Invalidate when data changes
def update_user(user_id):
    db.update(...)
    redis.delete(f"user:{user_id}")  # Clear cache
```

**3. Tag-based**
```python
# Invalidate related items
def update_model(model_id):
    db.update(...)
    # Clear all caches with this tag
    tags = redis.smembers(f"cache_tags:model:{model_id}")
    for tag in tags:
        redis.delete(tag)
```

---

## 📢 Pub/Sub

**Real-time messaging between processes.**

### Publishing

```python
import redis

r = redis.Redis()

# Publish message
r.publish("notifications", "New model uploaded!")
```

### Subscribing

```python
import redis

r = redis.Redis()
pubsub = r.pubsub()

# Subscribe to channel
pubsub.subscribe("notifications")

# Listen for messages
for message in pubsub.listen():
    if message['type'] == 'message':
        print(f"Received: {message['data']}")
```

### Pattern Subscriptions

```python
# Subscribe to pattern
pubsub.psubscribe("user:*:notifications")

# Matches:
# user:123:notifications
# user:456:notifications
```

### Use Cases

- Real-time notifications
- Chat applications
- Live updates
- Event broadcasting
- Microservice communication

---

## 🐍 Redis with Python

### Installation

```bash
pip install redis
```

### Basic Usage

```python
import redis

# Connect
r = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True  # Auto-decode bytes to strings
)

# Or from URL
r = redis.from_url('redis://localhost:6379/0')

# Test connection
r.ping()  # Returns: True

# String operations
r.set('key', 'value')
r.get('key')  # Returns: 'value'

r.setex('key', 3600, 'value')  # With expiration

# Hash operations
r.hset('user:123', 'email', 'user@example.com')
r.hget('user:123', 'email')
r.hgetall('user:123')

# List operations
r.rpush('queue', 'item1')
r.lpop('queue')

# Set operations
r.sadd('tags', 'python', 'redis')
r.smembers('tags')

# Sorted set operations
r.zadd('leaderboard', {'alice': 100, 'bob': 200})
r.zrevrange('leaderboard', 0, 9)
```

### Connection Pooling

```python
import redis

# Create pool
pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    max_connections=20,
    decode_responses=True
)

# Use pool
r = redis.Redis(connection_pool=pool)
```

### Pipeline (Batch Operations)

```python
# Without pipeline (4 round trips)
r.set('key1', 'value1')
r.set('key2', 'value2')
r.get('key1')
r.get('key2')

# With pipeline (1 round trip)
pipe = r.pipeline()
pipe.set('key1', 'value1')
pipe.set('key2', 'value2')
pipe.get('key1')
pipe.get('key2')
results = pipe.execute()  # Returns: [True, True, 'value1', 'value2']
```

### Transactions

```python
# Atomic operations
pipe = r.pipeline(transaction=True)
pipe.set('balance:1', 100)
pipe.set('balance:2', 200)
pipe.execute()
# Both or neither
```

### Lua Scripts

```python
# Atomic complex operations
script = """
local current = redis.call('GET', KEYS[1])
if tonumber(current) >= tonumber(ARGV[1]) then
    return redis.call('DECRBY', KEYS[1], ARGV[1])
else
    return -1
end
"""

# Register script
deduct = r.register_script(script)

# Execute
result = deduct(keys=['balance'], args=[50])
```

---

## ⚡ Performance Tips

### 1. Use Pipelining

```python
# Slow: 1000 round trips
for i in range(1000):
    r.set(f'key:{i}', f'value:{i}')

# Fast: 1 round trip
pipe = r.pipeline()
for i in range(1000):
    pipe.set(f'key:{i}', f'value:{i}')
pipe.execute()
```

### 2. Use Hashes for Objects

```python
# Memory inefficient (3 keys)
r.set('user:123:name', 'John')
r.set('user:123:email', 'john@example.com')
r.set('user:123:age', 30)

# Memory efficient (1 key)
r.hset('user:123', mapping={
    'name': 'John',
    'email': 'john@example.com',
    'age': 30
})
```

### 3. Use Appropriate Data Types

```python
# Bad: String for set
r.set('tags', 'python,redis,fastapi')

# Good: Actual set
r.sadd('tags', 'python', 'redis', 'fastapi')
```

### 4. Set Expiration

```python
# Always set TTL to prevent memory leaks
r.setex('cache:key', 3600, 'value')
```

### 5. Use SCAN Instead of KEYS

```python
# Bad: Blocks server
keys = r.keys('user:*')

# Good: Iterative
cursor = 0
while True:
    cursor, keys = r.scan(cursor, match='user:*', count=100)
    # Process keys
    if cursor == 0:
        break
```

---

## 🏭 Production Best Practices

### 1. Persistence Configuration

**RDB (Snapshots)**
```redis
# Save every 60 seconds if 1000+ keys changed
SAVE 60 1000
```

**AOF (Append-Only File)**
```redis
# Log every write command
appendonly yes
appendfsync everysec  # or always (slower) or no (faster)
```

**Recommendation:** Use both!

---

### 2. Memory Management

```redis
# Set max memory
maxmemory 2gb

# Eviction policy
maxmemory-policy allkeys-lru  # Remove least recently used

# Options:
# - noeviction: Return errors when memory full
# - allkeys-lru: Remove any key, least recently used
# - volatile-lru: Remove keys with TTL, least recently used
# - allkeys-random: Remove random key
# - volatile-random: Remove random key with TTL
# - volatile-ttl: Remove key with shortest TTL
```

---

### 3. Security

```bash
# Set password
requirepass your_strong_password

# Bind to localhost only (if same server)
bind 127.0.0.1

# Disable dangerous commands
rename-command FLUSHALL ""
rename-command FLUSHDB ""
rename-command CONFIG "CONFIG_abc123"
```

---

### 4. Monitoring

```python
# Get stats
info = r.info()

# Memory usage
memory = info['used_memory_human']

# Hit rate
hits = info['keyspace_hits']
misses = info['keyspace_misses']
hit_rate = hits / (hits + misses) if (hits + misses) > 0 else 0

# Connected clients
clients = info['connected_clients']

# Monitor commands (debugging only)
r.monitor()
```

---

### 5. High Availability

**Master-Slave Replication**
```redis
# On slave
REPLICAOF master_host master_port
```

**Redis Sentinel** (automatic failover)
**Redis Cluster** (sharding + replication)

---

## 🎯 Common Patterns

### Rate Limiting

```python
def is_rate_limited(user_id: str, limit: int = 100) -> bool:
    """
    Allow {limit} requests per minute
    """
    key = f"rate_limit:{user_id}:{int(time.time() / 60)}"
    
    current = r.incr(key)
    
    if current == 1:
        r.expire(key, 60)  # Expire after 1 minute
    
    return current > limit
```

### Distributed Lock

```python
import uuid

def acquire_lock(resource: str, timeout: int = 10) -> str:
    """
    Acquire distributed lock
    """
    lock_id = str(uuid.uuid4())
    
    # Set only if not exists, with expiration
    acquired = r.set(
        f"lock:{resource}",
        lock_id,
        nx=True,  # Only set if not exists
        ex=timeout  # Expiration
    )
    
    return lock_id if acquired else None

def release_lock(resource: str, lock_id: str):
    """
    Release lock (only if we own it)
    """
    script = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    """
    
    release = r.register_script(script)
    release(keys=[f"lock:{resource}"], args=[lock_id])
```

### Leaderboard

```python
def update_score(user_id: str, score: int):
    """Add/update user score"""
    r.zadd('leaderboard', {user_id: score})

def get_top_players(n: int = 10):
    """Get top N players"""
    return r.zrevrange('leaderboard', 0, n-1, withscores=True)

def get_user_rank(user_id: str):
    """Get user's rank (1-based)"""
    rank = r.zrevrank('leaderboard', user_id)
    return rank + 1 if rank is not None else None
```

### Session Storage

```python
import json

def create_session(user_id: str, data: dict) -> str:
    """Create session"""
    session_id = str(uuid.uuid4())
    
    r.setex(
        f"session:{session_id}",
        3600,  # 1 hour
        json.dumps({'user_id': user_id, **data})
    )
    
    return session_id

def get_session(session_id: str) -> dict:
    """Get session data"""
    data = r.get(f"session:{session_id}")
    return json.loads(data) if data else None

def destroy_session(session_id: str):
    """Logout"""
    r.delete(f"session:{session_id}")
```

---

## 📚 Quick Reference

### Most Used Commands

```redis
# Strings
SET key value
GET key
DEL key
EXISTS key
EXPIRE key seconds
TTL key

# Hashes
HSET key field value
HGET key field
HGETALL key
HDEL key field

# Lists
LPUSH key value
RPUSH key value
LPOP key
RPOP key
LRANGE key start stop

# Sets
SADD key member
SMEMBERS key
SISMEMBER key member
SCARD key

# Sorted Sets
ZADD key score member
ZRANGE key start stop
ZREVRANGE key start stop
ZSCORE key member
ZRANK key member
```

---

## 🔗 Related Guides

- [Phase 4: Prediction Guide](../PHASE_4_PREDICTION_GUIDE.md) - Redis caching for predictions
- [Phase 6: Advanced Features](../PHASE_6_ADVANCED_GUIDE.md) - Rate limiting with Redis
- [Docker Mastery](./DOCKER_MASTERY.md) - Running Redis in Docker

---

**Created:** October 23, 2025  
**Last Updated:** October 23, 2025

**TL;DR**: Redis is super fast in-memory storage. Use it for caching, sessions, rate limiting, and real-time features. Not for primary data storage!

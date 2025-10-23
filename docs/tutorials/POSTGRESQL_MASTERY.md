# 🐘 PostgreSQL Mastery - Complete Guide

**From Zero to Hero with PostgreSQL**

---

## 📚 Table of Contents

1. [What is PostgreSQL?](#what-is-postgresql)
2. [Why PostgreSQL?](#why-postgresql)
3. [PostgreSQL Basics](#postgresql-basics)
4. [Data Types](#data-types)
5. [CRUD Operations](#crud-operations)
6. [Relationships](#relationships)
7. [Indexes](#indexes)
8. [Transactions](#transactions)
9. [Advanced Queries](#advanced-queries)
10. [Performance Optimization](#performance-optimization)
11. [Backup & Recovery](#backup--recovery)
12. [PostgreSQL with Python](#postgresql-with-python)

---

## 🎯 What is PostgreSQL?

**PostgreSQL** (often called "Postgres") is a powerful, open-source relational database.

### Simple Analogy

Think of PostgreSQL as an **Excel spreadsheet on steroids**:
- Tables = Sheets
- Rows = Data entries
- Columns = Fields
- But with superpowers (transactions, relationships, millions of rows)

### Key Features

- ✅ **ACID Compliant** - Data integrity guaranteed
- ✅ **Open Source** - Free forever
- ✅ **Powerful** - Handles billions of rows
- ✅ **JSON Support** - Store structured and unstructured data
- ✅ **Extensions** - Add features (PostGIS, pg_trgm, etc.)
- ✅ **Mature** - 30+ years of development

---

## 🤔 Why PostgreSQL?

### PostgreSQL vs Others

| Feature | PostgreSQL | MySQL | SQLite | MongoDB |
|---------|-----------|-------|--------|---------|
| **Type** | Relational | Relational | Relational | NoSQL |
| **ACID** | ✅ Full | ⚠️ Partial | ✅ Full | ❌ Limited |
| **JSON** | ✅ Native | ⚠️ Basic | ❌ No | ✅ Native |
| **Performance** | 🚀 Excellent | 🚀 Good | ⚡ Fast (small) | 🚀 Good |
| **Concurrency** | ✅ MVCC | ⚠️ Locking | ❌ Limited | ✅ Good |
| **Best For** | Everything | Web apps | Mobile/Embedded | Flexible schemas |

### When to Use PostgreSQL

✅ **Use PostgreSQL when:**
- Need data integrity (ACID)
- Complex queries and relationships
- Large datasets (millions+ rows)
- Multiple concurrent users
- Need JSON + relational data

❌ **Consider alternatives when:**
- Embedded (SQLite)
- Simple key-value (Redis)
- Flexible schema constantly changing (MongoDB)

---

## 🏗️ PostgreSQL Basics

### Architecture

```
┌─────────────────────────────────┐
│        Client Application        │
│      (Your Python/FastAPI)       │
└──────────────┬──────────────────┘
               │ TCP/IP (Port 5432)
               ▼
┌─────────────────────────────────┐
│      PostgreSQL Server           │
│  ┌───────────────────────────┐  │
│  │   Connection Manager      │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │   Query Parser            │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │   Optimizer               │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │   Executor                │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │   Storage (Tables)        │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

### Key Concepts

**Database** = Container for all your data
```sql
CREATE DATABASE myapp;
```

**Schema** = Namespace within a database (default: public)
```sql
CREATE SCHEMA app;
```

**Table** = Where data is stored
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL
);
```

**Row** = Single record
```
| id | email            |
|----|------------------|
| 1  | user@example.com |
```

**Column** = Field in a record
```
email, password, created_at
```

---

## 📦 Data Types

### Common Data Types

#### Numbers

```sql
-- Integers
SMALLINT    -- -32,768 to 32,767
INTEGER     -- -2 billion to 2 billion
BIGINT      -- -9 quintillion to 9 quintillion
SERIAL      -- Auto-incrementing integer

-- Decimals
NUMERIC(10, 2)  -- 10 digits, 2 after decimal (exact)
DECIMAL(10, 2)  -- Same as NUMERIC
REAL            -- 6 decimal digits precision
DOUBLE PRECISION -- 15 decimal digits precision

-- Examples
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    price NUMERIC(10, 2),  -- $99999999.99
    rating REAL,            -- 4.5
    views BIGINT           -- 1000000000
);
```

#### Text

```sql
-- Text types
CHAR(10)        -- Fixed length (always 10 chars)
VARCHAR(100)    -- Variable length (max 100)
TEXT            -- Unlimited length

-- Best practice: Use TEXT
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    slug VARCHAR(100) UNIQUE  -- Only when you need limit
);
```

#### Date/Time

```sql
DATE            -- 2025-10-23
TIME            -- 14:30:00
TIMESTAMP       -- 2025-10-23 14:30:00
TIMESTAMPTZ     -- 2025-10-23 14:30:00+00 (with timezone)

-- Always use TIMESTAMPTZ for user data!
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Boolean

```sql
BOOLEAN  -- true/false

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false
);
```

#### JSON

```sql
JSON     -- Text-based JSON (slower)
JSONB    -- Binary JSON (faster, indexable)

-- Always use JSONB
CREATE TABLE models (
    id SERIAL PRIMARY KEY,
    metadata JSONB
);

-- Insert
INSERT INTO models (metadata) VALUES 
('{"framework": "sklearn", "version": "1.0"}');

-- Query
SELECT * FROM models WHERE metadata->>'framework' = 'sklearn';
```

#### UUID

```sql
UUID  -- Universally Unique Identifier

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL
);
```

#### Arrays

```sql
TEXT[]      -- Array of text
INTEGER[]   -- Array of integers

CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    tags TEXT[]
);

-- Insert
INSERT INTO posts (tags) VALUES (ARRAY['python', 'fastapi', 'tutorial']);

-- Query
SELECT * FROM posts WHERE 'python' = ANY(tags);
```

---

## 🔨 CRUD Operations

### Create (INSERT)

```sql
-- Single row
INSERT INTO users (email, password) 
VALUES ('user@example.com', 'hashed_password');

-- Multiple rows
INSERT INTO users (email, password) VALUES 
    ('user1@example.com', 'pass1'),
    ('user2@example.com', 'pass2'),
    ('user3@example.com', 'pass3');

-- Return inserted data
INSERT INTO users (email, password) 
VALUES ('new@example.com', 'pass')
RETURNING id, email, created_at;

-- Insert from SELECT
INSERT INTO archived_users 
SELECT * FROM users WHERE created_at < '2020-01-01';
```

### Read (SELECT)

```sql
-- All rows, all columns
SELECT * FROM users;

-- Specific columns
SELECT id, email FROM users;

-- With condition
SELECT * FROM users WHERE is_active = true;

-- Multiple conditions
SELECT * FROM users 
WHERE is_active = true 
  AND created_at > '2025-01-01';

-- Pattern matching
SELECT * FROM users WHERE email LIKE '%@gmail.com';

-- Sorting
SELECT * FROM users ORDER BY created_at DESC;

-- Limit
SELECT * FROM users LIMIT 10 OFFSET 20;

-- Counting
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM users WHERE is_active = true;

-- Distinct
SELECT DISTINCT email_domain FROM users;

-- Aggregation
SELECT 
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE is_active = true) as active,
    AVG(age) as avg_age,
    MAX(created_at) as latest_signup
FROM users;

-- Group by
SELECT 
    email_domain,
    COUNT(*) as count
FROM users
GROUP BY email_domain
HAVING COUNT(*) > 10
ORDER BY count DESC;
```

### Update (UPDATE)

```sql
-- Update single row
UPDATE users 
SET email = 'newemail@example.com' 
WHERE id = 1;

-- Update multiple columns
UPDATE users 
SET 
    email = 'new@example.com',
    is_active = false,
    updated_at = NOW()
WHERE id = 1;

-- Update with condition
UPDATE users 
SET is_active = false 
WHERE last_login < NOW() - INTERVAL '1 year';

-- Update and return
UPDATE users 
SET is_active = true 
WHERE id = 1
RETURNING *;

-- Conditional update
UPDATE products 
SET price = price * 0.9 
WHERE category = 'electronics';
```

### Delete (DELETE)

```sql
-- Delete single row
DELETE FROM users WHERE id = 1;

-- Delete with condition
DELETE FROM users WHERE is_active = false;

-- Delete and return
DELETE FROM users 
WHERE id = 1 
RETURNING *;

-- Delete all (DANGEROUS!)
DELETE FROM users;

-- Truncate (faster, can't rollback)
TRUNCATE TABLE users;

-- Cascade delete
DELETE FROM users WHERE id = 1;  -- Also deletes related models
```

---

## 🔗 Relationships

### One-to-Many

**One user has many models**

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL
);

CREATE TABLE models (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL
);

-- Insert
INSERT INTO users (email) VALUES ('user@example.com') RETURNING id;
-- Returns: id = 1

INSERT INTO models (user_id, name) VALUES 
    (1, 'Model 1'),
    (1, 'Model 2');

-- Query (JOIN)
SELECT 
    users.email,
    models.name
FROM users
JOIN models ON models.user_id = users.id
WHERE users.id = 1;
```

### Many-to-Many

**Models have many tags, tags have many models**

```sql
CREATE TABLE models (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- Junction table
CREATE TABLE model_tags (
    model_id INTEGER REFERENCES models(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (model_id, tag_id)
);

-- Insert
INSERT INTO models (name) VALUES ('Classifier') RETURNING id;  -- id = 1
INSERT INTO tags (name) VALUES ('sklearn'), ('production');

INSERT INTO model_tags (model_id, tag_id) VALUES 
    (1, 1),  -- Classifier + sklearn
    (1, 2);  -- Classifier + production

-- Query
SELECT 
    models.name,
    array_agg(tags.name) as tags
FROM models
JOIN model_tags ON model_tags.model_id = models.id
JOIN tags ON tags.id = model_tags.tag_id
GROUP BY models.id, models.name;
```

### Foreign Key Options

```sql
-- CASCADE: Delete related rows
REFERENCES users(id) ON DELETE CASCADE

-- SET NULL: Set to NULL when parent deleted
REFERENCES users(id) ON DELETE SET NULL

-- RESTRICT: Prevent deletion if has children (default)
REFERENCES users(id) ON DELETE RESTRICT

-- SET DEFAULT: Set to default value
REFERENCES users(id) ON DELETE SET DEFAULT
```

---

## 🚀 Indexes

### What Are Indexes?

Think of an index like a **book index**:
- Without index: Read entire book to find topic
- With index: Jump directly to page

### When to Create Indexes

✅ **Create index for:**
- Primary keys (automatic)
- Foreign keys
- Columns in WHERE clauses
- Columns in JOIN conditions
- Columns in ORDER BY

❌ **Don't index:**
- Small tables (< 1000 rows)
- Columns that change frequently
- Columns with low cardinality (few unique values)

### Creating Indexes

```sql
-- Simple index
CREATE INDEX idx_users_email ON users(email);

-- Unique index
CREATE UNIQUE INDEX idx_users_email ON users(email);

-- Multi-column index
CREATE INDEX idx_models_user_status ON models(user_id, status);

-- Partial index (only index some rows)
CREATE INDEX idx_active_users ON users(email) WHERE is_active = true;

-- Expression index
CREATE INDEX idx_lower_email ON users(LOWER(email));

-- Full-text search index
CREATE INDEX idx_posts_search ON posts USING gin(to_tsvector('english', content));
```

### Viewing Indexes

```sql
-- Show all indexes
\di

-- Show indexes for table
SELECT * FROM pg_indexes WHERE tablename = 'users';

-- Drop index
DROP INDEX idx_users_email;
```

---

## 💾 Transactions

### What Are Transactions?

**Transaction** = Group of operations that succeed or fail together

**ACID Properties:**
- **A**tomic - All or nothing
- **C**onsistent - Valid state always
- **I**solated - Concurrent transactions don't interfere
- **D**urable - Committed changes persist

### Using Transactions

```sql
-- Start transaction
BEGIN;

-- Operations
INSERT INTO users (email) VALUES ('user@example.com');
INSERT INTO models (user_id, name) VALUES (1, 'Model 1');

-- Commit (save changes)
COMMIT;

-- Or rollback (undo changes)
ROLLBACK;
```

### Real-World Example

```sql
-- Transfer money between accounts
BEGIN;

-- Deduct from account 1
UPDATE accounts SET balance = balance - 100 WHERE id = 1;

-- Add to account 2
UPDATE accounts SET balance = balance + 100 WHERE id = 2;

-- Only commit if both succeed
COMMIT;

-- If any error, ROLLBACK automatically happens
```

### Savepoints

```sql
BEGIN;

INSERT INTO users (email) VALUES ('user1@example.com');

SAVEPOINT sp1;

INSERT INTO users (email) VALUES ('user2@example.com');

-- Undo only to savepoint
ROLLBACK TO sp1;

-- Commit first insert only
COMMIT;
```

---

## 🔍 Advanced Queries

### Subqueries

```sql
-- Find users with more than 5 models
SELECT * FROM users 
WHERE id IN (
    SELECT user_id FROM models 
    GROUP BY user_id 
    HAVING COUNT(*) > 5
);

-- Scalar subquery
SELECT 
    name,
    (SELECT COUNT(*) FROM predictions WHERE model_id = models.id) as pred_count
FROM models;
```

### Common Table Expressions (CTE)

```sql
-- WITH clause for readability
WITH active_users AS (
    SELECT id, email FROM users WHERE is_active = true
),
recent_models AS (
    SELECT * FROM models WHERE created_at > NOW() - INTERVAL '30 days'
)
SELECT 
    active_users.email,
    COUNT(recent_models.id) as model_count
FROM active_users
LEFT JOIN recent_models ON recent_models.user_id = active_users.id
GROUP BY active_users.id, active_users.email;
```

### Window Functions

```sql
-- Row number
SELECT 
    name,
    created_at,
    ROW_NUMBER() OVER (ORDER BY created_at DESC) as row_num
FROM models;

-- Rank
SELECT 
    name,
    score,
    RANK() OVER (ORDER BY score DESC) as rank
FROM models;

-- Running total
SELECT 
    date,
    revenue,
    SUM(revenue) OVER (ORDER BY date) as running_total
FROM sales;

-- Partition
SELECT 
    user_id,
    name,
    created_at,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) as user_model_num
FROM models;
```

### JSON Operations

```sql
-- Query JSON
SELECT * FROM models WHERE metadata->>'framework' = 'sklearn';

-- Extract value
SELECT metadata->>'version' as version FROM models;

-- Check key exists
SELECT * FROM models WHERE metadata ? 'gpu_enabled';

-- Update JSON
UPDATE models 
SET metadata = jsonb_set(metadata, '{version}', '"2.0"')
WHERE id = 1;

-- Merge JSON
UPDATE models 
SET metadata = metadata || '{"status": "deployed"}'::jsonb
WHERE id = 1;
```

---

## ⚡ Performance Optimization

### EXPLAIN

```sql
-- See query plan
EXPLAIN SELECT * FROM users WHERE email = 'user@example.com';

-- With execution stats
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'user@example.com';
```

### Optimization Tips

**1. Use Indexes**
```sql
CREATE INDEX idx_users_email ON users(email);
```

**2. Limit Results**
```sql
SELECT * FROM users LIMIT 100;  -- Good
SELECT * FROM users;             -- Bad if millions of rows
```

**3. Use Specific Columns**
```sql
SELECT id, email FROM users;  -- Good
SELECT * FROM users;           -- Bad
```

**4. Avoid N+1 Queries**
```sql
-- Bad (N+1)
SELECT * FROM users;  -- 1 query
-- Then for each user:
SELECT * FROM models WHERE user_id = ?;  -- N queries

-- Good (1 query)
SELECT 
    users.*,
    json_agg(models.*) as models
FROM users
LEFT JOIN models ON models.user_id = users.id
GROUP BY users.id;
```

**5. Use Connection Pooling**
```python
# With SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10
)
```

---

## 💾 Backup & Recovery

### Backup Database

```bash
# Full backup
pg_dump mydb > backup.sql

# Compressed backup
pg_dump mydb | gzip > backup.sql.gz

# Backup with Docker
docker exec postgres_container pg_dump -U postgres mydb > backup.sql

# Backup specific table
pg_dump -t users mydb > users_backup.sql
```

### Restore Database

```bash
# Restore
psql mydb < backup.sql

# Restore compressed
gunzip < backup.sql.gz | psql mydb

# Restore with Docker
cat backup.sql | docker exec -i postgres_container psql -U postgres mydb
```

### Automated Backups

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump mydb | gzip > /backups/mydb_$DATE.sql.gz

# Keep only last 7 days
find /backups -name "*.sql.gz" -mtime +7 -delete
```

---

## 🐍 PostgreSQL with Python

### Using psycopg2 (Raw SQL)

```python
import psycopg2

# Connect
conn = psycopg2.connect(
    host="localhost",
    database="mydb",
    user="postgres",
    password="password"
)

# Execute query
cur = conn.cursor()
cur.execute("SELECT * FROM users WHERE email = %s", ('user@example.com',))
rows = cur.fetchall()

# Insert
cur.execute(
    "INSERT INTO users (email, password) VALUES (%s, %s) RETURNING id",
    ('new@example.com', 'hashed_pass')
)
user_id = cur.fetchone()[0]
conn.commit()

# Close
cur.close()
conn.close()
```

### Using SQLAlchemy (ORM)

```python
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Setup
engine = create_engine('postgresql://user:pass@localhost/mydb')
Base = declarative_base()
Session = sessionmaker(bind=engine)

# Models
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    models = relationship("Model", back_populates="user")

class Model(Base):
    __tablename__ = 'models'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String)
    user = relationship("User", back_populates="models")

# Create tables
Base.metadata.create_all(engine)

# Use
session = Session()

# Create
user = User(email='user@example.com')
session.add(user)
session.commit()

# Query
user = session.query(User).filter_by(email='user@example.com').first()

# Update
user.email = 'newemail@example.com'
session.commit()

# Delete
session.delete(user)
session.commit()
```

---

## 📚 Best Practices

### Do's ✅

1. **Always use parameterized queries** (prevent SQL injection)
```python
# Good
cur.execute("SELECT * FROM users WHERE email = %s", (email,))

# Bad
cur.execute(f"SELECT * FROM users WHERE email = '{email}'")
```

2. **Use transactions for multiple operations**
3. **Index frequently queried columns**
4. **Use TIMESTAMPTZ for timestamps**
5. **Use TEXT instead of VARCHAR**
6. **Use JSONB instead of JSON**
7. **Regular backups**

### Don'ts ❌

1. **Don't use SELECT *** in production
2. **Don't expose database errors to users**
3. **Don't store sensitive data in plain text**
4. **Don't use sequential IDs for public URLs**
5. **Don't forget to close connections**
6. **Don't create indexes on everything**

---

## 🎯 Common Patterns

### Soft Delete

```sql
ALTER TABLE users ADD COLUMN deleted_at TIMESTAMPTZ;

-- Delete (mark as deleted)
UPDATE users SET deleted_at = NOW() WHERE id = 1;

-- Query (exclude deleted)
SELECT * FROM users WHERE deleted_at IS NULL;
```

### Audit Trail

```sql
ALTER TABLE users ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE users ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();
```

### Pagination

```sql
-- Offset pagination (simple but slow for large offsets)
SELECT * FROM users ORDER BY id LIMIT 20 OFFSET 40;

-- Cursor pagination (fast)
SELECT * FROM users WHERE id > 40 ORDER BY id LIMIT 20;
```

---

## 🔗 Related Guides

- [Phase 1: Setup Guide](../PHASE_1_SETUP_GUIDE.md) - PostgreSQL with Docker
- [Pydantic & ORM Mastery](./PYDANTIC_ORM_MASTERY.md) - SQLAlchemy deep dive
- [Phase 8: Production Guide](../PHASE_8_PRODUCTION_GUIDE.md) - Performance optimization

---

**Created:** October 23, 2025  
**Last Updated:** October 23, 2025

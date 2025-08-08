"""
Persistent Storage Backends for Production Deployment
Provides Redis and PostgreSQL storage implementations to replace InMemoryStorage
"""

import json
import os
import time
import uuid
from typing import Dict, Iterable, Optional, Tuple

try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

try:
    import asyncpg
    import asyncio
    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False

from .episodic_memory import StorageBackend


class RedisStorageBackend(StorageBackend):
    """Redis-based persistent storage for episodic memory."""
    
    def __init__(
        self, 
        redis_url: Optional[str] = None, 
        key_prefix: str = "episodic_memory",
        ttl: Optional[int] = None
    ):
        if not HAS_REDIS:
            raise ImportError("redis package is required for RedisStorageBackend")
            
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.key_prefix = key_prefix
        self.ttl = ttl
        self._client = redis.from_url(self.redis_url, decode_responses=True)
        
        # Test connection
        try:
            self._client.ping()
        except redis.RedisError as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")

    def _make_key(self, record_id: str) -> str:
        """Create Redis key for record."""
        return f"{self.key_prefix}:{record_id}"

    def save(self, record: Dict) -> str:
        """Save record to Redis."""
        record_id = record.get("id", str(uuid.uuid4()))
        record["id"] = record_id
        record["created_at"] = record.get("created_at", time.time())
        record["updated_at"] = time.time()
        
        key = self._make_key(record_id)
        serialized = json.dumps(record, default=str)
        
        if self.ttl:
            self._client.setex(key, self.ttl, serialized)
        else:
            self._client.set(key, serialized)
            
        # Add to index
        self._client.sadd(f"{self.key_prefix}:index", record_id)
        
        return record_id

    def all(self) -> Iterable[Tuple[str, Dict]]:
        """Retrieve all records from Redis."""
        index_key = f"{self.key_prefix}:index"
        record_ids = self._client.smembers(index_key)
        
        for record_id in record_ids:
            key = self._make_key(record_id)
            data = self._client.get(key)
            
            if data:
                try:
                    record = json.loads(data)
                    yield record_id, record
                except json.JSONDecodeError:
                    # Clean up corrupted entry
                    self._client.delete(key)
                    self._client.srem(index_key, record_id)
            else:
                # Clean up stale index entry
                self._client.srem(index_key, record_id)

    def delete(self, record_id: str) -> None:
        """Delete record from Redis."""
        key = self._make_key(record_id)
        self._client.delete(key)
        self._client.srem(f"{self.key_prefix}:index", record_id)

    def update(self, record_id: str, updates: Dict) -> None:
        """Update record in Redis."""
        key = self._make_key(record_id)
        data = self._client.get(key)
        
        if data:
            try:
                record = json.loads(data)
                record.update(updates)
                record["updated_at"] = time.time()
                
                serialized = json.dumps(record, default=str)
                if self.ttl:
                    self._client.setex(key, self.ttl, serialized)
                else:
                    self._client.set(key, serialized)
            except json.JSONDecodeError:
                pass  # Skip corrupted records

    def get(self, record_id: str) -> Optional[Dict]:
        """Get single record by ID."""
        key = self._make_key(record_id)
        data = self._client.get(key)
        
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                self.delete(record_id)  # Clean up corrupted record
        return None

    def health_check(self) -> Dict[str, any]:
        """Check Redis connectivity and stats."""
        try:
            info = self._client.info()
            index_size = self._client.scard(f"{self.key_prefix}:index")
            
            return {
                "status": "healthy",
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "unknown"),
                "total_records": index_size,
                "redis_version": info.get("redis_version", "unknown")
            }
        except redis.RedisError as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


class PostgresStorageBackend(StorageBackend):
    """PostgreSQL-based persistent storage for episodic memory."""
    
    def __init__(
        self,
        database_url: Optional[str] = None,
        table_name: str = "episodic_memory"
    ):
        if not HAS_ASYNCPG:
            raise ImportError("asyncpg package is required for PostgresStorageBackend")
            
        self.database_url = database_url or os.getenv(
            "DATABASE_URL", 
            "postgresql://postgres:postgres@localhost:5432/episodic_memory"
        )
        self.table_name = table_name
        self._pool = None
        self._initialize()

    def _initialize(self):
        """Initialize connection pool and create tables."""
        asyncio.create_task(self._async_initialize())

    async def _async_initialize(self):
        """Async initialization."""
        try:
            self._pool = await asyncpg.create_pool(self.database_url)
            await self._create_tables()
        except Exception as e:
            raise ConnectionError(f"Failed to initialize PostgreSQL connection: {e}")

    async def _create_tables(self):
        """Create required tables."""
        async with self._pool.acquire() as conn:
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id VARCHAR PRIMARY KEY,
                    data JSONB NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_created_at 
                ON {self.table_name}(created_at);
                
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_data_gin 
                ON {self.table_name} USING GIN(data);
            """)

    def save(self, record: Dict) -> str:
        """Save record to PostgreSQL."""
        record_id = record.get("id", str(uuid.uuid4()))
        record["id"] = record_id
        record["created_at"] = record.get("created_at", time.time())
        record["updated_at"] = time.time()
        
        return asyncio.create_task(self._async_save(record_id, record)).result()

    async def _async_save(self, record_id: str, record: Dict) -> str:
        """Async save implementation."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                f"""
                INSERT INTO {self.table_name} (id, data, updated_at)
                VALUES ($1, $2, NOW())
                ON CONFLICT (id) DO UPDATE SET
                    data = $2,
                    updated_at = NOW()
                """,
                record_id, json.dumps(record, default=str)
            )
        return record_id

    def all(self) -> Iterable[Tuple[str, Dict]]:
        """Retrieve all records from PostgreSQL."""
        return asyncio.create_task(self._async_all()).result()

    async def _async_all(self) -> Iterable[Tuple[str, Dict]]:
        """Async all implementation."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(f"SELECT id, data FROM {self.table_name}")
            
            results = []
            for row in rows:
                try:
                    record = json.loads(row['data'])
                    results.append((row['id'], record))
                except json.JSONDecodeError:
                    continue  # Skip corrupted records
                    
            return results

    def delete(self, record_id: str) -> None:
        """Delete record from PostgreSQL."""
        asyncio.create_task(self._async_delete(record_id))

    async def _async_delete(self, record_id: str):
        """Async delete implementation."""
        async with self._pool.acquire() as conn:
            await conn.execute(f"DELETE FROM {self.table_name} WHERE id = $1", record_id)

    def update(self, record_id: str, updates: Dict) -> None:
        """Update record in PostgreSQL."""
        asyncio.create_task(self._async_update(record_id, updates))

    async def _async_update(self, record_id: str, updates: Dict):
        """Async update implementation."""
        async with self._pool.acquire() as conn:
            # Get current record
            row = await conn.fetchrow(
                f"SELECT data FROM {self.table_name} WHERE id = $1", 
                record_id
            )
            
            if row:
                try:
                    record = json.loads(row['data'])
                    record.update(updates)
                    record["updated_at"] = time.time()
                    
                    await conn.execute(
                        f"UPDATE {self.table_name} SET data = $1, updated_at = NOW() WHERE id = $2",
                        json.dumps(record, default=str), record_id
                    )
                except json.JSONDecodeError:
                    pass  # Skip corrupted records

    async def health_check(self) -> Dict[str, any]:
        """Check PostgreSQL connectivity and stats."""
        try:
            async with self._pool.acquire() as conn:
                # Test connection
                await conn.fetchval("SELECT 1")
                
                # Get record count
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {self.table_name}")
                
                return {
                    "status": "healthy",
                    "total_records": count,
                    "pool_size": len(self._pool._holders)
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


class FileBasedStorageBackend(StorageBackend):
    """File-based persistent storage for development/small deployments."""
    
    def __init__(self, data_dir: str = "./episodic_memory_data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self._index_file = os.path.join(data_dir, "index.json")
        self._load_index()

    def _load_index(self):
        """Load record index from file."""
        try:
            with open(self._index_file, 'r') as f:
                self._index = set(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            self._index = set()

    def _save_index(self):
        """Save record index to file."""
        with open(self._index_file, 'w') as f:
            json.dump(list(self._index), f)

    def _record_path(self, record_id: str) -> str:
        """Get file path for record."""
        return os.path.join(self.data_dir, f"{record_id}.json")

    def save(self, record: Dict) -> str:
        """Save record to file."""
        record_id = record.get("id", str(uuid.uuid4()))
        record["id"] = record_id
        record["created_at"] = record.get("created_at", time.time())
        record["updated_at"] = time.time()
        
        path = self._record_path(record_id)
        with open(path, 'w') as f:
            json.dump(record, f, indent=2, default=str)
        
        self._index.add(record_id)
        self._save_index()
        
        return record_id

    def all(self) -> Iterable[Tuple[str, Dict]]:
        """Retrieve all records from files."""
        for record_id in self._index.copy():
            path = self._record_path(record_id)
            
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        record = json.load(f)
                    yield record_id, record
                except (json.JSONDecodeError, IOError):
                    # Clean up corrupted/inaccessible files
                    self._index.discard(record_id)
                    try:
                        os.remove(path)
                    except OSError:
                        pass
            else:
                # Clean up missing files from index
                self._index.discard(record_id)
        
        self._save_index()

    def delete(self, record_id: str) -> None:
        """Delete record file."""
        path = self._record_path(record_id)
        try:
            os.remove(path)
        except OSError:
            pass
        
        self._index.discard(record_id)
        self._save_index()

    def update(self, record_id: str, updates: Dict) -> None:
        """Update record in file."""
        path = self._record_path(record_id)
        
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    record = json.load(f)
                
                record.update(updates)
                record["updated_at"] = time.time()
                
                with open(path, 'w') as f:
                    json.dump(record, f, indent=2, default=str)
            except (json.JSONDecodeError, IOError):
                pass  # Skip corrupted files

    def health_check(self) -> Dict[str, any]:
        """Check file system storage stats."""
        try:
            import shutil
            total, used, free = shutil.disk_usage(self.data_dir)
            
            return {
                "status": "healthy",
                "total_records": len(self._index),
                "disk_total_gb": round(total / (1024**3), 2),
                "disk_used_gb": round(used / (1024**3), 2),
                "disk_free_gb": round(free / (1024**3), 2)
            }
        except Exception as e:
            return {
                "status": "unhealthy", 
                "error": str(e)
            }


def create_storage_backend(storage_type: Optional[str] = None) -> StorageBackend:
    """Factory function to create appropriate storage backend based on environment."""
    storage_type = storage_type or os.getenv("STORAGE_BACKEND", "file").lower()
    
    if storage_type == "redis" and HAS_REDIS:
        return RedisStorageBackend()
    elif storage_type == "postgres" and HAS_ASYNCPG:
        return PostgresStorageBackend()
    elif storage_type == "file":
        return FileBasedStorageBackend()
    else:
        # Fallback to in-memory for development
        from .episodic_memory import InMemoryStorage
        return InMemoryStorage()
"""
File hash computation module with caching.

Provides efficient SHA-256 hashing of file contents with modification-time-based caching.
"""
import hashlib
import os
from typing import Dict, Tuple, Optional


# In-memory cache: (file_path, mtime) -> hash
_hash_cache: Dict[Tuple[str, float], str] = {}


def compute_file_hash(file_path: str) -> str:
    """
    Compute SHA-256 hash of file content.
    
    Args:
        file_path: Absolute path to file
        
    Returns:
        Hexadecimal SHA-256 hash string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file can't be read
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256 = hashlib.sha256()
    
    try:
        with open(file_path, 'rb') as f:
            # Read in 64KB chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(65536), b''):
                sha256.update(chunk)
    except PermissionError:
        raise PermissionError(f"Cannot read file: {file_path}")
    
    return sha256.hexdigest()


def compute_file_hash_cached(file_path: str) -> str:
    """
    Compute file hash with caching based on modification time.
    
    Uses (file_path, modification_time) as cache key. If file hasn't been
    modified since last hash computation, returns cached value.
    
    Args:
        file_path: Absolute path to file
        
    Returns:
        Hexadecimal SHA-256 hash string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file can't be read
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Get modification time
    mtime = os.path.getmtime(file_path)
    cache_key = (file_path, mtime)
    
    # Check cache
    if cache_key in _hash_cache:
        return _hash_cache[cache_key]
    
    # Compute hash
    file_hash = compute_file_hash(file_path)
    
    # Store in cache
    _hash_cache[cache_key] = file_hash
    
    return file_hash


def clear_hash_cache():
    """Clear the hash cache. Useful for testing or memory management."""
    _hash_cache.clear()


def get_cache_size() -> int:
    """Get current number of entries in hash cache."""
    return len(_hash_cache)


def get_file_modified_time(file_path: str) -> Optional[str]:
    """
    Get file's last modified time as ISO format string.
    
    Args:
        file_path: Absolute path to file
        
    Returns:
        ISO format timestamp string, or None if file doesn't exist
    """
    if not os.path.exists(file_path):
        return None
    
    from datetime import datetime
    mtime = os.path.getmtime(file_path)
    return datetime.fromtimestamp(mtime).isoformat()

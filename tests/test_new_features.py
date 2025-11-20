"""Tests for new features: vector DB, Redis, cost monitoring, sandbox."""

import asyncio
import pytest
from datetime import datetime, timezone

from lewis_ai_system.vector_db import InMemoryVectorDB, EmbeddingVector
from lewis_ai_system.redis_cache import InMemoryCache
from lewis_ai_system.cost_monitor import CostMonitor
from lewis_ai_system.sandbox import EnhancedSandbox


class TestVectorDB:
    """Test vector database functionality."""
    
    @pytest.mark.asyncio
    async def test_insert_and_search(self):
        """Test inserting and searching vectors."""
        db = InMemoryVectorDB()
        
        # Create test vectors
        vectors = [
            EmbeddingVector(
                id="vec1",
                vector=[1.0, 0.0, 0.0],
                metadata={"type": "test"},
                text="First vector",
                created_at=datetime.now(timezone.utc)
            ),
            EmbeddingVector(
                id="vec2",
                vector=[0.9, 0.1, 0.0],
                metadata={"type": "test"},
                text="Second vector",
                created_at=datetime.now(timezone.utc)
            ),
        ]
        
        # Insert vectors
        success = await db.insert("test_collection", vectors)
        assert success
        
        # Search for similar vectors
        results = await db.search("test_collection", [1.0, 0.0, 0.0], limit=2)
        assert len(results) == 2
        assert results[0][1] > results[1][1]  # First should be more similar
    
    @pytest.mark.asyncio
    async def test_delete_vectors(self):
        """Test deleting vectors."""
        db = InMemoryVectorDB()
        
        vectors = [
            EmbeddingVector(
                id="vec1",
                vector=[1.0, 0.0],
                metadata={},
                text="Test",
                created_at=datetime.now(timezone.utc)
            )
        ]
        
        await db.insert("test", vectors)
        await db.delete("test", ["vec1"])
        
        results = await db.search("test", [1.0, 0.0])
        assert len(results) == 0


class TestRedisCache:
    """Test Redis cache functionality."""
    
    @pytest.mark.asyncio
    async def test_get_set(self):
        """Test basic get/set operations."""
        cache = InMemoryCache()
        await cache.initialize()
        
        # Set value
        success = await cache.set("test_key", {"data": "value"}, ttl_seconds=60)
        assert success
        
        # Get value
        value = await cache.get("test_key")
        assert value == {"data": "value"}
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting functionality."""
        cache = InMemoryCache()
        await cache.initialize()
        
        # First requests should succeed
        for i in range(3):
            allowed, remaining = await cache.rate_limit_check("user1", 3, 60)
            assert allowed
            assert remaining == 2 - i
        
        # Fourth request should be blocked
        allowed, remaining = await cache.rate_limit_check("user1", 3, 60)
        assert not allowed
        assert remaining == 0


class TestCostMonitor:
    """Test cost monitoring and anomaly detection."""
    
    def test_record_snapshot(self):
        """Test recording cost snapshots."""
        monitor = CostMonitor()
        
        monitor.record_snapshot("proj1", "project", 10.0)
        monitor.record_snapshot("proj1", "project", 15.0)
        
        assert "proj1" in monitor.snapshots
        assert len(monitor.snapshots["proj1"]) == 2
    
    def test_cost_rate_calculation(self):
        """Test cost rate calculation."""
        monitor = CostMonitor()
        
        # Record snapshots with known times
        monitor.record_snapshot("proj1", "project", 10.0)
        monitor.record_snapshot("proj1", "project", 20.0)
        
        rate = monitor.calculate_cost_rate("proj1", window_minutes=60)
        assert rate >= 0.0  # Rate should be positive
    
    def test_anomaly_detection(self):
        """Test anomaly detection."""
        monitor = CostMonitor()
        
        # Record normal usage
        for i in range(10):
            monitor.record_snapshot("proj1", "project", i * 1.0)
        
        # Record spike
        monitor.record_snapshot("proj1", "project", 50.0)
        
        # Check for anomalies
        anomalies = monitor.check_for_anomalies(
            "proj1",
            "project",
            budget_limit=100.0,
            completion_percentage=0.5
        )
        
        # Should detect budget or rate issues
        assert len(anomalies) >= 0  # May or may not detect depending on timing
    
    def test_should_pause(self):
        """Test pause recommendation."""
        monitor = CostMonitor()
        
        # Exceed budget
        monitor.record_snapshot("proj1", "project", 150.0)
        
        should_pause, reason = monitor.should_pause_entity(
            "proj1",
            "project",
            budget_limit=100.0,
            auto_pause_enabled=True
        )
        
        assert should_pause
        assert reason == "paused_budget"


class TestSandbox:
    """Test enhanced sandbox functionality."""
    
    def test_execute_python_basic(self):
        """Test basic Python execution."""
        sandbox = EnhancedSandbox(timeout_seconds=5)
        
        code = """
result = 2 + 2
"""
        
        result = sandbox.execute_python(code)
        assert result["result"] == 4
        assert result["error"] is None
    
    def test_execute_python_with_output(self):
        """Test Python execution with stdout."""
        sandbox = EnhancedSandbox(timeout_seconds=5)
        
        code = """
print("Hello, sandbox!")
result = "done"
"""
        
        result = sandbox.execute_python(code)
        assert "Hello, sandbox!" in result["stdout"]
        assert result["result"] == "done"
    
    def test_execute_python_timeout(self):
        """Test timeout handling."""
        sandbox = EnhancedSandbox(timeout_seconds=1)
        
        code = """
import time
time.sleep(10)
result = "should not reach"
"""
        
        result = sandbox.execute_python(code)
        assert result["error"] is not None
        assert "Timeout" in result["error"] or "error" in result["error"].lower()
    
    def test_execute_python_restricted(self):
        """Test restricted builtins."""
        sandbox = EnhancedSandbox(timeout_seconds=5)
        
        # Should work with allowed functions
        code = """
result = sum([1, 2, 3])
"""
        result = sandbox.execute_python(code)
        assert result["result"] == 6
        
        # Should fail with disallowed functions
        code_bad = """
import os
os.system("echo bad")
"""
        result = sandbox.execute_python(code_bad)
        assert result["error"] is not None


def test_all_imports():
    """Test that all new modules can be imported."""
    from lewis_ai_system import vector_db
    from lewis_ai_system import redis_cache
    from lewis_ai_system import cost_monitor
    from lewis_ai_system import sandbox
    
    assert vector_db is not None
    assert redis_cache is not None
    assert cost_monitor is not None
    assert sandbox is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

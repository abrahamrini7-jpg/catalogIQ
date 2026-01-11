#!/usr/bin/env python3
"""
Test script for the agentic flow.
This script simulates creating a task and uploading photos to trigger the agent workflow.
"""

import sys
import logging
import time
from datetime import datetime, timezone
from bson import ObjectId
from database import get_db

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_agentic_flow")

def test_agentic_flow():
    """Create a test task and simulate photo upload to trigger agents"""
    
    db = get_db()
    logger.info("🧪 Starting agentic flow test...")
    
    # Verify database connection
    try:
        db.command('ping')
        logger.info("✅ Connected to MongoDB")
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        return
    
    # 1. Create a test task (matching MongoDB schema)
    from datetime import datetime
    task_id = ObjectId()
    test_task = {
        "_id": task_id,
        "status": "INITIATED",
        "workflow_step": 1,
        "sku_code": "TEST-SKU-001",
        "metadata": {
            "product_name": "Test Product",
            "title": "Test Product Title",
            "country": "US",
            "photo_urls": [
                "https://example.com/photo1.jpg",
                "https://example.com/photo2.jpg"
            ]
        },
        "agent_log": [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent": "test_script",
                "action": "task_created",
                "thought": "Created initial test task"
            }
        ],
        "retry_metadata": {
            "count": 0,
            "last_error": None
        }
    }
    
    # Insert the task
    db.tasks.insert_one(test_task)
    logger.info(f"✓ Created test task: {task_id}")
    logger.info(f"  Status: INITIATED")
    logger.info(f"  SKU: {test_task['sku_code']}")
    logger.info(f"  Product: {test_task['metadata']['product_name']}")
    
    # 2. Simulate photo upload by updating status to PHOTOS_UPLOADED
    logger.info(f"\n📝 Updating task status to PHOTOS_UPLOADED...")
    logger.info(f"   This should trigger agent_worker.py via change stream")
    
    result = db.tasks.update_one(
        {"_id": task_id},
        {"$set": {"status": "PHOTOS_UPLOADED"}}
    )
    logger.info(f"✓ Update result: matched={result.matched_count}, modified={result.modified_count}")
    
    # 3. Wait for agent to process
    logger.info(f"\n⏳ Waiting 5 seconds for agent to process...")
    time.sleep(5)
    
    # 4. Check the result
    updated_task = db.tasks.find_one({"_id": task_id})
    if not updated_task:
        logger.error("❌ Task not found!")
        return
    
    final_status = updated_task.get('status')
    agent_log = updated_task.get('agent_log', [])
    
    logger.info(f"\n📊 Final task status: {final_status}")
    logger.info(f"📋 Agent log entries: {len(agent_log)}")
    
    for log_entry in agent_log:
        logger.info(f"   [{log_entry['timestamp'][:19]}] {log_entry['agent']}: {log_entry['action']} - {log_entry['thought']}")
    
    if final_status == "COLOR_CORRECTED":
        logger.info("✅ SUCCESS! Agent was triggered and processed the task")
    else:
        logger.warning(f"⚠️  Expected 'COLOR_CORRECTED' but got '{final_status}'")
        logger.warning("   Agent may not have been triggered yet")
        if agent_log:
            logger.warning(f"   Last log entry: {agent_log[-1]}")
        else:
            logger.warning("   No agent log entries found")
    
    # Cleanup
    # logger.info(f"\n🧹 Cleaning up test data...")
    # db.tasks.delete_one({"_id": task_id})
    # db.photos.delete_many({"task_id": task_id})
    # logger.info(f"✓ Cleaned up test data")

if __name__ == "__main__":
    try:
        test_agentic_flow()
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        sys.exit(1)

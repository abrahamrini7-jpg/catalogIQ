#!/usr/bin/env python3
"""
Debug script to test MongoDB change stream directly.
"""

import logging
import time
from bson import ObjectId
from database import get_db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("stream_debug")

db = get_db()
logger.info("🧪 Testing MongoDB change stream...")

# Verify database connection
try:
    db.command('ping')
    logger.info("✅ Connected to MongoDB")
except Exception as e:
    logger.error(f"❌ Failed to connect: {e}")
    exit(1)

# Clear old test data
logger.info("🧹 Clearing old test data...")
db.tasks.delete_many({"status": "INITIATED"})

# Create a simple change stream (ALL operations)
logger.info("📡 Opening change stream for ALL operations...")

try:
    # Use an empty pipeline to catch ALL changes
    with db.tasks.watch([]) as stream:
        logger.info("✅ Change stream opened!")
        logger.info("🎯 Making a test change in 2 seconds...")
        time.sleep(2)
        
        # Make a change in a separate thread/process simulation
        task_id = ObjectId()
        logger.info(f"\n📝 Inserting test task: {task_id}")
        db.tasks.insert_one({
            "_id": task_id,
            "status": "INITIATED",
            "test": True
        })
        
        logger.info("⏳ Waiting for change event (10 second timeout)...")
        
        # Wait for the change event with timeout
        start = time.time()
        for change in stream:
            elapsed = time.time() - start
            logger.info(f"\n✅ CHANGE DETECTED after {elapsed:.1f}s!")
            logger.info(f"   Full change event:")
            logger.info(f"   Operation: {change.get('operationType')}")
            logger.info(f"   Document ID: {change.get('documentKey')}")
            logger.info(f"   Full data: {change}")
            
            # Clean up and exit
            logger.info("\n🧹 Cleaning up...")
            db.tasks.delete_one({"_id": task_id})
            logger.info("✅ Test complete!")
            break
            
            if elapsed > 10:
                logger.error("❌ No change detected after 10 seconds!")
                break
                
except Exception as e:
    logger.error(f"❌ Error: {e}", exc_info=True)

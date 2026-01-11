import os
import logging
from datetime import datetime, timezone
from bson import ObjectId
from database import get_db

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("upload_photo")

db = get_db()

def upload_real_photo(task_sku, file_path, product_name="UNKNOWN", country="US"):
    """
    Upload a real photo and trigger the agentic flow.
    Creates a task if it doesn't exist, updates status to PHOTOS_UPLOADED.
    """
    try:
        # 1. Get the absolute path so the agent can find it later
        absolute_path = os.path.abspath(file_path)
        
        if not os.path.exists(absolute_path):
            logger.error(f"❌ File not found: {absolute_path}")
            return False
        
        logger.info(f"📸 Uploading photo for SKU: {task_sku}")
        logger.info(f"   File: {absolute_path}")
        logger.info(f"   Size: {os.path.getsize(absolute_path)} bytes")
        
        # 2. Check if task exists
        existing_task = db.tasks.find_one({"sku_code": task_sku})
        
        if existing_task:
            logger.info(f"✓ Found existing task: {existing_task['_id']}")
            task_id = existing_task['_id']
        else:
            logger.info(f"ℹ️  Task doesn't exist, creating new one...")
            task_id = ObjectId()
            new_task = {
                "_id": task_id,
                "sku_code": task_sku,
                "status": "INITIATED",
                "workflow_step": 1,
                "metadata": {
                    "product_name": product_name,
                    "country": country,
                    "photo_urls": []
                },
                "agent_log": [
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "agent": "upload_photo",
                        "action": "task_created",
                        "thought": f"Created task for SKU {task_sku}"
                    }
                ],
                "retry_metadata": {
                    "count": 0,
                    "last_error": None
                }
            }
            db.tasks.insert_one(new_task)
            logger.info(f"✓ Created new task: {task_id}")
        
        # 3. Update the task to add photo and trigger agent
        logger.info(f"\n📝 Updating task to PHOTOS_UPLOADED...")
        
        result = db.tasks.update_one(
            {"_id": task_id},
            {
                "$set": {"status": "PHOTOS_UPLOADED"},
                "$push": {
                    "metadata.photo_urls": absolute_path,
                    "agent_log": {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "agent": "upload_photo",
                        "action": "photo_uploaded",
                        "thought": f"Uploaded photo: {os.path.basename(file_path)}"
                    }
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"✅ SUCCESS! Task {task_sku} updated with photo")
            logger.info(f"   Task ID: {task_id}")
            logger.info(f"   Status: PHOTOS_UPLOADED → Agent 2A should trigger now")
            return True
        else:
            logger.error(f"❌ Failed to update task (no modifications made)")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error uploading photo: {e}", exc_info=True)
        return False

# TEST IT: Change 'NIKE-USA-101' to your actual SKU and provide a real image filename
if __name__ == "__main__":
    upload_real_photo(
        task_sku="NIKE-USA-101",
        file_path="test_product.jpg",
        product_name="Nike Running Shoe",
        country="US"
    )
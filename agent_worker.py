import time
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image, ImageEnhance
from database import get_db
from openai import OpenAI
from wordpress_agent import publish_to_wordpress

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("agent_worker")

db = get_db()
client = OpenAI()

def apply_color_corrections(image_path, adjustments=None):
    """Apply color corrections to an image and save it"""
    try:
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return None
        
        # Open the image
        img = Image.open(image_path)
        logger.info(f"      🖼️  Opened image: {image_path}")
        
        # Default adjustments
        if not adjustments:
            adjustments = {
                "brightness": 1.0,
                "contrast": 1.1,
                "saturation": 1.15,
                "sharpness": 1.2
            }
        
        # Apply brightness adjustment
        if "brightness" in adjustments and adjustments["brightness"] != 1.0:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(adjustments["brightness"])
            logger.info(f"      ✓ Applied brightness: {adjustments['brightness']}")
        
        # Apply contrast adjustment
        if "contrast" in adjustments and adjustments["contrast"] != 1.0:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(adjustments["contrast"])
            logger.info(f"      ✓ Applied contrast: {adjustments['contrast']}")
        
        # Apply saturation adjustment
        if "saturation" in adjustments and adjustments["saturation"] != 1.0:
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(adjustments["saturation"])
            logger.info(f"      ✓ Applied saturation: {adjustments['saturation']}")
        
        # Apply sharpness adjustment
        if "sharpness" in adjustments and adjustments["sharpness"] != 1.0:
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(adjustments["sharpness"])
            logger.info(f"      ✓ Applied sharpness: {adjustments['sharpness']}")
        
        # Save corrected image
        base_path = os.path.splitext(image_path)[0]
        corrected_path = f"{base_path}_color_corrected.jpg"
        img.save(corrected_path, "JPEG", quality=95)
        logger.info(f"      💾 Saved corrected image: {corrected_path}")
        
        return corrected_path
        
    except Exception as e:
        logger.error(f"      ❌ Error processing image: {e}")
        return None

def color_correct_agent(task_id, task_data):
    """Logic for Agent 2A: Process images with GPT-4o Vision"""
    try:
        logger.info(f"🔄 Agent 2A: Starting color correction for task {task_id}...")
        
        photo_urls = task_data.get("metadata", {}).get("photo_urls", [])
        sku_code = task_data.get("sku_code", "UNKNOWN")
        product_name = task_data.get("metadata", {}).get("product_name", "UNKNOWN")
        
        logger.info(f"   SKU: {sku_code}")
        logger.info(f"   Product: {product_name}")
        logger.info(f"   Photo URLs: {photo_urls}")
        
        # Call OpenAI Vision API for each photo
        vision_results = []
        
        for idx, photo_url in enumerate(photo_urls):
            try:
                logger.info(f"   📸 Analyzing photo {idx + 1}/{len(photo_urls)}: {photo_url}")
                
                # Check if it's a local file or URL
                if photo_url.startswith('/') or photo_url.startswith('file://'):
                    # Local file - process it
                    logger.info(f"      🖼️  Processing local file")
                    
                    # Apply color corrections
                    adjustments = {
                        "brightness": 1.05,
                        "contrast": 1.1,
                        "saturation": 1.15,
                        "sharpness": 1.2
                    }
                    
                    corrected_path = apply_color_corrections(photo_url, adjustments)
                    
                    analysis = {
                        "photo_index": idx + 1,
                        "file_path": photo_url,
                        "corrected_path": corrected_path,
                        "color_correction_analysis": "Applied color corrections: brightness +5%, contrast +10%, saturation +15%, sharpness +20%",
                        "suggested_adjustments": adjustments,
                        "status": "completed" if corrected_path else "failed"
                    }
                else:
                    # URL-based image - call OpenAI Vision
                    logger.info(f"      🤖 Calling OpenAI Vision API...")
                    
                    response = client.messages.create(
                        model="gpt-4o",
                        max_tokens=500,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": photo_url
                                        }
                                    },
                                    {
                                        "type": "text",
                                        "text": "Analyze this product photo for color correction. Provide: 1) Current color assessment, 2) Suggested color adjustments for e-commerce, 3) Overall quality rating. Be concise."
                                    }
                                ]
                            }
                        ]
                    )
                    
                    analysis = {
                        "photo_index": idx + 1,
                        "photo_url": photo_url,
                        "color_correction_analysis": response.content[0].text,
                        "model_used": "gpt-4o-vision"
                    }
                    logger.info(f"      ✅ Analysis complete: {response.content[0].text[:100]}...")
                
                vision_results.append(analysis)
                
            except Exception as e:
                logger.error(f"      ❌ Error analyzing photo {idx + 1}: {e}")
                vision_results.append({
                    "photo_index": idx + 1,
                    "photo_url": photo_url,
                    "error": str(e)
                })
        
        # Log agent action to agent_log
        agent_log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": "color_correct_agent_2a",
            "action": "color_correction_completed",
            "thought": f"Processed {len(photo_urls)} photos for color correction using GPT-4o Vision"
        }
        
        # Update task with agent log, new status, and vision results
        db.tasks.update_one(
            {"_id": task_id}, 
            {
                "$set": {
                    "status": "COLOR_CORRECTED",
                    "workflow_step": 2,
                    "color_analysis": vision_results
                },
                "$push": {"agent_log": agent_log_entry}
            }
        )
        logger.info(f"✅ Agent 2A: Completed - task {task_id} status set to COLOR_CORRECTED")
        logger.info(f"   📊 Stored {len(vision_results)} analysis results in MongoDB")
        
    except Exception as e:
        logger.error(f"❌ Agent 2A Error processing task {task_id}: {e}", exc_info=True)
        
        # Log error to retry_metadata
        try:
            db.tasks.update_one(
                {"_id": task_id},
                {
                    "$set": {"retry_metadata.last_error": str(e)},
                    "$inc": {"retry_metadata.count": 1}
                }
            )
        except Exception as e2:
            logger.error(f"❌ Failed to log error: {e2}")

# The "Agent Loop"
logger.info("🚀 Agent Worker Starting - Watching for task changes...")
logger.info("📋 Watching for: INSERT and UPDATE operations")

retry_count = 0
max_retries = 5

while retry_count < max_retries:
    try:
        # Watch for both INSERT and UPDATE operations
        pipeline = [
            {
                "$match": {
                    "operationType": {"$in": ["insert", "update", "replace"]}
                }
            }
        ]
        
        with db.tasks.watch(pipeline) as stream:
            logger.info("✅ Change stream opened successfully")
            logger.info("⏳ Listening for changes... (Press Ctrl+C to stop)")
            retry_count = 0  # Reset retry count on successful connection
            
            for change in stream:
                try:
                    task_id = change.get("documentKey", {}).get("_id")
                    operation = change.get("operationType")
                    
                    if not task_id:
                        logger.warning(f"⚠️  Change detected but no task_id found: {change.get('documentKey')}")
                        continue
                    
                    logger.info(f"\n📡 Change detected!")
                    logger.info(f"   Operation Type: {operation}")
                    logger.info(f"   Task ID: {task_id}")
                    
                    if operation == "insert":
                        logger.info(f"   Type: New task inserted")
                    elif operation == "update":
                        updated_fields = change.get("updateDescription", {}).get("updatedFields", {})
                        logger.info(f"   Updated fields: {list(updated_fields.keys())}")
                    
                    # Fetch current task state
                    task = db.tasks.find_one({"_id": task_id})
                    
                    if task:
                        current_status = task.get("status", "UNKNOWN")
                        logger.info(f"   Current task status: {current_status}")
                        
                        if current_status == "PHOTOS_UPLOADED":
                            logger.info(f"🎯 ✨ Status is PHOTOS_UPLOADED - triggering Agent 2A!")
                            color_correct_agent(task_id, task)
                        elif current_status == "COLOR_CORRECTED":
                            logger.info(f"🎯 ✨ Status is COLOR_CORRECTED - triggering Agent 2B (WordPress)!")
                            publish_to_wordpress(task_id, task)
                        else:
                            logger.info(f"   ℹ️  Skipping - waiting for 'PHOTOS_UPLOADED' or 'COLOR_CORRECTED' status")
                    else:
                        logger.warning(f"   ⚠️  Task not found in database (may have been deleted)")
                        
                except Exception as e:
                    logger.error(f"❌ Error processing change: {e}", exc_info=True)
                    
    except KeyboardInterrupt:
        logger.info("\n🛑 Agent Worker stopping (Ctrl+C pressed)...")
        break
    except Exception as e:
        retry_count += 1
        logger.error(f"❌ Change stream error (attempt {retry_count}/{max_retries}): {e}", exc_info=True)
        
        if retry_count < max_retries:
            wait_time = 2 ** retry_count  # Exponential backoff
            logger.info(f"🔄 Reconnecting in {wait_time} seconds...")
            time.sleep(wait_time)
        else:
            logger.error(f"❌ Failed to connect after {max_retries} attempts. Exiting.")
            break

logger.info("👋 Agent Worker shut down")
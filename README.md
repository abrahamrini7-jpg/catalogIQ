# CatalogiQ - Agentic Product Photo Workflow

An intelligent automation system that processes product photos through a multi-agent workflow: color correction, enhancement, and WordPress publishing.

## 🎯 Features

- **Automated Color Correction** (Agent 2A): Analyzes and enhances product images using OpenAI Vision API
- **WordPress Publishing** (Agent 2B): Auto-uploads corrected images to WordPress
- **MongoDB Change Streams**: Real-time task monitoring and agent triggering
- **Comprehensive Logging**: Full audit trail of all agent actions
- **Workflow Orchestration**: Sequential agent execution based on status updates

## 🏗️ Architecture

```
Upload Photo → PHOTOS_UPLOADED → Agent 2A (Color Correct)
                                        ↓
                                COLOR_CORRECTED → Agent 2B (WordPress Publish)
                                        ↓
                                WORDPRESS_PUBLISHED
```

### Agents

| Agent | Function | Input | Output |
|-------|----------|-------|--------|
| **Agent 2A** | Color correction & enhancement | Photo URLs | Corrected images + analysis |
| **Agent 2B** | WordPress publishing | Corrected images | Media library + URLs |

## 📋 Prerequisites

- Python 3.8+
- MongoDB Atlas account with change stream support
- OpenAI API key
- WordPress site with REST API enabled
- Hosting with ModSecurity disabled or whitelisted for `/wp-json/wp/v2/media`

## 🚀 Setup

### 1. Clone & Install

```bash
git clone <your-repo>
cd catalogiq
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:

```env
# MongoDB
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/

# OpenAI
OPENAI_API_KEY=sk-proj-...

# WordPress
WORDPRESS_URL=https://your-site.com
WORDPRESS_USER=your_username
WORDPRESS_PASSWORD=your_app_password
```

### 3. Initialize MongoDB

Create these collections:
- `tasks` - Main task workflow data
- `photos` - Photo metadata and versions (optional)

### 4. Run the Agent Worker

```bash
python3 agent_worker.py
```

The agent will start listening for task status changes and automatically trigger processing.

## 📖 Usage

### Upload a Photo

```bash
python3 upload_photo.py
```

Or use it as a module:

```python
from upload_photo import upload_real_photo

upload_real_photo(
    task_sku="PRODUCT-001",
    file_path="path/to/photo.jpg",
    product_name="Nike Running Shoe",
    country="US"
)
```

### Test the Workflow

```bash
python3 test_agentic_flow.py
```

This creates a test task and triggers the full workflow.

## 📊 MongoDB Schema

```json
{
  "_id": ObjectId,
  "sku_code": "NIKE-USA-101",
  "status": "WORDPRESS_PUBLISHED",
  "workflow_step": 3,
  "metadata": {
    "product_name": "Nike Running Shoe",
    "title": "Product Title",
    "country": "US",
    "photo_urls": ["path/to/photo.jpg"]
  },
  "color_analysis": [
    {
      "photo_index": 1,
      "file_path": "path/to/photo.jpg",
      "corrected_path": "path/to/photo_color_corrected.jpg",
      "status": "completed",
      "suggested_adjustments": {
        "brightness": 1.05,
        "contrast": 1.1
      }
    }
  ],
  "wordpress_publish_results": [
    {
      "photo_index": 1,
      "status": "published",
      "media_id": 12345,
      "media_url": "https://site.com/photo.jpg"
    }
  ],
  "agent_log": [
    {
      "timestamp": "2026-01-10T15:53:52.000Z",
      "agent": "upload_photo",
      "action": "photo_uploaded",
      "thought": "Uploaded photo for color correction"
    }
  ],
  "retry_metadata": {
    "count": 0,
    "last_error": null
  }
}
```

## 🔧 Configuration

### Agent 2A - Color Correction

Adjustments in `agent_worker.py`:

```python
adjustments = {
    "brightness": 1.05,   # 5% brighter
    "contrast": 1.1,      # 10% more contrast
    "saturation": 1.15,   # 15% more saturated
    "sharpness": 1.2      # 20% sharper
}
```

Modify these values to adjust processing intensity.

### Agent 2B - WordPress

Set in `.env`:

```env
WORDPRESS_URL=https://your-site.com
WORDPRESS_USER=api_user
WORDPRESS_PASSWORD=application_password
```

**Note**: Use WordPress application passwords, not your main password.

## 🚨 Troubleshooting

### 406 ModSecurity Error (WordPress Upload Fails)

**Problem**: `"An appropriate representation of the requested resource could not be found"`

**Solutions**:

1. **Contact your host** to whitelist `/wp-json/wp/v2/media` in ModSecurity
2. **Disable ModSecurity** for API requests in cPanel
3. **Add .htaccess exception**:
   ```apache
   <IfModule mod_security.c>
       <LocationMatch "^/wp-json/wp/v2/media">
           SecRuleEngine Off
       </LocationMatch>
   </IfModule>
   ```

### MongoDB Connection Error

```
SSL: CERTIFICATE_VERIFY_FAILED
```

**Fix**:
```bash
pip install --upgrade certifi
```

Or install Python certificates:
```bash
/Applications/Python\ 3.*/Install\ Certificates.command
```

### Agent Not Triggering

Check that:
1. Agent worker is running: `python3 agent_worker.py`
2. MongoDB change streams are enabled (requires replica set)
3. Task status was actually updated
4. Check logs for errors

## 📁 Project Structure

```
catalogiq/
├── agent_worker.py          # Main agent orchestrator
├── wordpress_agent.py       # WordPress publishing agent
├── upload_photo.py          # Photo upload trigger
├── database.py              # MongoDB connection
├── test_agentic_flow.py     # Integration test
├── test_wordpress_api.py    # WordPress API tester
├── .env                     # Configuration (gitignored)
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## 🔐 Security

- **Never commit `.env`** - Contains API keys and passwords
- **Use application passwords** for WordPress, not main password
- **Rotate API keys** regularly
- **MongoDB IP Whitelist** - Whitelist your bot's IP in MongoDB Atlas
- **HTTPS only** - Ensure WordPress is HTTPS

## 🛠️ Development

### Run tests

```bash
python3 test_agentic_flow.py
python3 test_wordpress_api.py
```

### View logs in MongoDB

```python
from database import get_db
db = get_db()

# Check a task
task = db.tasks.find_one({"sku_code": "NIKE-USA-101"})
print(task["agent_log"])
print(task["color_analysis"])
```

### Debug agent behavior

Add to `agent_worker.py`:

```python
logger.info(f"DEBUG: {variable_name}")
```

All logs go to console with timestamp and level.

## 🚀 Next Steps

- [ ] Add support for FTP uploads instead of REST API
- [ ] Implement image quality checks
- [ ] Add background removal agent
- [ ] Create web UI for task monitoring
- [ ] Add batch processing
- [ ] Implement retry logic with exponential backoff
- [ ] Add Slack/email notifications

## 📝 License

MIT

## 👤 Author

CatalogiQ Team

## 📞 Support

For issues:
1. Check logs: `agent_worker.py` outputs
2. Check MongoDB: View task status and `agent_log`
3. Test WordPress connection: `python3 test_wordpress_api.py`

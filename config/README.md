# Configuration Directory

This directory contains configuration templates and working configuration files for the Vimeo Monitor application.

## 🔒 Security Note

**IMPORTANT:** API credentials and other sensitive information should **NEVER** be stored in this directory or committed to version control. Always use the `.env` file in the project root for sensitive data.

## Quick Setup

1. **Initialize configuration:**

   ```bash
   python scripts/setup_config.py --init
   ```

2. **Edit your API credentials:**

   ```bash
   # Edit .env file with your actual Vimeo API credentials
   vim .env
   ```

3. **Customize settings (optional):**

   ```bash
   # Edit config.yaml with your preferences
   vim config/config.yaml
   ```

4. **Validate configuration:**

   ```bash
   python scripts/setup_config.py --validate
   ```

## Configuration Structure

### Sensitive Data (.env file in project root)

- VIMEO_TOKEN
- VIMEO_KEY
- VIMEO_SECRET
- VIMEO_STREAM_ID

### Non-Sensitive Settings (Config files in this directory)

- Timing configuration
- API failure handling parameters
- File paths for media
- Logging configuration
- Overlay display settings

## File Priority

1. Environment variables (highest priority)
2. Configuration file (YAML/TOML)
3. Default values (lowest priority)

## Live Reload Support

Configuration files are automatically reloaded when changed, with backup creation and change logging.

# UI Testing Setup

## Selenium Tests

The UI test suite uses Selenium with Chrome/Chromium for browser automation and comprehensive testing.

### First Time Setup (Devcontainer)

The devcontainer includes Chromium and chromedriver. If you need to reinstall:

```bash
# Install Chromium and chromedriver
apk add --no-cache chromium chromium-chromedriver nss freetype harfbuzz ca-certificates ttf-freefont font-noto

# Install Selenium
pip install selenium
```

### Running Tests

```bash
# Run all UI tests
pytest test/ui/

# Run specific test file
pytest test/ui/test_ui_dashboard.py

# Run specific test
pytest test/ui/test_ui_dashboard.py::test_dashboard_loads

# Run with verbose output
pytest test/ui/ -v

# Run and stop on first failure
pytest test/ui/ -x
```

### What Gets Tested

- ✅ **API Backend endpoints** - All Flask API endpoints work correctly
- ✅ **Page loads** - All pages load without fatal errors (Dashboard, Devices, Network, Settings, etc.)
- ✅ **Dashboard metrics** - Charts and device counts display
- ✅ **Device operations** - Add, edit, delete devices via UI
- ✅ **Network topology** - Device relationship visualization
- ✅ **Multi-edit bulk operations** - Bulk device editing
- ✅ **Maintenance tools** - CSV export/import, database cleanup
- ✅ **Settings configuration** - Settings page loads and saves
- ✅ **Notification system** - User notifications display
- ✅ **JavaScript error detection** - No console errors on page loads

### Test Organization

Tests are organized by page/feature:

- `test_ui_dashboard.py` - Dashboard metrics and charts
- `test_ui_devices.py` - Device listing and CRUD operations
- `test_ui_network.py` - Network topology visualization
- `test_ui_maintenance.py` - Database tools and CSV operations
- `test_ui_multi_edit.py` - Bulk device editing
- `test_ui_settings.py` - Settings configuration
- `test_ui_notifications.py` - Notification system
- `test_ui_plugins.py` - Plugin management

### Troubleshooting

**"Could not start Chromium"**
- Ensure Chromium is installed: `which chromium`
- Check chromedriver: `which chromedriver`
- Verify versions match: `chromium --version` and `chromedriver --version`

**"API token not available"**
- Check `/data/config/app.conf` exists and contains `API_TOKEN=`
- Restart backend services if needed

**Tests skip with "Chromium browser not available"**
- Chromium not installed or not in PATH
- Run: `apk add chromium chromium-chromedriver`

### Writing New Tests

See [TESTING_GUIDE.md](TESTING_GUIDE.md) for comprehensive examples of:
- Button click testing
- Form submission
- AJAX request verification
- File download testing
- Multi-step workflows

**Browser launch fails**
- Alpine Linux uses system Chromium
- Make sure chromium package is installed: `apk info chromium`

**Tests timeout**
- Increase timeout in test functions
- Check if backend is running: `ps aux | grep python3`
- Verify frontend is accessible: `curl http://localhost:20211`

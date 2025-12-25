# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

E-Ink Weather Panel is a Python application that generates comprehensive weather display images for e-ink displays connected to Raspberry Pi devices. The system integrates data from Yahoo Weather API, Japan Meteorological Agency rain radar, and InfluxDB sensor data to create multi-panel weather displays.

## Development Commands

### Python Environment (uv)

```bash
# Install dependencies
uv sync

# Run main application locally
env RASP_HOSTNAME="hostname" uv run src/display_image.py

# Run basic functionality tests
uv run pytest --timeout=240 -x tests/test_basic.py

# Run all tests with coverage
uv run pytest --cov=src --cov-report=html tests/

# Run specific test file
uv run pytest tests/unit/test_config.py

# Run E2E tests (requires running webapp)
uv run pytest tests/e2e/test_webapp.py --host <host-ip> --port <port>

# Type check
uv run pyright
```

### React Frontend

```bash
cd react

# Install dependencies
npm ci

# Development server
npm run dev

# Build for production
npm run build

# Lint code
npm run lint
```

### Docker Development

```bash
# Build frontend first
cd react && npm ci && npm run build && cd -

# Run with Docker Compose
docker compose run --build --rm weather_panel
```

## Architecture

### Core Components

| File | Description |
|------|-------------|
| `src/create_image.py` | Image generation using multiprocessing pool for parallel panel rendering |
| `src/display_image.py` | Main application loop, SSH connection management to Raspberry Pi |
| `src/healthz.py` | Kubernetes liveness probe implementation |
| `src/webui.py` | Flask-based web UI server for testing/viewing images |
| `src/weather_display/display.py` | SSH connection management, image transfer, retry logic with `exec_patiently()` |
| `src/weather_display/config.py` | Frozen dataclass-based configuration with YAML parsing |

### Weather Display Panels (`src/weather_display/panel/`)

| File | Description | Data Source |
|------|-------------|-------------|
| `weather.py` | Weather forecast (24-48hr hourly), temperature, precipitation, wind, feel temperature | Yahoo Weather API |
| `rain_cloud.py` | Rain radar images (current + 1 hour forecast) | Japan Meteorological Agency (via Selenium) |
| `sensor_graph.py` | Multi-room sensor data visualization (temp, humidity, CO2, lux) with async fetching | InfluxDB |
| `sensor_graph_utils.py` | Utility functions for icon drawing and air conditioner power detection | - |
| `power_graph.py` | Power consumption monitoring graph with historical trends | InfluxDB |
| `wbgt.py` | WBGT heat index display with 5-level face icons | Ministry of Environment API |
| `rain_fall.py` | Current rainfall amount overlay with duration tracking | InfluxDB (rain gauge sensor) |
| `time.py` | Current time display (Asia/Tokyo timezone) | System clock |

### Supporting Modules

| Module | Description |
|--------|-------------|
| `src/weather_display/timing_filter.py` | Kalman filter-based timing control for update synchronization |
| `src/weather_display/metrics/server.py` | Flask-based metrics web server (runs on separate thread) |
| `src/weather_display/metrics/collector.py` | SQLite-based metrics storage with anomaly detection (Isolation Forest) |
| `src/weather_display/metrics/webapi/page.py` | Metrics dashboard web page |
| `src/weather_display/metrics/webapi/page_js.py` | JavaScript for metrics dashboard |
| `src/weather_display/runner/webapi/run.py` | Async subprocess execution of `create_image.py` with stdout/stderr streaming |

### Configuration

- **Python Version**: 3.13 (3.10+ required)
- **Two display modes**: Normal (3200x1800) and Small (2200x1650)
- **YAML configuration** with JSON schema validation
- **Example configs**: `config.example.yaml` and `config-small.example.yaml`
- **All configuration** parsed into frozen dataclasses for type safety and immutability

### Data Flow

1. `display_image.py` starts main loop and metrics server
2. Spawns `create_image.py` as subprocess for each update cycle
3. `create_image.py` uses `multiprocessing.Pool` to generate 7 panels (normal) or 4 panels (small) in parallel
4. Generated image is piped to Raspberry Pi via SSH and displayed using `fbi`

### Error Codes

| Code | Constant | Description |
|------|----------|-------------|
| 220 | `ERROR_CODE_MINOR` | Panel generation error (display continues) |
| 222 | `ERROR_CODE_MAJOR` | Display failure (critical error) |

### External Dependencies

- **my-py-lib**: Custom library for Slack notifications, InfluxDB access, image utilities, Selenium helpers
- **Selenium/Chrome**: Used by `rain_cloud.py` for JMA radar scraping (headless Chrome required)
- **InfluxDB**: Time-series database for sensor data (config via `my_lib.sensor_data.InfluxDBConfig`)

## Testing Strategy

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures and helpers
├── test_basic.py            # Comprehensive integration tests
├── unit/                    # Unit tests
│   ├── test_config.py           # Configuration parsing
│   ├── test_timing_filter.py    # Kalman filter logic
│   ├── test_sensor_graph_utils.py  # Utility functions
│   ├── test_rain_fall_utils.py  # Rainfall formatting
│   ├── test_weather_calc.py     # Feel temperature calculation
│   ├── test_metrics_collector.py  # Metrics and anomaly detection
│   ├── test_display.py          # SSH display control
│   ├── test_healthz.py          # Health check
│   └── test_webapi_run.py       # Web API subprocess runner
├── integration/             # Integration tests
│   ├── test_create_image.py     # Image generation workflow
│   ├── test_display_image.py    # Display control
│   ├── test_weather_panel.py    # Weather panel
│   ├── test_sensor_graph_panel.py  # Sensor graph
│   ├── test_power_graph_panel.py   # Power graph
│   ├── test_rain_cloud_panel.py    # Rain cloud (Selenium)
│   ├── test_rain_fall_panel.py     # Rain fall
│   └── test_wbgt_panel.py          # WBGT
├── webapp/                  # Web API tests
│   └── test_api.py              # Flask API endpoints
└── e2e/                     # End-to-end tests (Playwright)
    └── test_webapp.py           # Web UI E2E tests
```

### Key Test Fixtures (conftest.py)

| Fixture | Description |
|---------|-------------|
| `config` / `config_small` | Load example configuration files |
| `ssh_mock` | Mock SSH connections to Raspberry Pi |
| `mock_sensor_fetch_data` | Mock InfluxDB data fetching |
| `image_checker` | Helper for saving and validating generated images |
| `slack_checker` | Verify Slack notification behavior |

### Running Tests

- Tests run with `DUMMY_MODE=true` by default to avoid real API calls
- Coverage reports are generated in `htmlcov/`
- Test reports (HTML, images) stored in `reports/`

## Deployment

### Local

Direct Python execution with uv:
```bash
env RASP_HOSTNAME="hostname" uv run src/display_image.py
```

### Docker

- **Base**: Ubuntu 24.04
- **Localization**: Japanese (ja_JP.UTF-8)
- **Package Manager**: uv
- **Init System**: tini
- **Chrome**: Installed for Selenium-based rain radar scraping
- **Entry point**: `tini` + `uv run src/display_image.py`

### Kubernetes

- **Namespace**: `panel`
- **Deployment**: `kubernetes/e-ink_weater_panel.yaml`
- **Liveness probe**: `healthz.py` (120s initial delay, 60s period)
- **Resource limits**: 512Mi minimum, 2Gi maximum memory

### Environment Variables

| Variable | Description |
|----------|-------------|
| `RASP_HOSTNAME` | Target Raspberry Pi hostname (required) |
| `SSH_KEY` | Path to SSH private key (default: `key/panel.id_rsa`) |
| `INFLUXDB_TOKEN` | InfluxDB authentication token |
| `DUMMY_MODE` | Set to "true" to use cached/dummy data |

## React Frontend

### Structure (`react/`)

| File | Description |
|------|-------------|
| `src/App.tsx` | Main application component |
| `src/main.tsx` | Entry point |
| `src/App.css`, `src/index.css` | Styling |
| `vite.config.ts` | Vite build configuration |

### Key Dependencies

- React 18.3.1 with TypeScript
- Vite for build tooling
- Bootstrap 5.3.1 (react-bootstrap)
- react-zoom-pan-pinch for image viewing

## Key Dependencies

### Backend (Python)

| Category | Packages |
|----------|----------|
| Image Processing | PIL/Pillow, matplotlib, opencv-contrib-python-headless |
| Data | influxdb-client, pandas, scipy, scikit-learn |
| Web Scraping | selenium, undetected-chromedriver |
| SSH | paramiko |
| Web Server | flask, flask-cors |

### Development

| Category | Packages |
|----------|----------|
| Testing | pytest, pytest-cov, pytest-html, pytest-mock, pytest-xdist, pytest-timeout |
| Browser Testing | playwright, pytest-playwright |
| Time Mocking | time-machine |
| Quality | pre-commit, pyright |

## Code Patterns

### Panel Creation Pattern

Each panel module follows this pattern:

```python
def create(config: AppConfig) -> tuple[PIL.Image.Image, float] | tuple[PIL.Image.Image, float, str]:
    """
    Returns:
        - (image, elapsed_time) on success
        - (image, elapsed_time, error_message) on error
    """
```

### Error Handling

- Panels use `my_lib.panel_util.draw_panel_patiently()` for retry logic
- Errors are logged and optionally sent to Slack
- Failed panels show error images instead of crashing the entire display
- Display module uses `exec_patiently()` for SSH command retry

### Configuration Access

Configuration uses frozen dataclasses:
```python
config.weather.panel.width  # Panel dimensions
config.influxdb.url         # InfluxDB connection
config.font.path            # Font directory
```

### Multiprocessing Strategy

- `create_image.py` spawns `multiprocessing.Pool` to generate panels in parallel
- Each panel runs in separate process to avoid matplotlib thread issues
- Metrics collected per-panel with elapsed time and error status

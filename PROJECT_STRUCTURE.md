# Project Structure & Setup Guide
## Demo-to-PDF Documentation Tool

---

## Complete Project Structure

```
demo-2-pdf/
│
├── README.md
├── FEASIBILITY_ANALYSIS.md
├── ARCHITECTURE_RECOMMENDATION.md
├── PROJECT_STRUCTURE.md
├── LICENSE
├── .gitignore
│
├── extension/                          # Browser Extension (Capture Layer)
│   ├── manifest.json
│   ├── package.json
│   ├── tsconfig.json
│   ├── webpack.config.js
│   ├── src/
│   │   ├── background/
│   │   │   └── service-worker.ts       # Background script
│   │   ├── content/
│   │   │   └── content-script.ts       # Injected into pages
│   │   ├── popup/
│   │   │   ├── popup.html
│   │   │   ├── popup.tsx               # React popup UI
│   │   │   └── popup.css
│   │   ├── lib/
│   │   │   ├── capture.ts              # Screenshot capture
│   │   │   ├── event-tracker.ts        # Event listeners
│   │   │   ├── api-client.ts           # Backend communication
│   │   │   └── utils.ts
│   │   └── types/
│   │       └── index.ts
│   ├── assets/
│   │   ├── icons/
│   │   │   ├── icon-16.png
│   │   │   ├── icon-48.png
│   │   │   └── icon-128.png
│   │   └── styles/
│   │       └── global.css
│   └── dist/                           # Built extension (gitignored)
│
├── backend/                            # Python Backend (Processing Layer)
│   ├── pyproject.toml                  # Poetry config
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── .env.example
│   ├── main.py                         # FastAPI entry point
│   ├── config.py
│   ├── src/
│   │   ├── __init__.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── capture.py              # Capture endpoints
│   │   │   ├── sessions.py             # Session management
│   │   │   ├── steps.py                # Step CRUD operations
│   │   │   ├── export.py               # PDF export
│   │   │   └── websocket.py            # Real-time updates
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── session.py
│   │   │   ├── step.py
│   │   │   └── database.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── session.py              # Pydantic schemas
│   │   │   └── step.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── capture_service.py
│   │   │   ├── image_service.py
│   │   │   ├── annotation_service.py
│   │   │   ├── pdf_service.py
│   │   │   └── ocr_service.py
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── session.py              # DB operations
│   │   │   └── migrations/
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── image_processing.py
│   │   │   └── helpers.py
│   │   └── templates/
│   │       ├── pdf_base.html
│   │       ├── pdf_modern.html
│   │       ├── pdf_minimal.html
│   │       └── styles/
│   │           ├── base.css
│   │           └── modern.css
│   ├── storage/                        # Runtime data (gitignored)
│   │   ├── sessions/
│   │   ├── images/
│   │   └── exports/
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── unit/
│   │   │   ├── test_capture_service.py
│   │   │   ├── test_image_service.py
│   │   │   └── test_pdf_service.py
│   │   ├── integration/
│   │   │   ├── test_api.py
│   │   │   └── test_export_flow.py
│   │   └── fixtures/
│   │       └── sample_data.py
│   └── scripts/
│       ├── setup_db.py
│       └── generate_sample_pdf.py
│
├── editor/                             # React Editor (Refinement Layer)
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── .env.example
│   ├── index.html
│   ├── public/
│   │   └── favicon.ico
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/
│   │   │   ├── client.ts               # API client
│   │   │   └── types.ts
│   │   ├── components/
│   │   │   ├── SessionList.tsx
│   │   │   ├── SessionDetail.tsx
│   │   │   ├── StepList.tsx
│   │   │   ├── StepEditor.tsx
│   │   │   ├── ImagePreview.tsx
│   │   │   ├── ImageAnnotator.tsx
│   │   │   ├── ExportDialog.tsx
│   │   │   └── common/
│   │   │       ├── Button.tsx
│   │   │       ├── Input.tsx
│   │   │       └── Modal.tsx
│   │   ├── hooks/
│   │   │   ├── useSession.ts
│   │   │   ├── useSteps.ts
│   │   │   └── useExport.ts
│   │   ├── store/
│   │   │   ├── sessionStore.ts         # Zustand store
│   │   │   └── uiStore.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── utils/
│   │   │   ├── formatting.ts
│   │   │   └── helpers.ts
│   │   └── styles/
│   │       └── global.css
│   ├── tests/
│   │   ├── setup.ts
│   │   ├── components/
│   │   │   ├── StepEditor.test.tsx
│   │   │   └── SessionList.test.tsx
│   │   └── utils/
│   │       └── test-utils.tsx
│   └── dist/                           # Built app (gitignored)
│
├── desktop/                            # Optional: Electron Desktop App
│   ├── package.json
│   ├── main.js                         # Electron main process
│   ├── preload.js
│   └── src/
│       └── (reuse editor code)
│
├── docs/                               # Documentation
│   ├── getting-started.md
│   ├── user-guide.md
│   ├── developer-guide.md
│   ├── api-reference.md
│   └── architecture/
│       ├── overview.md
│       └── decisions/
│           ├── 001-browser-extension-approach.md
│           └── 002-pdf-generation-library.md
│
├── scripts/                            # Utility scripts
│   ├── setup-dev-env.sh
│   ├── build-all.sh
│   ├── run-tests.sh
│   └── package-extension.sh
│
└── .github/                            # CI/CD
    └── workflows/
        ├── test-backend.yml
        ├── test-frontend.yml
        ├── build-extension.yml
        └── release.yml
```

---

## Initial Setup Instructions

### Prerequisites

- **Node.js:** 18+ (for extension and editor)
- **Python:** 3.11+ (for backend)
- **Poetry:** Latest version (Python package manager)
- **Git:** For version control
- **Chrome/Chromium:** For testing extension

### Quick Start

```bash
# Clone repository
git clone https://github.com/yourusername/demo-2-pdf.git
cd demo-2-pdf

# Run setup script
chmod +x scripts/setup-dev-env.sh
./scripts/setup-dev-env.sh
```

### Manual Setup

#### 1. Backend Setup

```bash
cd backend

# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Or use pip
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your settings

# Initialize database
poetry run python scripts/setup_db.py

# Run backend server
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Backend should now be running at:** `http://localhost:8000`
**API docs available at:** `http://localhost:8000/docs`

#### 2. Editor Setup

```bash
cd editor

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env (set VITE_API_URL=http://localhost:8000)

# Run development server
npm run dev
```

**Editor should now be running at:** `http://localhost:3000`

#### 3. Browser Extension Setup

```bash
cd extension

# Install dependencies
npm install

# Build extension
npm run build

# Load in Chrome:
# 1. Open chrome://extensions/
# 2. Enable "Developer mode"
# 3. Click "Load unpacked"
# 4. Select the extension/dist folder
```

---

## Key Configuration Files

### Backend: pyproject.toml

```toml
[tool.poetry]
name = "demo2pdf-backend"
version = "0.1.0"
description = "Backend service for Demo-to-PDF documentation tool"
authors = ["Your Name <you@example.com>"]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.109.0"
uvicorn = {extras = ["standard"], version = "^0.27.0"}
sqlalchemy = "^2.0.25"
pydantic = "^2.5.3"
pillow = "^10.2.0"
weasyprint = "^60.2"
jinja2 = "^3.1.3"
python-multipart = "^0.0.6"
aiosqlite = "^0.19.0"
python-dotenv = "^1.0.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.4"
pytest-asyncio = "^0.23.3"
pytest-cov = "^4.1.0"
black = "^24.1.1"
ruff = "^0.1.14"
mypy = "^1.8.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

### Backend: .env.example

```env
# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true
LOG_LEVEL=INFO

# Database
DATABASE_URL=sqlite:///./storage/demo2pdf.db

# Storage
STORAGE_PATH=./storage
MAX_UPLOAD_SIZE_MB=50

# PDF Generation
PDF_TEMPLATE=modern
PDF_DEFAULT_QUALITY=85
PDF_MAX_IMAGE_WIDTH=1920

# CORS
CORS_ORIGINS=http://localhost:3000,chrome-extension://*

# Optional: AI Features
OPENAI_API_KEY=your-key-here
ENABLE_AI_DESCRIPTIONS=false
```

### Extension: manifest.json

```json
{
  "manifest_version": 3,
  "name": "Demo-to-PDF",
  "version": "0.1.0",
  "description": "Capture screen activity and convert it into user documentation PDFs",
  "permissions": [
    "activeTab",
    "storage",
    "tabs"
  ],
  "host_permissions": [
    "<all_urls>"
  ],
  "background": {
    "service_worker": "background.js"
  },
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["content-script.js"],
      "run_at": "document_idle"
    }
  ],
  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "assets/icons/icon-16.png",
      "48": "assets/icons/icon-48.png",
      "128": "assets/icons/icon-128.png"
    }
  },
  "icons": {
    "16": "assets/icons/icon-16.png",
    "48": "assets/icons/icon-48.png",
    "128": "assets/icons/icon-128.png"
  }
}
```

### Extension: package.json

```json
{
  "name": "demo2pdf-extension",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "webpack --mode development --watch",
    "build": "webpack --mode production",
    "lint": "eslint src --ext .ts,.tsx",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/chrome": "^0.0.260",
    "@types/react": "^18.2.48",
    "@types/react-dom": "^18.2.18",
    "copy-webpack-plugin": "^12.0.2",
    "css-loader": "^6.9.1",
    "eslint": "^8.56.0",
    "html-webpack-plugin": "^5.6.0",
    "style-loader": "^3.3.4",
    "ts-loader": "^9.5.1",
    "typescript": "^5.3.3",
    "webpack": "^5.89.0",
    "webpack-cli": "^5.1.4"
  }
}
```

### Editor: package.json

```json
{
  "name": "demo2pdf-editor",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx",
    "test": "vitest",
    "test:ui": "vitest --ui"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.3",
    "@chakra-ui/react": "^2.8.2",
    "@emotion/react": "^11.11.3",
    "@emotion/styled": "^11.11.0",
    "framer-motion": "^11.0.3",
    "zustand": "^4.5.0",
    "axios": "^1.6.5",
    "react-beautiful-dnd": "^13.1.1"
  },
  "devDependencies": {
    "@types/react": "^18.2.48",
    "@types/react-dom": "^18.2.18",
    "@vitejs/plugin-react": "^4.2.1",
    "@vitest/ui": "^1.2.0",
    "eslint": "^8.56.0",
    "typescript": "^5.3.3",
    "vite": "^5.0.11",
    "vitest": "^1.2.0"
  }
}
```

---

## Development Workflow

### Daily Development

```bash
# Terminal 1: Backend
cd backend
poetry run uvicorn main:app --reload

# Terminal 2: Editor
cd editor
npm run dev

# Terminal 3: Extension
cd extension
npm run dev  # Rebuilds on changes

# Reload extension in Chrome after changes
```

### Running Tests

```bash
# Backend tests
cd backend
poetry run pytest

# With coverage
poetry run pytest --cov=src --cov-report=html

# Frontend tests
cd editor
npm test

# E2E tests (if implemented)
cd tests/e2e
npm run test:e2e
```

### Code Quality

```bash
# Backend linting
cd backend
poetry run black src/
poetry run ruff check src/
poetry run mypy src/

# Frontend linting
cd editor
npm run lint

# Extension linting
cd extension
npm run lint
```

### Building for Production

```bash
# Build all components
./scripts/build-all.sh

# Or manually:

# Backend (no build needed, but can create standalone)
cd backend
poetry build

# Editor
cd editor
npm run build

# Extension
cd extension
npm run build
```

---

## Git Workflow

### Branch Strategy

```
main              # Production-ready code
├── develop       # Integration branch
├── feature/*     # New features
├── bugfix/*      # Bug fixes
└── release/*     # Release preparation
```

### Commit Convention

```
feat: Add video export functionality
fix: Resolve screenshot timing issue
docs: Update API documentation
test: Add unit tests for PDF service
refactor: Simplify capture logic
chore: Update dependencies
```

---

## Deployment Checklist

### Pre-Release

- [ ] All tests passing
- [ ] Code coverage >80%
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in all package files
- [ ] Security audit completed (`npm audit`, `safety check`)
- [ ] Performance benchmarks run
- [ ] Browser extension tested on Chrome, Firefox, Edge

### Release Process

```bash
# 1. Create release branch
git checkout -b release/v0.1.0

# 2. Update version numbers
# - extension/manifest.json
# - extension/package.json
# - editor/package.json
# - backend/pyproject.toml

# 3. Build production assets
./scripts/build-all.sh

# 4. Tag release
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0

# 5. Package extension
cd extension/dist
zip -r demo2pdf-extension-v0.1.0.zip .

# 6. Submit to Chrome Web Store
# (Manual process via Chrome Developer Dashboard)
```

---

## Troubleshooting

### Backend won't start

```bash
# Check Python version
python --version  # Should be 3.11+

# Reinstall dependencies
cd backend
rm -rf venv/
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Check port availability
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows
```

### Extension not loading

```bash
# Verify build output
cd extension
ls -la dist/  # Should contain manifest.json

# Check for errors in Chrome
# 1. Go to chrome://extensions/
# 2. Look for errors in red
# 3. Click "Errors" to see details

# Rebuild with verbose output
npm run build -- --verbose
```

### PDF generation fails

```bash
# Install system dependencies (WeasyPrint requirements)

# Ubuntu/Debian
sudo apt-get install python3-dev python3-pip python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info

# macOS
brew install cairo pango gdk-pixbuf libffi

# Windows
# Use pre-built wheels from: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer
```

---

## Additional Resources

### Documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Docs](https://react.dev/)
- [Chrome Extension API](https://developer.chrome.com/docs/extensions/reference/)
- [WeasyPrint Docs](https://weasyprint.org/)

### Tools
- [Postman Collection](./docs/postman/demo2pdf.json) - API testing
- [Figma Designs](./docs/designs/) - UI mockups
- [Test Data Generator](./scripts/generate-test-data.py)

---

**Last Updated:** November 13, 2025
**Maintainer:** Development Team

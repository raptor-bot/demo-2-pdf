# Demo-to-PDF

**Capture screen activity and convert it into user documentation PDFs**

Automatically record user interactions on web applications and generate professional step-by-step PDF guides with screenshots and descriptions.

---

## Overview

Demo-to-PDF is a tool that helps you create user documentation by capturing screen activity. Simply record your actions on a web application, and the tool will generate a structured PDF guide with screenshots and step descriptions.

### Key Features

- **Automated Capture:** Browser extension records clicks, inputs, and navigation
- **Smart Screenshots:** Captures screen at each important interaction
- **Step Editing:** Refine captured steps, add descriptions, reorder content
- **PDF Export:** Generate professional documentation with customizable templates
- **Privacy-First:** All data stored locally, no cloud upload required

---

## Quick Links

- **[🚀 Prototype Guide](PROTOTYPE_GUIDE.md)** - **START HERE** - Working prototype in 15 minutes!
- **[🤖 LLM Integration Guide](LLM_INTEGRATION_GUIDE.md)** - AI-powered description generation
- **[Quick Start Guide](QUICK_START.md)** - Original quick start
- **[Feasibility Analysis](FEASIBILITY_ANALYSIS.md)** - Detailed technical analysis
- **[Architecture Recommendation](ARCHITECTURE_RECOMMENDATION.md)** - Production architecture
- **[Project Structure](PROJECT_STRUCTURE.md)** - Complete setup guide

---

## Architecture

```
Browser Extension (Capture)
         ↓
Python Backend (Processing)
         ↓
React Editor (Refinement)
         ↓
PDF Generation (Export)
```

**Technology Stack:**
- **Capture:** Chrome/Firefox Extension (JavaScript/TypeScript)
- **Backend:** Python 3.11+ with FastAPI
- **Editor:** React 18+ with TypeScript
- **PDF:** WeasyPrint (HTML/CSS to PDF)

---

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- Chrome or Firefox browser

### Installation

```bash
# Clone repository
git clone <repository-url>
cd demo-2-pdf

# Run setup script
./setup.sh

# Start backend
cd backend
source venv/bin/activate
python main.py

# Load extension
# Chrome: chrome://extensions/ → Load unpacked → select 'extension' folder
# Firefox: about:debugging → Load Temporary Add-on → select extension/manifest.json
```

**→ For detailed setup, see [PROTOTYPE_GUIDE.md](PROTOTYPE_GUIDE.md)**

---

## Usage

1. **Start Recording:** Click the browser extension icon and press "Start Recording"
2. **Perform Actions:** Click, type, navigate through your web application
3. **Stop Recording:** Press "Stop Recording" when done
4. **Edit Steps:** (Optional) Use the web editor to refine captured steps
5. **Export PDF:** Generate your documentation PDF

---

## Documentation

### For Users
- [Quick Start Guide](QUICK_START.md) - Get up and running quickly
- [User Guide](docs/user-guide.md) - Detailed usage instructions

### For Developers
- [Feasibility Analysis](FEASIBILITY_ANALYSIS.md) - Technical evaluation
- [Architecture Recommendation](ARCHITECTURE_RECOMMENDATION.md) - System design
- [Project Structure](PROJECT_STRUCTURE.md) - Code organization
- [Developer Guide](docs/developer-guide.md) - Contributing guidelines
- [API Reference](docs/api-reference.md) - Backend API documentation

---

## Project Status

**Current Phase:** Planning & Architecture
**Version:** 0.1.0 (Pre-Alpha)

### Roadmap

- [ ] **Phase 1:** Core capture and basic PDF export (Weeks 1-3)
- [ ] **Phase 2:** Web editor for step refinement (Weeks 4-6)
- [ ] **Phase 3:** Smart automation and OCR (Weeks 7-9)
- [ ] **Phase 4:** Production polish and distribution (Weeks 10-12)

See [ARCHITECTURE_RECOMMENDATION.md](ARCHITECTURE_RECOMMENDATION.md) for detailed roadmap.

---

## Features

### Current (Planned)
- ✓ Browser-based capture
- ✓ Screenshot automation
- ✓ Session management
- ✓ Basic PDF export
- ✓ Step editing interface
- ✓ Image optimization

### Current (Working Prototype) 🎉
- ✓ **AI-powered descriptions** - OpenAI, Anthropic, Ollama support
- ✓ **Template-based descriptions** - Fast, free fallback
- ✓ **Real-time capture** - Clicks, inputs, navigation
- ✓ **Automatic screenshots** - After each action
- ✓ **REST API** - Session management and export

### Future
- Video export
- Desktop application capture
- Cloud sync (optional)
- Multiple PDF templates
- Collaboration features
- Full PDF generation with WeasyPrint

---

## Architecture Highlights

### Why Browser Extension?
- Direct DOM access (no OCR needed for web content)
- Best UX for web application documentation
- No OS-level permissions required
- Fast and lightweight

### Why Python Backend?
- Rich ecosystem for image processing and PDF generation
- FastAPI provides modern async API
- Easy integration with OCR and AI tools

### Why WeasyPrint?
- HTML/CSS to PDF (familiar tech stack)
- Automatic layout management
- Excellent image handling
- Professional output quality

For complete architecture details, see [ARCHITECTURE_RECOMMENDATION.md](ARCHITECTURE_RECOMMENDATION.md).

---

## Development

### Development Setup

```bash
# Backend (Terminal 1)
cd backend
source venv/bin/activate
python main.py

# Editor (Terminal 2)
cd editor
npm run dev

# Extension development
cd extension
npm run dev  # Auto-rebuild on changes
# Reload extension in chrome://extensions/ after changes
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd editor
npm test
```

### Building for Production

```bash
# Backend
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

## Contributing

Contributions are welcome! Please read the contributing guidelines before submitting pull requests.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

[Choose appropriate license - MIT, Apache 2.0, etc.]

---

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [React](https://react.dev/) - Frontend framework
- [WeasyPrint](https://weasyprint.org/) - PDF generation
- [Chrome Extension APIs](https://developer.chrome.com/docs/extensions/) - Browser integration

---

## Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/demo-2-pdf/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/demo-2-pdf/discussions)
- **Documentation:** [docs/](docs/)

---

## Contact

**Project Maintainer:** [Your Name]
**Email:** [your.email@example.com]
**Website:** [https://demo2pdf.dev](https://demo2pdf.dev)

---

**Status:** 🚧 Under Development | **Version:** 0.1.0 | **License:** TBD

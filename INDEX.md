# Documentation Index — TonerTrack v2

Primary docs
- README.md — Full user manual and configuration
- QUICK_START.md — Quick start steps (run and open UI)
- PROJECT_SUMMARY.md — High-level project overview
- ARCHITECTURE.md — Technical architecture and API
- DISCOVERY_GUIDE.md — Printer discovery and import methods

Start here
- If you're deploying: read `QUICK_START.md` then `README.md`
- If you're a developer: read `ARCHITECTURE.md` then explore source

API docs are available at: `http://localhost:8000/docs` when the server is running.
# 📚 TonerTrack v2.0 - Documentation Index

Welcome to TonerTrack v2.0! This index will help you find the right documentation for your needs.

## 🚀 Getting Started

**Start here if this is your first time:**

1. **[QUICK_START.md](QUICK_START.md)** ⭐ START HERE
   - 3-step installation guide
   - What's new in v2.0
   - Your migrated printers list
   - Quick tips and troubleshooting

2. **[README.md](README.md)** 📖 Full Documentation
   - Complete feature list
   - Installation instructions
   - Usage guide
   - API documentation
   - Troubleshooting

## 📊 Understanding the Project

**Read these to understand what you have:**

3. **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** 📝 Overview
   - What changed from v1 to v2
   - Feature comparison
   - Technical improvements
   - Deployment options
   - Future enhancements

4. **[ARCHITECTURE.md](ARCHITECTURE.md)** 🏗️ Technical Details
   - System architecture diagrams
   - Data flow explanation
   - Technology stack details
   - API examples
   - Performance characteristics

## 📁 Project Files

### Core Application Files
```
main.py              - FastAPI backend server (300+ lines)
snmp_utils.py        - SNMP query utilities (200+ lines)
start.py             - Easy launcher script
start.bat            - Windows quick launcher
requirements.txt     - Python dependencies
printers_sample.json - Your 19 migrated printers
```

### Web Interface Files
```
templates/
  └── index.html     - Main web interface (200+ lines)
  
static/
  ├── css/
  │   └── styles.css - Dark theme styling (600+ lines)
  └── js/
      └── app.js     - Frontend logic (500+ lines)
```

### Documentation Files
```
README.md            - Complete user guide (300+ lines)
QUICK_START.md       - Quick reference (150+ lines)
PROJECT_SUMMARY.md   - Project overview (250+ lines)
ARCHITECTURE.md      - Technical docs (350+ lines)
INDEX.md            - This file!
```

## 🎯 Quick Reference by Task

### I want to...

#### Install and Run
→ **[QUICK_START.md](QUICK_START.md)** - Section: "Getting Started (3 Steps)"
→ **[README.md](README.md)** - Section: "Installation"

#### Add/Edit/Delete Printers
→ **[README.md](README.md)** - Section: "Usage"
→ **[QUICK_START.md](QUICK_START.md)** - Section: "Main Features"

#### Understand the Status Colors
→ **[README.md](README.md)** - Section: "Status Codes"
→ **[QUICK_START.md](QUICK_START.md)** - Section: "Status Colors"

#### Access from Other Computers
→ **[QUICK_START.md](QUICK_START.md)** - Section: "Accessing From Other Computers"
→ **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Section: "Deployment Options"

#### Fix Connection Issues
→ **[README.md](README.md)** - Section: "Troubleshooting"
→ **[ARCHITECTURE.md](ARCHITECTURE.md)** - Section: "Troubleshooting Flow"

#### Use the API Programmatically
→ **[README.md](README.md)** - Section: "API Documentation"
→ **[ARCHITECTURE.md](ARCHITECTURE.md)** - Section: "API Request/Response Examples"
→ http://localhost:8000/docs (when running)

#### Deploy on a Server
→ **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Section: "Deployment Options"
→ **[ARCHITECTURE.md](ARCHITECTURE.md)** - Section: "Deployment Scenarios"

#### Understand SNMP Configuration
→ **[README.md](README.md)** - Section: "SNMP Configuration"
→ **[ARCHITECTURE.md](ARCHITECTURE.md)** - Section: "SNMP Query Details"

#### Export/Import Data
→ **[README.md](README.md)** - Section: "Export/Import"
→ Use the web interface: 📥 Export button

#### Migrate from Old Version
→ **[QUICK_START.md](QUICK_START.md)** - Section: "Migration from v1"
→ **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Section: "Old vs New Comparison"

#### Customize or Extend
→ **[ARCHITECTURE.md](ARCHITECTURE.md)** - All sections
→ Review source code with inline comments

## 🔍 Documentation Features

### By Document Type

| Document | Type | Best For | Length |
|----------|------|----------|--------|
| QUICK_START.md | Quick Reference | First-time users, quick lookups | 150 lines |
| README.md | User Manual | Complete usage guide | 300 lines |
| PROJECT_SUMMARY.md | Overview | Understanding changes, decisions | 250 lines |
| ARCHITECTURE.md | Technical | Developers, system admins | 350 lines |
| INDEX.md | Navigation | Finding the right docs | This file |

### By Audience

**👤 End Users** (Just want to use it):
1. QUICK_START.md (sections: Getting Started, Main Features)
2. README.md (sections: Usage, Troubleshooting)

**👨‍💼 IT Administrators** (Deploy and maintain):
1. PROJECT_SUMMARY.md (sections: Deployment Options, Security)
2. README.md (sections: Installation, SNMP Configuration)
3. ARCHITECTURE.md (sections: Deployment Scenarios)

**👨‍💻 Developers** (Customize or extend):
1. ARCHITECTURE.md (all sections)
2. Source code files with comments
3. API docs at /docs endpoint

## 📈 Document Relationships

```
┌─────────────────┐
│  QUICK_START.md │ ← Start here for quick setup
└────────┬────────┘
         │ Need more detail?
         ↓
┌─────────────────┐
│    README.md    │ ← Complete user guide
└────────┬────────┘
         │ Want to understand changes?
         ↓
┌─────────────────┐
│ PROJECT_SUMMARY │ ← Project overview & comparison
└────────┬────────┘
         │ Need technical details?
         ↓
┌─────────────────┐
│ ARCHITECTURE.md │ ← Deep technical documentation
└─────────────────┘
```

## 🛠️ Code Organization

### Backend (Python)
```python
main.py:
  - FastAPI app initialization
  - API endpoint definitions (/api/printers, /api/stats, etc.)
  - Business logic (evaluate_status, poll tasks)
  - Data persistence (load/save JSON)

snmp_utils.py:
  - SNMP query functions (snmp_get, snmp_walk)
  - Printer status queries (get_printer_status_async)
  - Data parsing and categorization
  - Async/await implementations
```

### Frontend (JavaScript)
```javascript
app.js:
  - DOM manipulation and rendering
  - API client functions (fetch requests)
  - State management (printers, selection)
  - Event handlers (search, filter, buttons)
  - Modal dialogs (add/edit printer)
```

### Styling (CSS)
```css
styles.css:
  - Dark theme variables
  - Layout (grid, flexbox)
  - Components (buttons, cards, panels)
  - Responsive design (mobile-first)
  - Animations and transitions
```

## 📞 Getting Help

### Self-Service Resources
1. **In-app documentation**: http://localhost:8000/docs
2. **These documentation files**: Everything you need is here!
3. **Error messages**: Check browser console (F12)
4. **Server logs**: Check terminal/command prompt output

### Troubleshooting Checklist
- [ ] Read QUICK_START.md troubleshooting section
- [ ] Read README.md troubleshooting section
- [ ] Check printer is powered on and on network
- [ ] Verify SNMP is enabled on printer
- [ ] Check firewall isn't blocking port 161
- [ ] Review server logs for error messages

### Common Issues → Solutions

| Issue | Solution Document | Section |
|-------|------------------|---------|
| Can't start server | QUICK_START.md | Troubleshooting |
| Printer offline | README.md | Troubleshooting |
| No toner levels | README.md | Troubleshooting |
| Can't access from other PC | QUICK_START.md | Accessing From Other Computers |
| Want to add authentication | ARCHITECTURE.md | Security Model |

## 🎓 Learning Path

### Beginner Path
1. Read QUICK_START.md completely (15 minutes)
2. Launch the application
3. Explore the web interface
4. Try adding/editing a printer
5. Read README.md sections as needed

### Administrator Path
1. Read QUICK_START.md (10 minutes)
2. Read PROJECT_SUMMARY.md - Deployment Options (15 minutes)
3. Read README.md - Installation & SNMP Config (20 minutes)
4. Review security considerations in ARCHITECTURE.md (10 minutes)
5. Deploy to your environment

### Developer Path
1. Skim QUICK_START.md (5 minutes)
2. Read ARCHITECTURE.md completely (30 minutes)
3. Review source code files (1 hour)
4. Experiment with API at /docs endpoint (30 minutes)
5. Make test modifications

## 📊 Features by Document

### Feature Coverage Matrix

| Feature | QUICK_START | README | PROJECT_SUMMARY | ARCHITECTURE |
|---------|-------------|--------|-----------------|--------------|
| Installation | ✅ Basic | ✅ Detailed | ⭐ Multiple options | - |
| Usage Guide | ✅ Quick | ✅ Complete | - | - |
| API Reference | - | ✅ Overview | - | ✅ Detailed |
| SNMP Details | - | ✅ Config | - | ✅ Technical |
| Troubleshooting | ✅ Common | ✅ Complete | - | ✅ Flow charts |
| Security | - | - | ✅ Considerations | ✅ Implementation |
| Architecture | - | - | ✅ Overview | ✅ Detailed |
| Migration | ✅ Guide | - | ✅ Comparison | - |

Legend: ✅ Included, ⭐ Primary source, - Not covered

## 🔄 Keeping Documentation Updated

All documentation is current as of November 2024.

If you make changes to the application:
1. Update inline code comments
2. Update relevant documentation file(s)
3. Update this index if adding new docs
4. Keep version numbers synchronized

## 📝 Documentation Standards

All documentation follows these principles:
- **Clear**: Written for your intended audience
- **Complete**: Covers all necessary topics
- **Correct**: Tested and verified information
- **Current**: Updated with the latest version
- **Concise**: Respects your time

## 🎉 Quick Wins

**Want to see it working in 5 minutes?**
1. Open QUICK_START.md
2. Follow the 3 steps
3. Click "Refresh All" button
4. Watch your printers update!

**Want to understand everything in 1 hour?**
1. Read QUICK_START.md (15 min)
2. Read PROJECT_SUMMARY.md (20 min)
3. Explore the running application (15 min)
4. Refer to README.md as needed (10 min)

---

## 📍 You Are Here

```
TonerTrack v2.0 Documentation
│
├─ 🚀 QUICK_START.md      ← Best starting point
├─ 📖 README.md           ← Complete reference
├─ 📝 PROJECT_SUMMARY.md  ← Project overview
├─ 🏗️ ARCHITECTURE.md     ← Technical deep-dive
└─ 📚 INDEX.md           ← You are here!
```

**Ready to begin?** → Open [QUICK_START.md](QUICK_START.md)

---

**Documentation Version**: 2.0  
**Last Updated**: November 2024  
**Total Pages**: 1,000+ lines across 5 documents  
**Estimated Read Time**: 1-2 hours for complete documentation
# Sentinel Electron Setup Checklist

Use this checklist to ensure everything is configured correctly before running the Electron app.

## ✅ Setup Checklist

### Backend Setup
- [ ] Python 3.10 installed
- [ ] Virtual environment created: `cd backend && python3 -m venv env`
- [ ] Virtual environment activated: `source env/bin/activate`
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] `.env` file created in backend/ with required variables:
  - [ ] `MSF_RPC_PASSWORD`
  - [ ] `MSF_RPC_PORT`
  - [ ] `GOOGLE_API_KEY`
  - [ ] Other API keys as needed
- [ ] Metasploit Framework installed (optional but recommended)
- [ ] MongoDB running (if required)

### Frontend Setup
- [ ] Node.js v16+ installed
- [ ] Dependencies installed: `cd frontend && npm install`
- [ ] Electron dependencies verified in package.json
- [ ] Build directory exists: `frontend/build/`
- [ ] Electron main.js created in `frontend/electron/`
- [ ] Preload script created in `frontend/electron/`

### Configuration Files
- [ ] `next.config.mjs` updated with static export settings
- [ ] `constants.js` updated to detect Electron environment
- [ ] `package.json` has Electron scripts configured
- [ ] `.gitignore` updated with Electron build artifacts
- [ ] `entitlements.mac.plist` created (for macOS)

### Optional Enhancement
- [ ] App icons created (see ICON_SETUP.md):
  - [ ] `frontend/public/icon.icns` (macOS)
  - [ ] `frontend/public/icon.ico` (Windows)
  - [ ] `frontend/public/icon.png` (Linux)

## 🚀 Quick Start Commands

### Development Mode
```bash
# One-line start (recommended)
cd frontend && ./dev-start.sh

# Or step-by-step
cd frontend
npm run electron-dev
```

### Production Build
```bash
# Interactive build script
cd frontend && ./build-prod.sh

# Or direct commands
npm run dist-mac    # macOS
npm run dist-win    # Windows
npm run dist-linux  # Linux
npm run dist        # All platforms
```

## 🧪 Testing Steps

1. **Test Backend Separately**
   ```bash
   cd backend
   source env/bin/activate
   python app.py
   # Should start on http://localhost:8000
   # Press Ctrl+C to stop
   ```

2. **Test Frontend Separately**
   ```bash
   cd frontend
   npm run dev
   # Should start on http://localhost:3000
   # Press Ctrl+C to stop
   ```

3. **Test Electron Dev Mode**
   ```bash
   cd frontend
   npm run electron-dev
   # Should open Electron window with app running
   ```

4. **Test Production Build**
   ```bash
   cd frontend
   npm run pack  # Creates unpackaged build in dist/
   # Open the built app from dist/ folder
   ```

## 🔍 Troubleshooting

### Issue: "electron: command not found"
**Solution**: Run `npm install` in frontend directory

### Issue: "Python backend failed to start"
**Solution**: 
- Check backend/env exists
- Verify .env file is configured
- Check Python dependencies: `pip install -r requirements.txt`

### Issue: "Module not found" errors
**Solution**: 
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Issue: "Port already in use"
**Solution**:
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

### Issue: "Metasploit connection failed"
**Solution**: 
- Verify Metasploit is installed: `msfconsole --version`
- Check MSF_RPC_PASSWORD in .env
- App will still work without Metasploit (limited features)

## 📋 Pre-Distribution Checklist

Before sharing your built app with others:

- [ ] Test the built app thoroughly
- [ ] Add custom app icons
- [ ] Update version number in package.json
- [ ] Test on target platform (build on macOS for .dmg, etc.)
- [ ] Include README with system requirements
- [ ] Include Metasploit installation instructions
- [ ] Sign the app (macOS/Windows for trusted installation)
- [ ] Test on a clean machine without development tools
- [ ] Create installation guide for end users

## 🎯 Next Steps

1. **Now**: Test the development environment
   ```bash
   cd frontend && npm run electron-dev
   ```

2. **After Testing**: Create a production build
   ```bash
   cd frontend && ./build-prod.sh
   ```

3. **For Distribution**: Package with icons and documentation

## 📚 Additional Resources

- Electron Documentation: https://www.electronjs.org/docs
- electron-builder Docs: https://www.electron.build/
- Next.js Static Export: https://nextjs.org/docs/app/building-your-application/deploying/static-exports
- Metasploit Framework: https://docs.metasploit.com/

---

**Status**: Setup Complete ✅  
**Version**: 1.0.0  
**Created**: March 2026

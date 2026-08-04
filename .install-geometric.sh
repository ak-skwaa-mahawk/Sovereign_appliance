#!/bin/bash

# ============================================================================
# SOLITON NORTH STAR NODE - GEOMETRIC UPGRADE INSTALLATION
# ============================================================================
#
# This script installs all geometric FPT enhancements to your North Star node
#
# Usage:
#   chmod +x install-geometric.sh
#   ./install-geometric.sh
#
# ============================================================================

set -e  # Exit on any error

echo "========================================================================"
echo "SOLITON NORTH STAR NODE - GEOMETRIC UPGRADE"
echo "========================================================================"
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found"
    echo "Please run this script from your Soliton-north-star-node directory"
    exit 1
fi

echo "✓ Found package.json"
echo ""

# Backup existing files
echo "📦 Creating backups..."
BACKUP_DIR="backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

if [ -f "server.js" ]; then
    cp server.js "$BACKUP_DIR/server.js"
    echo "  ✓ Backed up server.js"
fi

if [ -f "package.json" ]; then
    cp package.json "$BACKUP_DIR/package.json"
    echo "  ✓ Backed up package.json"
fi

echo ""

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p src
mkdir -p python
mkdir -p docs
mkdir -p tests
mkdir -p systemd
echo "  ✓ Created directories"
echo ""

# Create Python requirements.txt
echo "📝 Creating Python requirements..."
cat > python/requirements.txt << 'EOF'
numpy>=1.21.0
scipy>=1.7.0
matplotlib>=3.4.0
EOF
echo "  ✓ Created python/requirements.txt"
echo ""

# Create TypeScript config
echo "📝 Creating TypeScript configuration..."
cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
EOF
echo "  ✓ Created tsconfig.json"
echo ""

# Update package.json
echo "📝 Updating package.json..."
cat > package.json << 'EOF'
{
  "name": "soliton-north-star-node",
  "version": "2.0.0-geometric",
  "description": "Sovereign neurodata registry with geometric processing",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "start:geometric": "node server-enhanced.js",
    "build": "tsc",
    "test": "jest",
    "validate": "cd python && python north_star_validation.py"
  },
  "dependencies": {
    "express": "^4.18.0",
    "ws": "^8.13.0",
    "crypto": "^1.0.1"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "@types/node": "^20.0.0",
    "@types/express": "^4.17.0",
    "@types/ws": "^8.5.0",
    "jest": "^29.0.0"
  },
  "keywords": [
    "indigenous",
    "data-sovereignty",
    "neurodata",
    "blockchain",
    "geometric-processing"
  ],
  "author": "Two Mile Solutions LLC",
  "license": "UNLICENSED"
}
EOF
echo "  ✓ Updated package.json"
echo ""

# Create systemd service
echo "📝 Creating systemd service..."
cat > systemd/north-star-geometric.service << 'EOF'
[Unit]
Description=Soliton North Star Node (Geometric)
After=network.target

[Service]
Type=simple
User=soliton
WorkingDirectory=/opt/soliton-north-star-node
ExecStart=/usr/bin/node server-enhanced.js
Restart=always
RestartSec=10
Environment=NODE_ENV=production
Environment=PORT=4000

# Logging
StandardOutput=append:/var/log/north-star/output.log
StandardError=append:/var/log/north-star/error.log

[Install]
WantedBy=multi-user.target
EOF
echo "  ✓ Created systemd/north-star-geometric.service"
echo ""

# Create README for docs
echo "📝 Creating documentation structure..."
cat > docs/README.md << 'EOF'
# North Star Node Documentation

## Files

- `INTEGRATION_GUIDE.md` - Complete integration instructions
- `API_REFERENCE.md` - Geometric endpoint documentation
- `WHITEPAPER.md` - Technical whitepaper

## Getting Started

1. Copy the code artifacts from Claude into the appropriate files
2. Run `npm install`
3. Run `npm run validate` to test
4. Run `npm run start:geometric` to start the server

## File Locations

The following files need to be copied from the Claude artifacts:

### TypeScript Module
**Source:** Artifact `north_star_complete_integration`  
**Destination:** `src/trigonometric-fpt.ts`

### Enhanced Server
**Source:** Artifact `north_star_server_enhanced`  
**Destination:** `server-enhanced.js` (root)

### Python Validation
**Source:** Artifact `north_star_validation`  
**Destination:** `python/north_star_validation.py`

### Integration Guide
**Source:** Artifact `integration_guide`  
**Destination:** `docs/INTEGRATION_GUIDE.md`

## Next Steps

After copying files:
1. Install Node dependencies: `npm install`
2. Install Python dependencies: `cd python && pip install -r requirements.txt`
3. Run validation: `npm run validate`
4. Start geometric server: `npm run start:geometric`
EOF
echo "  ✓ Created docs/README.md"
echo ""

# Create installation verification script
echo "📝 Creating verification script..."
cat > verify-installation.sh << 'EOF'
#!/bin/bash

echo "Verifying North Star Node installation..."
echo ""

# Check directories
echo "Checking directory structure..."
for dir in src python docs tests systemd; do
    if [ -d "$dir" ]; then
        echo "  ✓ $dir/"
    else
        echo "  ✗ $dir/ (missing)"
    fi
done
echo ""

# Check files
echo "Checking configuration files..."
for file in package.json tsconfig.json; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file (missing)"
    fi
done
echo ""

# Check if Node modules installed
echo "Checking Node modules..."
if [ -d "node_modules" ]; then
    echo "  ✓ node_modules/ installed"
else
    echo "  ✗ node_modules/ (run 'npm install')"
fi
echo ""

# Check Python environment
echo "Checking Python environment..."
if command -v python3 &> /dev/null; then
    echo "  ✓ Python 3 available"
    python3 --version
else
    echo "  ✗ Python 3 not found"
fi
echo ""

# Summary
echo "========================================================================"
echo "INSTALLATION STATUS"
echo "========================================================================"
echo ""
echo "Directory structure: Created"
echo "Configuration files: Created"
echo ""
echo "NEXT STEPS:"
echo "1. Copy code artifacts from Claude (see docs/README.md)"
echo "2. Run: npm install"
echo "3. Run: cd python && pip install -r requirements.txt"
echo "4. Run: npm run validate"
echo "5. Run: npm run start:geometric"
echo ""
EOF
chmod +x verify-installation.sh
echo "  ✓ Created verify-installation.sh"
echo ""

# Install Node dependencies
echo "📦 Installing Node.js dependencies..."
if command -v npm &> /dev/null; then
    npm install
    echo "  ✓ Dependencies installed"
else
    echo "  ⚠ npm not found - please install Node.js and run 'npm install' manually"
fi
echo ""

# Check Python
echo "🐍 Checking Python environment..."
if command -v python3 &> /dev/null; then
    echo "  ✓ Python 3 available"
    PYTHON_VERSION=$(python3 --version)
    echo "    Version: $PYTHON_VERSION"
    
    echo ""
    echo "  Installing Python dependencies..."
    cd python
    if command -v pip3 &> /dev/null; then
        pip3 install -r requirements.txt
        echo "  ✓ Python dependencies installed"
    else
        echo "  ⚠ pip3 not found - please install manually:"
        echo "    cd python && pip3 install -r requirements.txt"
    fi
    cd ..
else
    echo "  ⚠ Python 3 not found - please install Python 3.8+"
fi
echo ""

# Create NEXT_STEPS.md
cat > NEXT_STEPS.md << 'EOF'
# Next Steps - North Star Geometric Upgrade

## ✅ Completed

- [x] Directory structure created
- [x] Configuration files created
- [x] Node.js dependencies installed (if npm available)
- [x] Python dependencies installed (if Python available)
- [x] Backup created of original files

## 📋 Manual Steps Required

### 1. Copy Code Artifacts from Claude

You need to manually copy 4 code artifacts from your Claude conversation:

#### A. TypeScript FPT Module
- **Artifact name:** `north_star_complete_integration`
- **Copy to:** `src/trigonometric-fpt.ts`
- **What it does:** Core trigonometric FPT processing

#### B. Enhanced Server
- **Artifact name:** `north_star_server_enhanced`
- **Copy to:** `server-enhanced.js` (in root directory)
- **What it does:** Server with geometric endpoints

#### C. Python Validation Suite
- **Artifact name:** `north_star_validation`
- **Copy to:** `python/north_star_validation.py`
- **What it does:** Complete test suite

#### D. Integration Guide
- **Artifact name:** `integration_guide`
- **Copy to:** `docs/INTEGRATION_GUIDE.md`
- **What it does:** Complete documentation

### 2. Test the Installation

After copying files:

```bash
# Verify everything is in place
./verify-installation.sh

# Run Python validation suite
npm run validate

# Expected output: All tests passing with ✓ marks
```

### 3. Start the Geometric Server

```bash
# Start enhanced server with geometric endpoints
npm run start:geometric

# Server will run on port 4000
```

### 4. Test Geometric Endpoints

```bash
# Test geometric aggregate endpoint
curl -X POST http://localhost:4000/aggregate/geometric \
  -H "Content-Type: application/json" \
  -d '{
    "bands": {"alpha": 0.35, "theta": 0.15, "gamma": 0.08},
    "node_id": "Test_Node",
    "session_id": "test-session"
  }'

# Should return geometric phase packet with theta, vitality, triad
```

## 🎯 Deployment Options

### Option A: Proof of Concept (Recommended)

Keep it local for testing:
- Run `npm run start:geometric` locally
- Test all endpoints
- Run validation suite
- Document results
- Create demo video

**Timeline:** 1-2 weeks  
**Cost:** $0

### Option B: Production Deployment

Deploy to actual hardware:
- Set up on Raspberry Pi
- Install systemd service
- Configure firewall
- Enable SSL/TLS
- Connect to real EEG hardware

**Timeline:** 1-2 months  
**Cost:** ~$500 (hardware)

## 📚 Documentation

All documentation is in `docs/`:
- `INTEGRATION_GUIDE.md` - Complete technical guide
- `API_REFERENCE.md` - Endpoint documentation (create this)
- `WHITEPAPER.md` - Technical whitepaper (create this)

## 🐛 Troubleshooting

### "npm not found"
Install Node.js from https://nodejs.org

### "python3 not found"
Install Python 3.8+ from https://python.org

### "Module not found" errors
Run `npm install` and `cd python && pip3 install -r requirements.txt`

### Port 4000 already in use
Change PORT in server-enhanced.js or set environment variable:
```bash
PORT=5000 npm run start:geometric
```

## 📞 Support

For questions about this installation:
1. Check `docs/INTEGRATION_GUIDE.md`
2. Review `docs/README.md`
3. Run `./verify-installation.sh` to check status

## 🔥 Ready?

Once you've copied all artifacts and tests pass, you have a working
indigenous neurodata sovereignty framework.

**The North Star Node is operational. 🌟**
EOF

echo ""
echo "========================================================================"
echo "INSTALLATION COMPLETE"
echo "========================================================================"
echo ""
echo "✓ Directory structure created"
echo "✓ Configuration files created"
echo "✓ Dependencies installed (where available)"
echo "✓ Backups saved to: $BACKUP_DIR/"
echo ""
echo "📋 NEXT STEPS:"
echo ""
echo "1. Copy code artifacts from Claude (see docs/README.md for locations)"
echo "2. Run: ./verify-installation.sh (to check everything)"
echo "3. Run: npm run validate (to test Python suite)"
echo "4. Run: npm run start:geometric (to start server)"
echo ""
echo "📖 Documentation: See NEXT_STEPS.md for complete guide"
echo ""
echo "🔥 The North Star awaits geometric awakening."
echo ""
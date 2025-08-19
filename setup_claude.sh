#!/bin/bash

# Setup script for testing dbt-core-mcp with Claude Desktop

echo "🚀 dbt-core-mcp Setup for Claude Desktop"
echo "========================================"
echo ""

# Get the current directory
CURRENT_DIR=$(pwd)

# Check Python version
echo "1. Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi
echo "✅ Python is installed"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "2. Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "2. Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "3. Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Install dependencies
echo "4. Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Install test dependencies
echo "5. Installing test dependencies..."
pip install -q pytest pytest-asyncio pytest-cov
echo "✅ Test dependencies installed"
echo ""

# Run tests
echo "6. Running unit tests..."
python -m pytest tests/ -v --tb=short
if [ $? -eq 0 ]; then
    echo "✅ All tests passed"
else
    echo "⚠️  Some tests failed"
fi
echo ""

# Run local test
echo "7. Running local integration test..."
python test_local.py
echo ""

# Generate Claude Desktop configuration
echo "8. Generating Claude Desktop configuration..."
cat > claude_desktop_config.json <<EOF
{
  "mcpServers": {
    "dbt-core-mcp": {
      "command": "python",
      "args": ["${CURRENT_DIR}/main.py"],
      "env": {
        "LOG_LEVEL": "INFO",
        "CACHE_SIZE": "1000",
        "CACHE_TTL_MINUTES": "60"
      }
    }
  }
}
EOF

echo "✅ Configuration saved to claude_desktop_config.json"
echo ""

# Display instructions
echo "========================================="
echo "📋 Setup Complete! Next Steps:"
echo "========================================="
echo ""
echo "1. Add the following to your Claude Desktop configuration:"
echo "   - macOS: ~/Library/Application Support/Claude/claude_desktop_config.json"
echo "   - Windows: %APPDATA%\\Claude\\claude_desktop_config.json"
echo "   - Linux: ~/.config/Claude/claude_desktop_config.json"
echo ""
echo "2. Copy the configuration from claude_desktop_config.json"
echo ""
echo "3. Restart Claude Desktop"
echo ""
echo "4. Test with Claude by asking:"
echo "   'Parse this dbt project file: [paste your dbt_project.yml]'"
echo "   'Search for customer-related models'"
echo "   'Show me the model lineage'"
echo ""
echo "========================================="
echo "Alternative: Run with Docker"
echo "========================================="
echo ""
echo "1. Build Docker image:"
echo "   docker build -t dbt-core-mcp ."
echo ""
echo "2. Run Docker container:"
echo "   docker run --rm -it dbt-core-mcp"
echo ""
echo "3. Or use docker-compose:"
echo "   docker-compose up"
echo ""

# Keep virtual environment info
echo "To manually activate the virtual environment later:"
echo "source venv/bin/activate"
# Testing dbt-core-mcp Locally

This guide will help you test the dbt-core-mcp server on your local machine.

## Quick Start

### 1. Automated Setup (Recommended)

Run the setup script:

```bash
./setup_claude.sh
```

This will:
- Create a virtual environment
- Install all dependencies
- Run unit tests
- Execute integration tests
- Generate Claude Desktop configuration

### 2. Manual Setup

#### Step 1: Create and activate virtual environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Step 2: Install dependencies

```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio  # For testing
```

#### Step 3: Run tests

```bash
# Run unit tests
pytest tests/ -v

# Run local integration test
python test_local.py
```

## Testing Methods

### Method 1: Standalone Python Script

The easiest way to test is using the provided test script:

```bash
python test_local.py
```

This tests all MCP tools with sample dbt data and verifies:
- Project parsing
- Schema parsing
- Model searching
- Lineage extraction
- Caching functionality

### Method 2: Unit Tests

Run the comprehensive test suite:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_parser.py

# Run with coverage
pytest --cov=src --cov-report=html
```

### Method 3: Interactive Python

Test individual components interactively:

```python
# Start Python interpreter
python

# Test the parser
from src.dbt_parser import DbtParser

project_yml = """
name: test_project
version: 1.0.0
models:
  test_project:
    +materialized: table
"""

project = DbtParser.parse_dbt_project(project_yml)
print(project.config.name)  # Output: test_project
```

### Method 4: With Claude Desktop

1. **Generate configuration:**
   ```bash
   python test_local.py  # This creates claude_desktop_config.json
   ```

2. **Add to Claude Desktop config:**
   
   Find your Claude Desktop configuration file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

3. **Add the MCP server configuration:**
   ```json
   {
     "mcpServers": {
       "dbt-core-mcp": {
         "command": "python",
         "args": ["/path/to/dbt-core-mcp/main.py"]
       }
     }
   }
   ```

4. **Restart Claude Desktop**

5. **Test in Claude:**
   - Ask: "Can you parse this dbt project file?" (paste your dbt_project.yml)
   - Ask: "Search for customer-related models"
   - Ask: "Show me the model lineage"

### Method 5: Docker Testing

1. **Build the Docker image:**
   ```bash
   docker build -t dbt-core-mcp .
   ```

2. **Run the container:**
   ```bash
   docker run --rm -it dbt-core-mcp
   ```

3. **Test with docker-compose:**
   ```bash
   docker-compose up
   ```

## Testing with Real dbt Projects

To test with your actual dbt project files:

1. **Create a test script:**

```python
# test_my_project.py
import asyncio
from src.server import DbtMCPServer

async def test_my_project():
    server = DbtMCPServer()
    
    # Read your actual dbt_project.yml
    with open('path/to/your/dbt_project.yml', 'r') as f:
        project_yml = f.read()
    
    # Parse it
    result = await server._parse_dbt_project({
        "dbt_project_yml_content": project_yml
    })
    
    print(result[0].text)
    
    # Read your schema.yml files
    with open('path/to/your/schema.yml', 'r') as f:
        schema_yml = f.read()
    
    # Parse schemas
    result = await server._parse_dbt_schema({
        "schema_yml_content": schema_yml
    })
    
    print(result[0].text)

asyncio.run(test_my_project())
```

2. **Run it:**
   ```bash
   python test_my_project.py
   ```

## Troubleshooting

### Common Issues

1. **Import errors:**
   - Make sure virtual environment is activated
   - Reinstall dependencies: `pip install -r requirements.txt`

2. **MCP import errors:**
   - Update to latest MCP: `pip install --upgrade mcp`

3. **YAML parsing errors:**
   - Validate your YAML files online first
   - Check for tabs vs spaces (use spaces only)

4. **Claude Desktop doesn't see the server:**
   - Check the config file path is correct
   - Restart Claude Desktop completely
   - Check logs: `tail -f ~/Library/Logs/Claude/mcp*.log` (macOS)

### Debug Mode

Run with debug logging:

```bash
python main.py --log-level DEBUG
```

Or set environment variable:

```bash
LOG_LEVEL=DEBUG python main.py
```

## Performance Testing

Test with large projects:

```python
# test_performance.py
import time
import asyncio
from src.dbt_parser import DbtParser

# Generate a large schema with many models
models = []
for i in range(1000):
    models.append(f"""
  - name: model_{i}
    description: "Model {i}"
    columns:
      - name: id
        tests: [unique, not_null]
      - name: value
        description: "Value field"
""")

schema_yml = f"""
version: 2
models:
{''.join(models)}
"""

start = time.time()
result = DbtParser.parse_schema_file(schema_yml)
end = time.time()

print(f"Parsed {len(result['models'])} models in {end-start:.2f} seconds")
```

## Continuous Testing

For development, use watch mode:

```bash
# Install pytest-watch
pip install pytest-watch

# Run tests on file changes
ptw -- --tb=short
```

## Next Steps

After successful local testing:

1. **Integration Testing**: Test with real dbt projects
2. **Load Testing**: Test with large schemas (100+ models)
3. **Claude Integration**: Set up and test with Claude Desktop
4. **Docker Deployment**: Build and test Docker image
5. **CI/CD**: Set up GitHub Actions for automated testing

## Support

If you encounter issues:
1. Check the logs: `python main.py --log-level DEBUG`
2. Run diagnostics: `python test_local.py`
3. Open an issue on GitHub with error details
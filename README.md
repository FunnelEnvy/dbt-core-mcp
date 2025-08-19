# dbt-context-provider

A FastMCP-based context provider that delivers rich database structure information from dbt projects to LLMs. Automatically syncs with GitHub repositories to provide always-fresh dbt metadata for intelligent SQL query generation.

## Overview

`dbt-context-provider` is a specialized MCP server that:
- 🔄 **Auto-syncs** with GitHub repositories to fetch dbt project files
- 📊 **Provides rich context** about database structure, models, columns, and relationships
- 🎯 **Focuses on context** - designed to work alongside SQL execution servers
- 🚀 **Built with FastMCP** for simple, efficient tool and prompt definitions
- ⚡ **Smart caching** with configurable TTL for optimal performance

## Key Features

- **Repository-Specific Configuration**: Each instance targets specific dbt models via glob patterns
- **Automatic GitHub Sync**: Fetches and caches dbt files, refreshing based on TTL
- **Context-Optimized Tools**: Purpose-built tools for providing database context to LLMs
- **Rich Model Information**: Complete details on columns, data types, tests, and relationships
- **Intelligent Search**: Find relevant models and columns for query construction
- **Lineage Tracking**: Understand data flow and dependencies

## Installation

### Prerequisites

- Python 3.8+
- GitHub Personal Access Token with repository read access
- Target dbt repository on GitHub

### From Source

```bash
git clone https://github.com/FunnelEnvy/dbt-core-mcp.git
cd dbt-core-mcp
pip install -r requirements.txt
```

### Configuration

Create a `.env` file with your configuration:

```bash
# Required
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_your_token_here
GITHUB_REPOSITORY=YourOrg/your-dbt-repo

# Schema patterns (glob patterns supported)
DBT_SCHEMA_PATTERNS=models/**/*.yml
# Or target specific directories:
# DBT_SCHEMA_PATTERNS=models/marts/forecasting/*.yml,models/marts/reform/*.yml

# Optional
DBT_PROJECT_PATH=dbt_project.yml  # Path to dbt_project.yml
CACHE_TTL_MINUTES=60               # How often to check for updates
LOG_LEVEL=INFO
```

## Claude Desktop Integration

Add to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### Single Repository Configuration

```json
{
  "mcpServers": {
    "dbt-context": {
      "command": "python",
      "args": ["/path/to/dbt-core-mcp/main.py"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token",
        "GITHUB_REPOSITORY": "YourOrg/your-dbt-repo",
        "DBT_SCHEMA_PATTERNS": "models/**/*.yml"
      }
    }
  }
}
```

### Multiple Focused Configurations

Run multiple instances for different model subsets:

```json
{
  "mcpServers": {
    "dbt-forecasting": {
      "command": "python",
      "args": ["/path/to/dbt-core-mcp/main.py"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token",
        "GITHUB_REPOSITORY": "FunnelEnvy/funnelenvy_dbt",
        "DBT_SCHEMA_PATTERNS": "models/marts/forecasting/*.yml"
      }
    },
    "dbt-reform": {
      "command": "python",
      "args": ["/path/to/dbt-core-mcp/main.py"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token",
        "GITHUB_REPOSITORY": "FunnelEnvy/funnelenvy_dbt",
        "DBT_SCHEMA_PATTERNS": "models/marts/reform/*.yml"
      }
    }
  }
}
```

## Available Tools

### `get_database_context()`
Returns comprehensive database structure overview including all models, schemas, and relationships. Automatically refreshes from GitHub if cache is stale.

**Example Response:**
```
# Database Context: YourOrg/your-dbt-repo
Total Models: 47
Total Sources: 12

## Schemas (4):
- staging: 15 models
- intermediate: 12 models
- marts: 20 models
```

### `get_model_context(model_name: str)`
Get detailed information about a specific model including columns, data types, tests, and documentation.

**Example:**
```python
get_model_context("customer_summary")
```

### `search_models(query: str, filters: Optional)`
Search for models by name, description, columns, or tags. Supports filtering by schema, tags, or materialization.

**Example:**
```python
search_models("revenue", filter_schema="marts")
```

### `get_model_lineage(model_name: str)`
Understand data flow with upstream and downstream dependencies.

### `get_column_info(model_name: str, column_name: str)`
Get detailed column information including data type, constraints, tests, and documentation.

### `list_available_models(schema_filter: Optional[str])`
List all models, optionally filtered by schema.

### `refresh_context()`
Manually trigger a refresh from GitHub (normally automatic based on TTL).

## Prompts

### `database_overview`
Provides a high-level introduction to the database structure and available commands.

### `sql_helper(query_intent: str)`
Gets database context relevant to a specific SQL query intent, suggesting relevant models and columns.

## Usage Examples

### Basic Workflow

1. **User**: "I need to write a query to analyze customer revenue"

2. **Claude** calls `search_models("customer revenue")`:
   ```
   Found 3 models:
   - customer_summary (marts): Customer aggregated metrics
   - revenue_daily (marts): Daily revenue by customer
   - customer_orders (intermediate): Customer order history
   ```

3. **Claude** calls `get_model_context("revenue_daily")`:
   ```
   Model: revenue_daily
   Columns:
   - customer_id (string): Unique customer identifier
   - date (date): Revenue date
   - revenue_amount (numeric): Total revenue
   - order_count (integer): Number of orders
   ```

4. **Claude** generates SQL with correct table and column names

### Understanding Data Flow

```python
# Check dependencies
get_model_lineage("customer_summary")

# Response:
Upstream Dependencies:
- customer_orders
- customer_attributes

Downstream Dependencies:
- executive_dashboard
- customer_segments
```

## Glob Pattern Support

The `DBT_SCHEMA_PATTERNS` environment variable supports various glob patterns:

- `models/**/*.yml` - All YAML files under models (recursive)
- `models/marts/*.yml` - All YAML files in marts directory
- `models/*/schema.yml` - Schema.yml in any subdirectory
- `models/marts/finance/*.yml,models/marts/marketing/*.yml` - Multiple specific paths

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────┐
│   Claude    │────▶│ dbt-context-     │────▶│ GitHub  │
│             │     │ provider         │     │  Repo   │
└─────────────┘     └──────────────────┘     └─────────┘
       │                     │
       │                     ├─── Auto-fetch on startup
       │                     ├─── Cache with TTL
       │                     └─── Refresh on demand
       │
       ▼
┌─────────────┐
│ SQL Execute │
│ MCP Server  │
└─────────────┘
```

## Performance

- **Smart Caching**: Files are cached with configurable TTL (default 60 minutes)
- **Selective Fetching**: Only fetches files matching configured patterns
- **Lazy Loading**: Syncs on startup, then only when cache expires
- **Efficient Search**: In-memory indices for fast model and column searches

## Troubleshooting

### GitHub Authentication Issues
- Ensure your PAT has repository read access
- Test with: `curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user`

### Pattern Matching
- Use `DBT_SCHEMA_PATTERNS=models/` to test with a smaller subset first
- Check logs to see which files are being fetched

### Cache Issues
- Set `CACHE_TTL_MINUTES=1` for development to force frequent refreshes
- Use `refresh_context()` tool to manually trigger sync

## Development

### Running Tests

```bash
# Test the server locally (without Claude)
python test.py

# Run unit tests
pytest tests/
```

### Debug Mode

```bash
LOG_LEVEL=DEBUG python main.py
```

## Limitations

- Requires dbt files to be in a GitHub repository
- Does not execute SQL queries (use a separate SQL MCP server)
- Limited to files matching configured patterns
- Cache TTL applies to all files (no per-file refresh)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Support

- **Issues**: [GitHub Issues](https://github.com/FunnelEnvy/dbt-core-mcp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/FunnelEnvy/dbt-core-mcp/discussions)
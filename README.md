# dbt-context-provider

A FastMCP-based context provider that delivers rich database structure information from dbt projects to LLMs. Automatically syncs with GitHub repositories to provide always-fresh dbt metadata for intelligent SQL query generation.

## Overview

`dbt-context-provider` is a specialized MCP server that:
- 🔄 **Auto-syncs** with GitHub repositories to fetch dbt project files
- 📊 **Provides rich context** about database structure, models, columns, and relationships
- 🎯 **Focuses on context** - designed to work alongside SQL execution servers
- 🚀 **Built with FastMCP** for simple, efficient tool and prompt definitions
- ⚡ **Smart caching** with configurable TTL for optimal performance

## Required Workflow

**⚠️ CRITICAL: This MCP must be consulted BEFORE any SQL execution**

The dbt-context-provider contains essential business logic and constraints that are NOT available in database INFORMATION_SCHEMA:
- ✅ **Accepted column values** from dbt tests (e.g., status: 'active'|'pending'|'closed')
- ✅ **Business constraints** and validation rules
- ✅ **Column relationships** and dependencies
- ✅ **Custom schema locations** from generate_schema_name macros
- ✅ **Data quality rules** from dbt tests

### Correct Query Workflow

1. **SEARCH** - Use `search_models()` to find relevant tables
2. **UNDERSTAND** - Use `get_model_context()` for each table to get column details
3. **INSPECT** - Use `get_column_info()` for columns with business logic
4. **EXECUTE** - Only after steps 1-3, write and run SQL queries

### What Happens If You Skip This MCP

- ❌ Incorrect filter conditions due to unknown enum values
- ❌ Missing critical business logic constraints
- ❌ Querying wrong schemas or datasets
- ❌ Invalid JOIN conditions
- ❌ Incomplete or incorrect query results

## Key Features

- **Repository-Specific Configuration**: Each instance targets specific dbt models via glob patterns
- **Automatic GitHub Sync**: Fetches and caches dbt files, refreshing based on TTL
- **Profile-Aware**: Parses profiles.yml to extract database/dataset configuration
- **Database Agnostic**: Works with BigQuery, Postgres, Redshift, Snowflake, and more
- **Context-Optimized Tools**: Purpose-built tools for providing database context to LLMs
- **Rich Model Information**: Complete details on columns, data types, tests, and relationships
- **Intelligent Search**: Find relevant models and columns for query construction
- **Lineage Tracking**: Understand data flow and dependencies

## Installation

### Prerequisites

- Python 3.10+ (if running from source) - required for FastMCP
- Docker (if using container)
- GitHub Personal Access Token with repository read access
- Target dbt repository on GitHub

### Quick Start (Docker)

```bash
docker pull ghcr.io/funnelenvy/dbt-core-mcp:latest
```

### From Source

```bash
git clone https://github.com/FunnelEnvy/dbt-core-mcp.git
cd dbt-core-mcp
pip install -r requirements.txt
```

### Configuration

#### For Claude Desktop
All configuration is provided directly in `claude_desktop_config.json` - no `.env` file needed (see integration section below).

#### For Local Development/Testing
Create a `.env` file for local testing with `python test.py`:

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
DBT_PROFILES_PATH=profiles.yml    # Path to profiles.yml
DBT_TARGET=prod                   # Target to use from profiles.yml (default: prod)
DBT_SCHEMA_OVERRIDE=schema_name   # Override schema/dataset (for custom generate_schema_name)
CACHE_TTL_MINUTES=60               # How often to check for updates
LOG_LEVEL=INFO
```

## Docker Support

### Quick Start with Pre-built Image

Use our pre-built image from GitHub Container Registry - no build required!

```bash
# Pull the latest image
docker pull ghcr.io/funnelenvy/dbt-core-mcp:latest

# Run with your configuration
docker run --rm \
  -e GITHUB_PERSONAL_ACCESS_TOKEN=ghp_your_token \
  -e GITHUB_REPOSITORY=YourOrg/your-repo \
  -e DBT_SCHEMA_PATTERNS="models/**/*.yml" \
  ghcr.io/funnelenvy/dbt-core-mcp:latest

# Or using an .env file
docker run --rm --env-file .env ghcr.io/funnelenvy/dbt-core-mcp:latest
```

### Build Your Own Image (Optional)

If you want to build the image locally:

```bash
docker build -t dbt-context-provider .
```

### Using docker-compose

Create a `docker-compose.yml`:

```yaml
version: '3.8'
services:
  dbt-context:
    build: .
    environment:
      - GITHUB_PERSONAL_ACCESS_TOKEN=${GITHUB_PERSONAL_ACCESS_TOKEN}
      - GITHUB_REPOSITORY=${GITHUB_REPOSITORY}
      - DBT_SCHEMA_PATTERNS=${DBT_SCHEMA_PATTERNS:-models/**/*.yml}
      - CACHE_TTL_MINUTES=${CACHE_TTL_MINUTES:-60}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
```

Then run:
```bash
# With .env file
docker-compose up

# Or with inline environment variables
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_token GITHUB_REPOSITORY=YourOrg/repo docker-compose up
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

### Using Docker in Claude Desktop

```json
{
  "mcpServers": {
    "dbt-context": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-e",
        "GITHUB_PERSONAL_ACCESS_TOKEN",
        "-e",
        "GITHUB_REPOSITORY",
        "-e",
        "DBT_SCHEMA_PATTERNS",
        "ghcr.io/funnelenvy/dbt-core-mcp:latest"
      ],
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
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-e",
        "GITHUB_PERSONAL_ACCESS_TOKEN",
        "-e",
        "GITHUB_REPOSITORY",
        "-e",
        "DBT_SCHEMA_PATTERNS",
        "ghcr.io/funnelenvy/dbt-core-mcp:latest"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token",
        "GITHUB_REPOSITORY": "FunnelEnvy/funnelenvy_dbt",
        "DBT_SCHEMA_PATTERNS": "models/marts/forecasting/*.yml"
      }
    },
    "dbt-reform": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-e",
        "GITHUB_PERSONAL_ACCESS_TOKEN",
        "-e",
        "GITHUB_REPOSITORY",
        "-e",
        "DBT_SCHEMA_PATTERNS",
        "ghcr.io/funnelenvy/dbt-core-mcp:latest"
      ],
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

## Custom Schema Names (generate_schema_name)

If your dbt project uses a custom `generate_schema_name` macro that doesn't follow dbt's default pattern, use `DBT_SCHEMA_OVERRIDE` to specify the actual database/dataset where your tables exist.

### When to use DBT_SCHEMA_OVERRIDE

Use this when your `generate_schema_name` macro:
- Uses custom schema names directly in production (e.g., `marts_forecasting` instead of `dbt_marts_forecasting`)
- Has environment-specific logic that changes schema names
- Implements any non-standard schema naming pattern

### Example

If your macro looks like this:
```sql
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if target.name == "prod" -%}
        {{ custom_schema_name | trim }}  -- Uses custom name directly
    {%- else -%}
        {{ target.schema }}_{{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
```

Then in production, models with `+schema: marts_forecasting` will be in the `marts_forecasting` dataset/schema, not `dbt_marts_forecasting`.

Set the override in your configuration:
```json
"env": {
  "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token",
  "GITHUB_REPOSITORY": "YourOrg/your-dbt-repo",
  "DBT_SCHEMA_PATTERNS": "models/marts/forecasting/*.yml",
  "DBT_SCHEMA_OVERRIDE": "marts_forecasting"
}
```

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

### Testing Without Claude

You have several options for local testing:

#### Option 1: Using .env file
```bash
cp .env.example .env
# Edit .env with your GitHub token and repository
python test.py
```

#### Option 2: Using environment variables directly
```bash
export GITHUB_PERSONAL_ACCESS_TOKEN=ghp_your_token
export GITHUB_REPOSITORY=YourOrg/your-repo
export DBT_SCHEMA_PATTERNS="models/**/*.yml"
python test.py
```

#### Option 3: Using Docker
```bash
docker run --rm \
  -e GITHUB_PERSONAL_ACCESS_TOKEN=ghp_your_token \
  -e GITHUB_REPOSITORY=YourOrg/your-repo \
  -e DBT_SCHEMA_PATTERNS="models/**/*.yml" \
  ghcr.io/funnelenvy/dbt-core-mcp:latest python test.py
```

### Running Unit Tests

```bash
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
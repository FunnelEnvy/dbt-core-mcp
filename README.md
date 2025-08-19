# dbt-core-mcp

A generic, open-source MCP (Model Context Protocol) server for parsing and analyzing dbt projects. This server works with any dbt repository structure and provides rich metadata access for AI-powered analysis workflows.

## Overview

`dbt-core-mcp` is a Python-based MCP server that:
- Parses dbt project files (`dbt_project.yml`, `schema.yml`) through Claude's file access
- Structures and indexes dbt metadata for efficient querying
- Provides comprehensive model information via MCP tools
- Works with any dbt project structure (staging/intermediate/marts patterns)
- Integrates seamlessly with warehouse-specific MCP servers (BigQuery, Snowflake, etc.)

## Features

- **Universal Compatibility**: Works with any dbt project structure
- **Warehouse Agnostic**: Supports BigQuery, Snowflake, Postgres, Redshift, Databricks, and more
- **Rich Metadata Access**: Full access to models, columns, tests, tags, and configurations
- **Smart Search**: Search across names, descriptions, columns, and tags
- **Lineage Tracking**: Extract model dependencies and relationships
- **Performance Optimized**: In-memory caching with configurable TTL
- **Production Ready**: Docker support, health checks, and comprehensive logging

## Quick Start

### Installation

#### Using Docker (Recommended)

```bash
docker pull ghcr.io/your-org/dbt-core-mcp:latest
docker run -d --name dbt-core-mcp ghcr.io/your-org/dbt-core-mcp:latest
```

#### Using pip

```bash
pip install dbt-core-mcp
dbt-core-mcp
```

#### From Source

```bash
git clone https://github.com/your-org/dbt-core-mcp.git
cd dbt-core-mcp
pip install -r requirements.txt
python main.py
```

### Claude Desktop Integration

Add to your Claude Desktop configuration:

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

Or with Docker:

```json
{
  "mcpServers": {
    "dbt-core-mcp": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "ghcr.io/your-org/dbt-core-mcp:latest"]
    }
  }
}
```

## Supported dbt Patterns

### Project Structures
- Standard layouts (staging → intermediate → marts)
- Multiple schema files per directory
- Nested folder organizations
- Custom folder structures

### dbt Features
- All materialization types (table, view, incremental, ephemeral, snapshot)
- Column-level documentation and tests
- Model configurations and meta fields
- Tags for organization
- Sources, exposures, and metrics
- Custom tests and constraints
- Pre/post hooks and grants

## Available MCP Tools

### parse_dbt_project
Parse a `dbt_project.yml` file to understand project structure.

**Input:**
- `dbt_project_yml_content`: The content of dbt_project.yml file

**Output:**
- Project metadata including name, version, profile
- Model configuration hierarchy
- Variable definitions
- Inferred warehouse type

### parse_dbt_schema
Parse a `schema.yml` file to extract model definitions.

**Input:**
- `schema_yml_content`: The content of schema.yml file
- `project_context` (optional): Project configuration context

**Output:**
- Parsed models with columns, tests, and configurations
- Sources, exposures, and metrics
- Comprehensive metadata for each model

### get_model_info
Get detailed information about a specific dbt model.

**Input:**
- `model_name`: The name of the dbt model

**Output:**
- Complete model details including columns, tests, tags
- Documentation coverage
- Test coverage by column
- Lineage relationships

### search_models
Search models by name, description, columns, tags, or meta fields.

**Input:**
- `query`: Search query string
- `filters` (optional): Filter by tags, schema, or materialization

**Output:**
- Ranked search results
- Relevance scoring
- Filtered by specified criteria

### list_datasets
Show how models map to warehouse datasets/schemas.

**Input:**
- `warehouse_type` (optional): bigquery, snowflake, postgres, etc.

**Output:**
- Dataset/schema organization
- Model groupings by dataset
- Warehouse-specific mappings

### get_model_lineage
Extract lineage relationships for a model.

**Input:**
- `model_name`: The name of the model
- `depth` (optional): Depth of lineage traversal (1-5)

**Output:**
- Upstream dependencies (refs and sources)
- Downstream dependents
- Dependency depth

### list_model_tags
Discover organizational patterns through tags.

**Output:**
- All tags used across models
- Model counts per tag
- Tag-based organization insights

### get_models_by_materialization
Find models by materialization type.

**Input:**
- `materialization_type`: table, view, incremental, etc.

**Output:**
- Models using specified materialization
- Configuration details
- Schema and database locations

## Example Workflows

### Basic Analysis Workflow

```
User: "Get the dbt_project.yml from github.com/myorg/analytics-dbt"
→ GitHub MCP fetches the project file

User: "Parse this dbt project and show me the structure"
→ dbt-core-mcp parses and returns project organization

User: "Get all schema.yml files from the models directory"
→ GitHub MCP fetches schema files

User: "Parse these schemas and search for customer-related models"
→ dbt-core-mcp parses schemas and searches for 'customer' models

User: "Show me the lineage for customer_summary model"
→ dbt-core-mcp returns upstream and downstream dependencies
```

### Integration with Warehouse MCP

```
User: "Parse the dbt project to understand the data model"
→ dbt-core-mcp provides model metadata

User: "Query the customer_dim table with proper column context"
→ BigQuery MCP uses dbt metadata for intelligent querying

User: "Which columns in customer_dim have data quality tests?"
→ dbt-core-mcp returns tested columns with test details
```

## Configuration

### Environment Variables

```bash
# Cache settings
CACHE_SIZE=1000              # Maximum cached items
CACHE_TTL_MINUTES=60         # Cache expiration time

# Server settings
LOG_LEVEL=INFO               # Logging level (DEBUG, INFO, WARNING, ERROR)
MCP_SERVER_NAME=dbt-core-mcp # Server identifier

# Performance tuning
MAX_MEMORY_MB=512            # Memory limit for Docker
ENABLE_CACHE_WARMING=false   # Pre-load cache on startup
```

### Command Line Arguments

```bash
python main.py --log-level DEBUG --cache-size 2000 --cache-ttl 120
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/your-org/dbt-core-mcp.git
cd dbt-core-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run in development mode
python main.py --dev
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_parser.py
```

### Building Docker Image

```bash
# Build the image
docker build -t dbt-core-mcp:latest .

# Run the container
docker run --rm -it dbt-core-mcp:latest

# With custom configuration
docker run --rm -it \
  -e LOG_LEVEL=DEBUG \
  -e CACHE_SIZE=2000 \
  dbt-core-mcp:latest
```

## API Reference

### Tool Schemas

Each tool accepts JSON input and returns structured JSON output. See the [API Documentation](docs/api.md) for detailed schemas.

### Error Handling

All tools return descriptive error messages:
- Invalid YAML format
- Model not found
- Missing required fields
- Cache errors

### Performance Considerations

- Parsing large projects: Use incremental parsing for projects with many schema files
- Cache management: Adjust CACHE_SIZE based on project size
- Memory usage: Monitor with get_memory_usage_estimate()
- Search performance: Indexed for fast lookups

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Process

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

### Code Standards

- Follow PEP 8 style guidelines
- Add type hints to all functions
- Include docstrings for public methods
- Write tests for new features

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/your-org/dbt-core-mcp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/dbt-core-mcp/discussions)
- **Documentation**: [Full Documentation](https://your-org.github.io/dbt-core-mcp)

## Roadmap

- [ ] Support for dbt Cloud API integration
- [ ] Advanced lineage visualization
- [ ] SQL parsing for deeper lineage extraction
- [ ] Integration with dbt test results
- [ ] Support for custom dbt macros
- [ ] Real-time file watching mode
- [ ] Multi-project support

## Acknowledgments

Built with the [MCP Python SDK](https://github.com/anthropics/mcp-python) by Anthropic.
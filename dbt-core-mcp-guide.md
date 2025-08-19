# Building dbt-core-mcp: A Generic dbt MCP Server

This guide will walk you through creating a generic, open-source Python MCP server that parses dbt project metadata and serves it to Claude for analysis. This server works with any dbt repository structure.

## Overview

You'll build `dbt-core-mcp` using the `mcp` Python SDK that:
- Reads dbt files through Claude's GitHub MCP integration
- Parses and structures dbt metadata generically
- Provides clean model metadata via MCP tools
- Works with any dbt project structure
- Integrates with existing BigQuery/Snowflake/etc. MCP setups

## Prerequisites

- Claude Code installed and configured
- GitHub MCP already configured in Claude Desktop
- Docker installed (recommended for team distribution)

## Step 1: Generic Project Setup

Use Claude Code to create the open-source project structure:

```bash
claude-code "Create a generic, open-source Python MCP server called dbt-core-mcp:

dbt-core-mcp/
├── src/
│   ├── __init__.py
│   ├── server.py
│   ├── dbt_parser.py
│   ├── models.py
│   └── cache.py
├── tests/
│   ├── __init__.py
│   ├── test_parser.py
│   ├── test_models.py
│   └── fixtures/
│       ├── sample_dbt_project.yml
│       └── sample_schema.yml
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── LICENSE
└── README.md

This is a generic MCP server that can parse any dbt project structure.

Required Python packages:
- mcp>=1.0.0
- pyyaml>=6.0
- pydantic>=2.0
- python-dotenv

MCP tools to implement:
- parse_dbt_project: Parse any dbt_project.yml file
- parse_dbt_schema: Parse any schema.yml file
- get_model_info: Get details for any model
- search_models: Search across any parsed models
- list_datasets: Show dataset mappings for any warehouse
- get_model_lineage: Extract basic lineage from model definitions

Make this completely generic - no business-specific logic."
```

## Step 2: Generic Pydantic Models

Define universal dbt data structures:

```bash
claude-code "Create models.py with generic pydantic models for any dbt project:

1. Core universal models:
   - DbtColumn: name, description, data_type, constraints, tests, meta
   - DbtModel: name, description, columns, config, tests, tags, meta, materialization
   - DbtProject: name, version, profile, model_paths, vars, models config tree
   - DbtTest: name, type, severity, config
   - ModelRegistry: container for all parsed data with search capabilities

2. Configuration models:
   - ModelConfig: materialized, schema, tags, meta, docs, etc.
   - ProjectConfig: model configurations by path/name
   - WarehouseConfig: dataset/schema mappings for different warehouses

3. Response models for MCP tools:
   - ModelListResponse: paginated model listings
   - ModelDetailResponse: comprehensive model information
   - DatasetMappingResponse: warehouse-agnostic dataset organization
   - SearchResultResponse: ranked search results with relevance
   - LineageResponse: basic model dependencies

4. Generic helper methods:
   - Model.get_test_columns()
   - Model.get_documented_columns()
   - ModelRegistry.search(query, filters)
   - ModelRegistry.get_by_tag(tag)
   - ModelRegistry.get_by_materialization(type)

5. Support for common dbt patterns:
   - Staging/intermediate/marts organization
   - Multiple schema configurations
   - Tag-based organization
   - Documentation and meta fields
   - Custom materializations

Make this work with BigQuery, Snowflake, Postgres, etc. - no warehouse-specific assumptions."
```

## Step 3: Universal dbt Parser

Create parsing logic that works with any dbt project:

```bash
claude-code "Implement dbt_parser.py with universal dbt parsing capabilities:

1. Project parser (works with any dbt_project.yml):
   - parse_dbt_project(yaml_content: str) -> DbtProject
   - Extract model configurations from any hierarchy
   - Parse vars, seeds, tests, snapshots configurations
   - Handle different schema naming patterns
   - Support custom materializations and configs
   - Extract warehouse-agnostic dataset mappings

2. Schema parser (works with any schema.yml structure):
   - parse_schema_file(yaml_content: str) -> List[DbtModel]
   - Parse models, sources, exposures, metrics
   - Handle nested YAML structures and references
   - Extract all column metadata and constraints
   - Parse all test types (generic, singular, custom)
   - Support meta fields and documentation

3. Universal model registry:
   - build_model_registry(project: DbtProject, models: List[DbtModel]) -> ModelRegistry
   - Create searchable index across all metadata
   - Group by tags, schemas, materializations
   - Build basic dependency tracking from refs/sources

4. Generic search functionality:
   - search_models(query: str, filters: Dict) -> List[DbtModel]
   - Search names, descriptions, columns, tags, meta
   - Filter by materialization, schema, tags
   - Rank by relevance and metadata completeness
   - Support fuzzy matching and stemming

5. Lineage extraction:
   - extract_basic_lineage(models: List[DbtModel]) -> Dict[str, List[str]]
   - Parse ref() and source() calls from model SQL (if provided)
   - Build dependency graph from YAML metadata
   - Identify model layers (staging -> intermediate -> marts)

6. Handle common dbt patterns:
   - Multiple schema.yml files per folder
   - Nested folder structures
   - Different naming conventions
   - Various test configurations
   - Custom meta and tag patterns

Make this completely generic - no assumptions about specific project structure or business domain."
```

## Step 4: Generic MCP Server Implementation

Implement the MCP server for any dbt project:

```bash
claude-code "Implement server.py using the MCP Python SDK for universal dbt processing:

1. MCP tools (use @list_tools and @call_tool decorators):

   - parse_dbt_project:
     * Input: dbt_project_yml_content (string)
     * Output: Project metadata with model configurations and warehouse mappings
     * Description: Parse any dbt_project.yml file to understand project structure

   - parse_dbt_schema:
     * Input: schema_yml_content (string), project_context (optional JSON)
     * Output: List of models, sources, and exposures with metadata
     * Description: Parse any dbt schema.yml file to extract model definitions

   - get_model_info:
     * Input: model_name (string)
     * Output: Comprehensive model details including columns, tests, config
     * Description: Get detailed information about any dbt model

   - search_models:
     * Input: query (string), filters (optional JSON)
     * Output: Ranked search results across all metadata
     * Description: Search models by name, description, columns, tags, or meta

   - list_datasets:
     * Input: warehouse_type (optional: 'bigquery', 'snowflake', 'postgres')
     * Output: Dataset/schema mappings organized by warehouse patterns
     * Description: Show how models map to warehouse datasets/schemas

   - get_model_lineage:
     * Input: model_name (string), depth (optional int)
     * Output: Upstream and downstream dependencies
     * Description: Extract basic lineage relationships for a model

   - list_model_tags:
     * Input: None
     * Output: All tags used across models with counts
     * Description: Discover organizational patterns via tags

   - get_models_by_materialization:
     * Input: materialization_type (string)
     * Output: All models using specified materialization
     * Description: Find tables, views, incremental models, etc.

2. Server features:
   - Completely stateless design
   - Fast in-memory processing of any dbt structure
   - Rich error messages with helpful parsing guidance
   - Support for incremental parsing (multiple schema files)
   - Warehouse-agnostic responses
   - Extensible for custom dbt patterns

3. Response formatting optimized for analysis workflows with any data warehouse"
```

## Step 5: Simple Caching Layer

Add lightweight caching for any dbt project:

```bash
claude-code "Implement cache.py with generic in-memory caching:

1. Universal cache design:
   - LRU cache for any parsed dbt content
   - Content-hash based cache keys (works with any file)
   - Configurable size and TTL
   - Thread-safe operations

2. Cache methods:
   - get_cached_result(content_hash: str) -> Optional[Any]
   - set_cached_result(content_hash: str, result: Any, ttl: int)
   - clear_cache() -> None
   - get_cache_stats() -> Dict[str, Any]
   - invalidate_pattern(pattern: str) -> int

3. Cache integration:
   - SHA-256 hashing of file contents
   - Cache parsed ModelRegistry objects
   - Cache search indices for performance
   - Optional cache warming strategies

4. Memory management:
   - Configurable memory limits
   - Automatic cleanup of stale entries
   - Cache hit/miss statistics
   - Performance monitoring

Keep it simple and generic - works with any dbt project size."
```

## Step 6: Docker Setup for Any Environment

Create portable Docker configuration:

```bash
claude-code "Create Docker setup that works in any environment:

1. Dockerfile:
   - python:3.11-slim base image
   - Multi-stage build for smaller image
   - Install requirements with proper caching
   - Non-root user for security
   - Health check endpoint
   - Support for stdio MCP transport

2. docker-compose.yml:
   - Simple service definition
   - Environment variable configuration
   - Optional cache volume
   - Resource limits
   - Restart policies
   - Logging configuration

3. .env.example:
   # Cache configuration
   CACHE_SIZE=1000
   CACHE_TTL_MINUTES=60
   
   # Server configuration
   LOG_LEVEL=INFO
   MCP_SERVER_NAME=dbt-core-mcp
   
   # Optional performance tuning
   MAX_MEMORY_MB=512
   ENABLE_CACHE_WARMING=false

4. Include docker-compose.override.yml for development

Make this work in any Docker environment - no external dependencies."
```

## Step 7: Comprehensive Documentation

Document the universal MCP server:

```bash
claude-code "Create comprehensive README.md for the open-source project:

1. Project overview:
   - What dbt-core-mcp does
   - Supported dbt features and patterns
   - Warehouse compatibility (BigQuery, Snowflake, Postgres, etc.)
   - Integration with other MCP servers

2. Quick start guide:
   - Installation options (Docker, pip, source)
   - Basic configuration
   - Claude Desktop integration
   - First analysis workflow

3. Supported dbt patterns:
   - Standard project structures (staging/intermediate/marts)
   - Multiple schema files
   - Custom materializations
   - Tag-based organization
   - Documentation and meta fields
   - Tests and constraints

4. Example workflows:
   ```
   User: \"Get the dbt_project.yml from [any-repo]\"
   → GitHub MCP fetches project file
   
   User: \"Parse this dbt project and show me the model structure\"
   → dbt-core-mcp parses and returns organized model info
   
   User: \"Search for models related to 'user' or 'customer'\"
   → dbt-core-mcp searches across all metadata
   
   User: \"Query the user_dim table with proper column context\"
   → BigQuery/Snowflake MCP uses dbt metadata for context
   ```

5. API reference:
   - Complete tool documentation
   - Input/output schemas
   - Error handling
   - Performance considerations

6. Contributing guide:
   - Development setup
   - Testing approach
   - Code standards
   - Feature request process

7. Deployment options:
   - Local development
   - Team deployment
   - CI/CD integration
   - Production considerations

Make this suitable for open-source distribution with clear examples."
```

## Step 8: Comprehensive Testing

Create tests that work with any dbt project:

```bash
claude-code "Create comprehensive test suite for generic dbt parsing:

1. tests/test_parser.py:
   - Test parsing various dbt_project.yml structures
   - Test different schema.yml patterns
   - Test multiple warehouse configurations
   - Test edge cases and malformed YAML
   - Test large project parsing performance

2. tests/test_models.py:
   - Test pydantic model validation
   - Test all supported dbt configurations
   - Test custom meta and tag patterns
   - Test different column constraint types
   - Test materialization configurations

3. tests/test_search.py:
   - Test search across different metadata types
   - Test filtering and ranking
   - Test fuzzy matching
   - Test large dataset search performance
   - Test search with various dbt patterns

4. tests/test_cache.py:
   - Test caching with different content types
   - Test cache invalidation
   - Test memory management
   - Test concurrent access patterns

5. tests/fixtures/:
   - Sample dbt_project.yml files (BigQuery, Snowflake, Postgres patterns)
   - Sample schema.yml files with various structures
   - Sample model SQL files for lineage testing
   - Large project samples for performance testing

6. Integration tests:
   - End-to-end MCP tool testing
   - Multi-file parsing workflows
   - Error handling scenarios
   - Performance benchmarks

Make tests generic and comprehensive - cover various dbt project patterns."
```

## Step 9: Open Source Setup

Create open-source project infrastructure:

```bash
claude-code "Set up the project for open-source distribution:

1. LICENSE file (MIT recommended for broad adoption)

2. Contributing guidelines:
   - Code of conduct
   - Development setup
   - Pull request process
   - Issue templates
   - Testing requirements

3. GitHub Actions workflows:
   - CI/CD pipeline
   - Automated testing
   - Docker image building
   - Release automation
   - Documentation building

4. Package configuration:
   - pyproject.toml for modern Python packaging
   - setup.py for backward compatibility
   - Version management
   - Entry points for CLI usage

5. Documentation site setup:
   - GitHub Pages or similar
   - API documentation generation
   - Example gallery
   - Integration guides

6. Release strategy:
   - Semantic versioning
   - Changelog generation
   - Release notes
   - Migration guides

Prepare for community contributions and adoption."
```

## Step 10: Main Entry Point

Create the universal server entry point:

```bash
claude-code "Create main.py that works with any dbt project:

1. Initialize MCP server using Python SDK
2. Register all universal dbt parsing tools
3. Set up configurable logging
4. Support multiple transport modes (stdio, HTTP)
5. Graceful shutdown and cleanup
6. Health monitoring and metrics
7. Configuration validation
8. Error recovery and reporting

Include CLI options for:
- Configuration file path
- Log level override
- Cache settings
- Development mode
- Version information

Make it production-ready and user-friendly."
```

## Installation and Usage

Once built, users can integrate dbt-core-mcp with:

```bash
# Docker (recommended)
docker run -d --name dbt-core-mcp ghcr.io/your-org/dbt-core-mcp

# Or local installation
pip install dbt-core-mcp
dbt-core-mcp

# Claude Desktop configuration
{
  "mcpServers": {
    "dbt-core-mcp": {
      "command": "docker",
      "args": ["run", "--rm", "--name", "dbt-core-mcp", "ghcr.io/your-org/dbt-core-mcp"]
    }
  }
}
```

## Universal Workflow

The generic workflow works with any dbt project:

```
1. User: "Get the dbt project file from [any-dbt-repo]"
   → GitHub MCP fetches dbt_project.yml

2. User: "Parse this dbt project and show me the model organization"
   → dbt-core-mcp analyzes structure and returns organized view

3. User: "Get schema files for the marts models"
   → GitHub MCP fetches relevant schema.yml files

4. User: "Parse these schemas and find models with customer data"
   → dbt-core-mcp searches and returns relevant models

5. User: "Query the customer_summary table using the column context"
   → Warehouse MCP uses dbt metadata for intelligent querying
```

## Key Benefits

1. **Universal compatibility**: Works with any dbt project structure
2. **Warehouse agnostic**: Supports BigQuery, Snowflake, Postgres, etc.
3. **Open source ready**: Generic, well-documented, community-friendly
4. **Performance optimized**: Caching and efficient parsing
5. **Extensible**: Easy to add new dbt features and patterns
6. **Production ready**: Comprehensive testing and monitoring

This creates a robust, generic MCP server that can become a standard tool for dbt + Claude integration across the community.
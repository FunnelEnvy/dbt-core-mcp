"""
FastMCP-based dbt context provider server.
Provides rich database structure context from dbt projects to LLMs.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path

from fastmcp import FastMCP, Context
from github import Github, GithubException
import yaml

from src.dbt_parser import DbtParser
from src.models import (
    DbtProject, ModelRegistry, DbtModel,
    SearchResultResponse, LineageResponse
)
from src.cache import get_cache_manager

logger = logging.getLogger(__name__)

# Initialize FastMCP application
mcp = FastMCP(name="dbt-context-provider")

# Global state
registry: Optional[ModelRegistry] = None
github_client: Optional[Github] = None
repository_name: Optional[str] = None
schema_patterns: List[str] = []
project_path: str = "dbt_project.yml"
profiles_path: str = "profiles.yml"
target_name: Optional[str] = None
last_sync: Optional[datetime] = None
cache_manager = get_cache_manager()


def initialize_github():
    """Initialize GitHub client with PAT."""
    global github_client, repository_name, schema_patterns, project_path, profiles_path, target_name
    
    token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not token:
        raise ValueError("GITHUB_PERSONAL_ACCESS_TOKEN environment variable is required")
    
    repo = os.getenv("GITHUB_REPOSITORY")
    if not repo:
        raise ValueError("GITHUB_REPOSITORY environment variable is required")
    
    schema_patterns = os.getenv("DBT_SCHEMA_PATTERNS", "models/**/*.yml").split(",")
    project_path = os.getenv("DBT_PROJECT_PATH", "dbt_project.yml")
    profiles_path = os.getenv("DBT_PROFILES_PATH", "profiles.yml")
    target_name = os.getenv("DBT_TARGET", "prod")  # Default to prod target
    
    github_client = Github(token)
    repository_name = repo
    
    logger.info(f"Initialized GitHub client for repository: {repository_name}")
    logger.info(f"Schema patterns: {schema_patterns}")
    logger.info(f"Project path: {project_path}")
    logger.info(f"Profiles path: {profiles_path}")
    logger.info(f"Target: {target_name}")
    
    # Check for schema override
    schema_override = os.getenv("DBT_SCHEMA_OVERRIDE")
    if schema_override:
        logger.info(f"Schema override: {schema_override}")


async def fetch_from_github(path: str) -> Optional[str]:
    """Fetch a file from GitHub repository."""
    if not github_client or not repository_name:
        raise ValueError("GitHub client not initialized")
    
    try:
        repo = github_client.get_repo(repository_name)
        file_content = repo.get_contents(path)
        
        if isinstance(file_content, list):
            # Directory, not a file
            return None
        
        return file_content.decoded_content.decode('utf-8')
    except GithubException as e:
        logger.error(f"Error fetching {path} from GitHub: {e}")
        return None


async def fetch_files_matching_patterns() -> Dict[str, str]:
    """Fetch all files matching the configured patterns."""
    if not github_client or not repository_name:
        raise ValueError("GitHub client not initialized")
    
    files = {}
    repo = github_client.get_repo(repository_name)
    
    for pattern in schema_patterns:
        # Convert glob pattern to GitHub search
        if "**" in pattern:
            # Recursive search
            base_path = pattern.split("**")[0].rstrip("/")
            extension = pattern.split(".")[-1] if "." in pattern else "yml"
            
            try:
                contents = repo.get_contents(base_path)
                files_to_check = []
                
                while contents:
                    file_content = contents.pop(0)
                    if file_content.type == "dir":
                        contents.extend(repo.get_contents(file_content.path))
                    elif file_content.path.endswith(f".{extension}"):
                        files_to_check.append(file_content.path)
                
                for file_path in files_to_check:
                    content = await fetch_from_github(file_path)
                    if content:
                        files[file_path] = content
                        
            except GithubException as e:
                logger.error(f"Error searching for pattern {pattern}: {e}")
                
        elif "*" in pattern:
            # Single directory wildcard
            base_path = pattern.rsplit("/", 1)[0] if "/" in pattern else ""
            
            try:
                contents = repo.get_contents(base_path)
                for file_content in contents:
                    if file_content.type == "file" and file_content.path.endswith(".yml"):
                        content = await fetch_from_github(file_content.path)
                        if content:
                            files[file_content.path] = content
            except GithubException as e:
                logger.error(f"Error searching for pattern {pattern}: {e}")
        else:
            # Specific file
            content = await fetch_from_github(pattern)
            if content:
                files[pattern] = content
    
    return files


async def sync_from_github() -> bool:
    """Sync dbt metadata from GitHub."""
    global registry, last_sync
    
    logger.info("Starting sync from GitHub...")
    
    try:
        # Fetch dbt_project.yml
        project_content = await fetch_from_github(project_path)
        if not project_content:
            logger.error(f"Could not fetch {project_path}")
            return False
        
        # Parse project
        project = DbtParser.parse_dbt_project(project_content)
        
        # Fetch and parse profiles.yml if available
        profile_config = None
        profiles_content = await fetch_from_github(profiles_path)
        if profiles_content:
            try:
                profiles_data = yaml.safe_load(profiles_content)
                if project.config.profile and project.config.profile in profiles_data:
                    profile_data = profiles_data[project.config.profile]
                    if 'outputs' in profile_data and target_name in profile_data['outputs']:
                        profile_config = profile_data['outputs'][target_name]
                        logger.info(f"Loaded profile config for target '{target_name}': {profile_config.get('type', 'unknown')} database")
            except Exception as e:
                logger.warning(f"Failed to parse profiles.yml: {e}")
        
        # Fetch schema files
        schema_files = await fetch_files_matching_patterns()
        logger.info(f"Fetched {len(schema_files)} schema files")
        
        # Parse all schemas and build registry
        all_models = []
        all_sources = []
        all_exposures = []
        all_metrics = []
        
        for file_path, content in schema_files.items():
            try:
                parsed = DbtParser.parse_schema_file(content, {"models": project.config.models})
                all_models.extend(parsed.get("models", []))
                all_sources.extend(parsed.get("sources", []))
                all_exposures.extend(parsed.get("exposures", []))
                all_metrics.extend(parsed.get("metrics", []))
                logger.info(f"Parsed {file_path}: {len(parsed.get('models', []))} models")
            except Exception as e:
                logger.error(f"Error parsing {file_path}: {e}")
        
        # Update project with all parsed data
        project.models = all_models
        project.sources = all_sources
        project.exposures = all_exposures
        project.metrics = all_metrics
        
        # Build registry
        registry = DbtParser.build_model_registry(project)
        
        # Store profile config in registry for later use
        if profile_config:
            registry.profile_config = profile_config
        
        last_sync = datetime.now()
        
        logger.info(f"Sync complete. Loaded {len(all_models)} models")
        return True
        
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return False


def should_refresh() -> bool:
    """Check if cache should be refreshed."""
    if not last_sync:
        return True
    
    ttl_minutes = int(os.getenv("CACHE_TTL_MINUTES", "60"))
    return datetime.now() - last_sync > timedelta(minutes=ttl_minutes)


async def ensure_fresh_context():
    """Ensure context is fresh, syncing if needed."""
    global registry
    
    # First-time sync or refresh needed
    if not registry or should_refresh():
        success = await sync_from_github()
        if not success and not registry:
            # If initial sync fails and we have no data, raise error
            raise Exception("Failed to sync from GitHub. Please check your configuration.")


# ============= FastMCP Tools =============

@mcp.tool()
async def get_database_context(ctx: Context) -> str:
    """
    ALWAYS use this FIRST before writing any SQL queries.
    Returns comprehensive database structure with business logic, constraints, and accepted values
    that are NOT available in database INFORMATION_SCHEMA.
    Includes column relationships, data quality rules, and test-validated values.
    """
    await ensure_fresh_context()
    
    if not registry:
        return "No dbt context available. Repository may not be properly configured."
    
    # Build comprehensive context
    context_parts = []
    
    # Project overview
    context_parts.append(f"# Database Context: {repository_name}\n")
    
    # Extract dataset configuration from profiles if available
    model_config = registry.project.config.models or {}
    dataset_info = None
    
    # First check for schema override
    schema_override = os.getenv("DBT_SCHEMA_OVERRIDE")
    if schema_override:
        dataset_info = schema_override
    # Otherwise get from profiles.yml parsing
    elif hasattr(registry, 'profile_config') and registry.profile_config:
        dataset_info = registry.profile_config.get('dataset') or registry.profile_config.get('database')
    
    # Otherwise look for dataset configuration in project
    elif 'marts' in model_config and isinstance(model_config['marts'], dict):
        marts_config = model_config['marts']
        if 'forecasting' in marts_config and isinstance(marts_config['forecasting'], dict):
            fc_config = marts_config['forecasting']
            if '+dataset' in fc_config:
                dataset_info = fc_config['+dataset']
            elif 'dataset' in fc_config:
                dataset_info = fc_config['dataset']
    
    if dataset_info:
        context_parts.append(f"**BigQuery Dataset**: `{dataset_info}`")
    
    context_parts.append(f"Total Models: {len(registry.project.models)}")
    context_parts.append(f"Total Sources: {len(registry.project.sources)}")
    
    # Group models by schema
    schemas = {}
    for model in registry.project.models:
        schema = model.config.schema or "default"
        if schema not in schemas:
            schemas[schema] = []
        schemas[schema].append(model)
    
    context_parts.append(f"\n## Schemas ({len(schemas)}):")
    for schema, models in schemas.items():
        context_parts.append(f"- {schema}: {len(models)} models")
    
    # List all models with basic info
    context_parts.append("\n## Models:")
    for model in registry.project.models[:50]:  # Limit to first 50 for context
        materialization = model.get_materialization()
        context_parts.append(
            f"- **{model.name}** ({materialization}): "
            f"{model.description[:100] if model.description else 'No description'}"
        )
        if model.columns:
            context_parts.append(f"  Columns: {', '.join([c.name for c in model.columns[:10]])}")
    
    # Tags overview
    if registry.tag_index:
        context_parts.append(f"\n## Tags: {', '.join(registry.tag_index.keys())}")
    
    return "\n".join(context_parts)


@mcp.tool()
async def get_model_context(ctx: Context, model_name: str) -> str:
    """
    REQUIRED before querying this table - provides critical column details.
    Returns column types, constraints, accepted values (from tests), relationships,
    and business logic NOT available in database metadata.
    Skipping this step will result in incorrect queries.
    
    Args:
        model_name: Name of the dbt model to get context for
    """
    await ensure_fresh_context()
    
    if not registry:
        return "No dbt context available. Repository may not be properly configured."
    
    model = registry.model_index.get(model_name.lower())
    if not model:
        return f"Model '{model_name}' not found. Use search_models to find available models."
    
    context_parts = []
    
    # Model header
    context_parts.append(f"# Model: {model.name}")
    if model.description:
        context_parts.append(f"\n{model.description}")
    
    # Configuration - Extract dataset from profiles and project config
    model_config = registry.project.config.models or {}
    
    # Get dataset/database from profile config if available
    dataset = None
    schema = model.config.schema or 'default'
    
    # First check for schema override environment variable
    schema_override = os.getenv("DBT_SCHEMA_OVERRIDE")
    if schema_override:
        dataset = schema_override
    elif hasattr(registry, 'profile_config') and registry.profile_config:
        # Different databases use different terms
        dataset = registry.profile_config.get('dataset')  # BigQuery
        if not dataset:
            dataset = registry.profile_config.get('database')  # Postgres/Redshift/Snowflake
        if not dataset:
            dataset = registry.profile_config.get('schema')  # Some configs
    
    # Override with model-specific database if set (unless schema override is active)
    if not schema_override and model.config.database:
        dataset = model.config.database
    
    # Check for dataset in various locations in project config if still not found
    elif not dataset and model_config:
        # Check for forecasting specific config
        if 'forecasting' in model_config:
            forecasting_config = model_config['forecasting']
            if isinstance(forecasting_config, dict):
                if '+dataset' in forecasting_config:
                    dataset = forecasting_config['+dataset']
                elif 'dataset' in forecasting_config:
                    dataset = forecasting_config['dataset']
        
        # Check for marts specific config
        if 'marts' in model_config:
            marts_config = model_config['marts']
            if isinstance(marts_config, dict):
                if '+dataset' in marts_config:
                    dataset = marts_config['+dataset']
                elif 'dataset' in marts_config:
                    dataset = marts_config['dataset']
                # Check for forecasting within marts
                if 'forecasting' in marts_config:
                    fc_config = marts_config['forecasting']
                    if isinstance(fc_config, dict):
                        if '+dataset' in fc_config:
                            dataset = fc_config['+dataset']
                        elif 'dataset' in fc_config:
                            dataset = fc_config['dataset']
    
    context_parts.append(f"\n## Configuration:")
    context_parts.append(f"- Materialization: {model.get_materialization()}")
    context_parts.append(f"- Schema: {schema}")
    
    # Provide full table path based on database type
    if dataset:
        # Determine database type from profile
        db_type = "database"
        if hasattr(registry, 'profile_config') and registry.profile_config:
            profile_type = registry.profile_config.get('type', '').lower()
            if profile_type == 'bigquery':
                db_type = "Dataset"
                context_parts.append(f"- Dataset: {dataset}")
                context_parts.append(f"- Full Table Path: `{dataset}.{schema}.{model.name}`")
            elif profile_type in ['postgres', 'redshift', 'snowflake']:
                db_type = "Database"
                context_parts.append(f"- Database: {dataset}")
                context_parts.append(f"- Full Table Path: `{dataset}.{schema}.{model.name}`")
            else:
                context_parts.append(f"- Database/Dataset: {dataset}")
                context_parts.append(f"- Full Table Path: `{dataset}.{schema}.{model.name}`")
        else:
            context_parts.append(f"- Database/Dataset: {dataset}")
            context_parts.append(f"- Full Table Path: `{dataset}.{schema}.{model.name}`")
    else:
        context_parts.append(f"- Full Table Path: {model.get_full_name()}")
    
    # Tags
    all_tags = list(set(model.tags + model.config.tags))
    if all_tags:
        context_parts.append(f"- Tags: {', '.join(all_tags)}")
    
    # Columns
    if model.columns:
        context_parts.append(f"\n## Columns ({len(model.columns)}):")
        for col in model.columns:
            col_info = f"- **{col.name}**"
            if col.data_type:
                col_info += f" ({col.data_type})"
            if col.description:
                col_info += f": {col.description}"
            context_parts.append(col_info)
            
            # Column tests
            if col.tests:
                test_names = [t.name for t in col.tests]
                context_parts.append(f"  Tests: {', '.join(test_names)}")
            
            # Column constraints
            if col.constraints:
                context_parts.append(f"  Constraints: {', '.join(col.constraints)}")
    
    # Model-level tests
    if model.tests:
        context_parts.append(f"\n## Model Tests:")
        for test in model.tests:
            context_parts.append(f"- {test.name} (severity: {test.severity})")
    
    # Dependencies
    if model.refs or model.sources:
        context_parts.append(f"\n## Dependencies:")
        if model.refs:
            context_parts.append(f"- References: {', '.join(model.refs)}")
        if model.sources:
            context_parts.append(f"- Sources: {', '.join(model.sources)}")
    
    return "\n".join(context_parts)


@mcp.tool()
async def search_models(
    ctx: Context,
    query: str,
    filter_schema: Optional[str] = None,
    filter_tags: Optional[List[str]] = None,
    filter_materialization: Optional[str] = None
) -> str:
    """
    Use this FIRST to find tables before writing SQL queries.
    Searches model names, descriptions, columns, and tags to identify relevant tables.
    Always search for models before attempting to query them directly.
    
    Args:
        query: Search term to look for in model names, descriptions, columns
        filter_schema: Optional schema name to filter results
        filter_tags: Optional list of tags to filter by
        filter_materialization: Optional materialization type (table, view, incremental)
    """
    await ensure_fresh_context()
    
    if not registry:
        return "No dbt context available. Repository may not be properly configured."
    
    # Build filters dict
    filters = {}
    if filter_schema:
        filters["schema"] = filter_schema
    if filter_tags:
        filters["tags"] = filter_tags
    if filter_materialization:
        filters["materialization"] = filter_materialization
    
    # Search
    results = registry.search(query, filters)
    
    if not results:
        return f"No models found matching '{query}'"
    
    # Format results
    output = [f"Found {len(results)} models matching '{query}':\n"]
    
    for model in results[:20]:  # Limit to 20 results
        output.append(f"**{model.name}** ({model.get_materialization()})")
        if model.description:
            output.append(f"  {model.description[:100]}")
        if model.config.schema:
            output.append(f"  Schema: {model.config.schema}")
        
        # Show matching columns if any
        matching_cols = [
            col.name for col in model.columns 
            if query.lower() in col.name.lower() or 
            (col.description and query.lower() in col.description.lower())
        ]
        if matching_cols:
            output.append(f"  Matching columns: {', '.join(matching_cols[:5])}")
        
        output.append("")
    
    return "\n".join(output)


@mcp.tool()
async def get_model_lineage(ctx: Context, model_name: str, depth: int = 1) -> str:
    """
    Get upstream and downstream dependencies for a model.
    Helps understand data flow and impact analysis.
    
    Args:
        model_name: Name of the model to get lineage for
        depth: How many levels of dependencies to show (1-3)
    """
    await ensure_fresh_context()
    
    if not registry:
        return "No dbt context available. Repository may not be properly configured."
    
    model = registry.model_index.get(model_name.lower())
    if not model:
        return f"Model '{model_name}' not found."
    
    # Get lineage
    all_lineage = DbtParser.extract_basic_lineage(registry.project.models)
    model_lineage = all_lineage.get(model.name, {"upstream": [], "downstream": []})
    
    output = [f"# Lineage for {model.name}\n"]
    
    # Upstream dependencies
    if model_lineage["upstream"]:
        output.append(f"## Upstream Dependencies ({len(model_lineage['upstream'])}):")
        for dep in model_lineage["upstream"]:
            dep_model = registry.model_index.get(dep.lower())
            if dep_model:
                output.append(f"- {dep}: {dep_model.description[:50] if dep_model.description else 'No description'}")
            else:
                output.append(f"- {dep} (external/source)")
    else:
        output.append("## No upstream dependencies (source table)")
    
    # Downstream dependencies
    if model_lineage["downstream"]:
        output.append(f"\n## Downstream Dependencies ({len(model_lineage['downstream'])}):")
        for dep in model_lineage["downstream"]:
            dep_model = registry.model_index.get(dep.lower())
            if dep_model:
                output.append(f"- {dep}: {dep_model.description[:50] if dep_model.description else 'No description'}")
            else:
                output.append(f"- {dep}")
    else:
        output.append("\n## No downstream dependencies (terminal model)")
    
    return "\n".join(output)


@mcp.tool()
async def get_column_info(ctx: Context, model_name: str, column_name: str) -> str:
    """
    Get detailed information about a specific column including
    data type, constraints, tests, and documentation.
    
    Args:
        model_name: Name of the model containing the column
        column_name: Name of the column to get info for
    """
    await ensure_fresh_context()
    
    if not registry:
        return "No dbt context available. Repository may not be properly configured."
    
    model = registry.model_index.get(model_name.lower())
    if not model:
        return f"Model '{model_name}' not found."
    
    column = model.get_column_by_name(column_name)
    if not column:
        return f"Column '{column_name}' not found in model '{model_name}'."
    
    output = [f"# Column: {model_name}.{column.name}\n"]
    
    if column.description:
        output.append(f"{column.description}\n")
    
    output.append("## Properties:")
    if column.data_type:
        output.append(f"- Data Type: {column.data_type}")
    
    if column.constraints:
        output.append(f"- Constraints: {', '.join(column.constraints)}")
    
    if column.tests:
        output.append(f"\n## Tests ({len(column.tests)}):")
        for test in column.tests:
            output.append(f"- {test.name} (severity: {test.severity})")
            if test.kwargs:
                output.append(f"  Config: {json.dumps(test.kwargs, indent=2)}")
    
    if column.meta:
        output.append(f"\n## Metadata:")
        output.append(json.dumps(column.meta, indent=2))
    
    if column.tags:
        output.append(f"\n## Tags: {', '.join(column.tags)}")
    
    return "\n".join(output)


@mcp.tool()
async def refresh_context(ctx: Context) -> str:
    """
    Manually refresh the dbt context from GitHub.
    Forces a re-fetch of all configured schema files.
    """
    success = await sync_from_github()
    
    if success:
        model_count = len(registry.project.models) if registry else 0
        return f"Successfully refreshed context. Loaded {model_count} models from {repository_name}."
    else:
        return "Failed to refresh context. Check logs for details."


@mcp.tool()
async def list_available_models(ctx: Context, schema_filter: Optional[str] = None) -> str:
    """
    List all available models in the dbt project.
    
    Args:
        schema_filter: Optional schema name to filter models
    """
    await ensure_fresh_context()
    
    if not registry:
        return "No dbt context available. Repository may not be properly configured."
    
    models_by_schema = {}
    for model in registry.project.models:
        schema = model.config.schema or "default"
        if schema_filter and schema != schema_filter:
            continue
        if schema not in models_by_schema:
            models_by_schema[schema] = []
        models_by_schema[schema].append(model.name)
    
    if not models_by_schema:
        return f"No models found{f' in schema {schema_filter}' if schema_filter else ''}."
    
    output = [f"# Available Models ({sum(len(m) for m in models_by_schema.values())} total)\n"]
    
    for schema, models in sorted(models_by_schema.items()):
        output.append(f"## Schema: {schema} ({len(models)} models)")
        for model in sorted(models):
            output.append(f"- {model}")
        output.append("")
    
    return "\n".join(output)


# ============= FastMCP Prompts =============

@mcp.prompt()
async def database_overview(ctx: Context) -> str:
    """
    Get dbt schema context BEFORE executing SQL - provides table structures and column details.
    """
    await ensure_fresh_context()
    
    if not registry:
        return "No database context available."
    
    # Get dataset/database info from profile or override
    dataset_info = ""
    schema_override = os.getenv("DBT_SCHEMA_OVERRIDE")
    
    if schema_override:
        dataset_info = f"\nSchema Override: **{schema_override}** (using custom generate_schema_name)"
    elif hasattr(registry, 'profile_config') and registry.profile_config:
        profile_type = registry.profile_config.get('type', '').lower()
        if profile_type == 'bigquery':
            dataset = registry.profile_config.get('dataset')
            if dataset:
                dataset_info = f"\nBigQuery Dataset: **{dataset}**"
        elif profile_type in ['postgres', 'redshift', 'snowflake']:
            database = registry.profile_config.get('database')
            if database:
                dataset_info = f"\nDatabase: **{database}**"
    
    return f"""**CRITICAL: DBT SCHEMA CONTEXT - REQUIRED FIRST STEP**

Repository: {repository_name}{dataset_info}
Target: {target_name}

⚠️ **MANDATORY WORKFLOW - NEVER SKIP THESE STEPS:**
1. **SEARCH** - Use search_models() to find relevant tables
2. **UNDERSTAND** - Use get_model_context() for EACH table you'll query
3. **INSPECT** - Use get_column_info() for columns with business logic
4. **THEN EXECUTE** - Only after steps 1-3, write and run SQL

**WHY THIS IS REQUIRED:**
This MCP contains critical information NOT available in database INFORMATION_SCHEMA:
- ✅ Accepted column values (e.g., lifecycle_stage: forecast/override/actual)
- ✅ Business constraints (e.g., invoice_status: invoiced/staged/due/scheduled)
- ✅ Data quality rules from dbt tests
- ✅ Column relationships and dependencies
- ✅ Actual table locations with custom schema names

**SKIPPING THIS WILL CAUSE:**
- ❌ Incorrect filter conditions (unknown enum values)
- ❌ Missing business logic constraints
- ❌ Querying wrong schemas/datasets
- ❌ Invalid JOIN conditions

This project contains:
- {len(registry.project.models)} models with full documentation
- {len(registry.project.sources)} data sources
- {len(registry.schema_index)} schemas

**Example: Column Values from Tests**
Models often have columns with specific accepted values defined in tests:
- current_lifecycle_stage: ['forecast', 'override', 'actual']
- invoice_status: ['invoiced', 'staged', 'due', 'scheduled', 'orphaned']
These values are ONLY discoverable through this MCP, not INFORMATION_SCHEMA.

After understanding the schema here, use the appropriate SQL execution MCP.
"""


@mcp.prompt()
async def sql_helper(ctx: Context, query_intent: str) -> str:
    """
    Get database context relevant to a specific SQL query intent.
    MUST be used before writing SQL to understand business logic and constraints.
    
    Args:
        query_intent: Description of what the SQL query should accomplish
    """
    await ensure_fresh_context()
    
    if not registry:
        return "No database context available."
    
    # Search for relevant models based on intent
    search_terms = query_intent.lower().split()
    relevant_models = set()
    
    for term in search_terms:
        if len(term) > 3:  # Skip short words
            results = registry.search(term)
            for model in results[:5]:
                relevant_models.add(model.name)
    
    output = [f"# SQL Context for: {query_intent}\n"]
    output.append("⚠️ **REMEMBER: Never write SQL without first getting full model context!**\n")
    
    if relevant_models:
        output.append(f"## Potentially Relevant Models:")
        for model_name in relevant_models:
            model = registry.model_index.get(model_name.lower())
            if model:
                output.append(f"\n### {model.name}")
                output.append(f"Full name: {model.get_full_name()}")
                if model.description:
                    output.append(f"Description: {model.description[:100]}")
                if model.columns:
                    col_names = [c.name for c in model.columns[:10]]
                    output.append(f"Key columns: {', '.join(col_names)}")
                output.append("**NEXT STEP**: Call get_model_context('" + model.name + "') for full details")
    else:
        output.append("No directly relevant models found. Use search_models() to explore available tables.")
    
    output.append("\n## REQUIRED WORKFLOW:")
    output.append("1. ✅ Use search_models() to find tables")
    output.append("2. ✅ Use get_model_context() for FULL column details including:")
    output.append("   - Accepted values for enum columns")
    output.append("   - Business constraints from tests")
    output.append("   - Data types and relationships")
    output.append("3. ✅ Use get_column_info() for specific column constraints")
    output.append("4. ✅ ONLY THEN write your SQL query")
    output.append("\n**WARNING**: Database INFORMATION_SCHEMA lacks business logic - you MUST use this MCP!")
    
    return "\n".join(output)


# ============= Startup =============
# Note: FastMCP doesn't have startup/shutdown decorators
# Initialize synchronously on module import

try:
    initialize_github()
    logger.info("GitHub client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize GitHub client: {e}")
    # Continue anyway - tools will handle the error


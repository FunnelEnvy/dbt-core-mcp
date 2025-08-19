# Migration Guide: Standard MCP to FastMCP

This guide explains the changes from the original MCP implementation to the new FastMCP-based dbt-context-provider.

## Key Changes

### 1. **Purpose Shift**
- **Before**: Universal dbt parser accepting any YAML content
- **After**: Repository-specific context provider that auto-syncs with GitHub

### 2. **Architecture**
- **Before**: Standard MCP SDK with manual tool definitions
- **After**: FastMCP with decorators and built-in GitHub integration

### 3. **Configuration**
- **Before**: Optional configuration, works without setup
- **After**: Requires GitHub PAT and repository configuration

## Migration Steps

### Step 1: Update Dependencies

```bash
# Install new requirements
pip install -r requirements.txt
```

New dependencies:
- `fastmcp` - Simplified MCP framework
- `PyGithub` - GitHub API integration
- `httpx` - HTTP client
- `tenacity` - Retry logic

### Step 2: Configure Environment

Create or update your `.env` file:

```bash
# Required (new)
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_your_token_here
GITHUB_REPOSITORY=YourOrg/your-dbt-repo

# Required (updated)
DBT_SCHEMA_PATTERNS=models/**/*.yml  # Now uses glob patterns

# Optional
DBT_PROJECT_PATH=dbt_project.yml
CACHE_TTL_MINUTES=60
LOG_LEVEL=INFO
```

### Step 3: Update Claude Desktop Configuration

**Old Configuration:**
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

**New Configuration:**
```json
{
  "mcpServers": {
    "dbt-context": {
      "command": "python",
      "args": ["/path/to/dbt-core-mcp/main_fastmcp.py"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token",
        "GITHUB_REPOSITORY": "YourOrg/your-dbt-repo",
        "DBT_SCHEMA_PATTERNS": "models/**/*.yml"
      }
    }
  }
}
```

### Step 4: Test the Migration

Run the test script to verify everything works:

```bash
python test_fastmcp.py
```

## Tool Mapping

### Tools Removed
- `parse_dbt_project` - Now automatic on startup
- `parse_dbt_schema` - Now automatic on startup
- `get_models_by_materialization` - Use `search_models` with filter
- `list_model_tags` - Information included in `get_database_context`

### Tools Added/Enhanced
- `get_database_context()` - Comprehensive overview (auto-refreshes)
- `refresh_context()` - Manual sync trigger
- `list_available_models()` - Simple model listing

### Tools Updated
- `search_models()` - Now includes filtering options
- `get_model_context()` - Enhanced with more details
- `get_model_lineage()` - Simplified interface

## Workflow Changes

### Before: Manual Parsing
```
1. User: "Get dbt_project.yml from GitHub"
2. GitHub MCP: Returns file content
3. User: "Parse this project file"
4. dbt-core-mcp: Parses and stores
5. User: "Get schema files"
6. GitHub MCP: Returns schema content
7. User: "Parse these schemas"
8. dbt-core-mcp: Parses and stores
```

### After: Automatic Sync
```
1. Server starts and auto-fetches from GitHub
2. User: "Show me customer models"
3. dbt-context-provider: Returns fresh context (auto-refreshed if needed)
```

## Benefits of Migration

1. **Always Fresh**: Automatic sync ensures latest schema
2. **Simpler Setup**: One-time configuration
3. **Better Performance**: Smart caching with TTL
4. **Cleaner Code**: FastMCP decorators reduce boilerplate
5. **Focused Purpose**: Clear role as context provider

## Running Both Versions

You can run both versions simultaneously with different names:

```json
{
  "mcpServers": {
    "dbt-classic": {
      "command": "python",
      "args": ["/path/to/dbt-core-mcp/main.py"]
    },
    "dbt-context": {
      "command": "python",
      "args": ["/path/to/dbt-core-mcp/main_fastmcp.py"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_token",
        "GITHUB_REPOSITORY": "YourOrg/repo",
        "DBT_SCHEMA_PATTERNS": "models/**/*.yml"
      }
    }
  }
}
```

## Troubleshooting

### Issue: "No models loaded"
- Check `GITHUB_REPOSITORY` format: `Owner/RepoName`
- Verify `DBT_SCHEMA_PATTERNS` matches actual file paths
- Test GitHub token: `curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user`

### Issue: "Authentication failed"
- Ensure PAT has repository read permissions
- Check token hasn't expired
- Verify repository is accessible

### Issue: "Pattern not matching files"
- Start with simple pattern: `models/`
- Use test script to see what's being fetched
- Check GitHub repository structure

## Rollback Plan

If you need to revert to the original version:

1. Use the original `main.py` entry point
2. Remove GitHub configuration from environment
3. Update Claude Desktop config to original setup
4. Original server still works with manual parsing

## Questions?

- Check `test_fastmcp.py` for examples
- See `README_FASTMCP.md` for detailed documentation
- Open an issue on GitHub for support
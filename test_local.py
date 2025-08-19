#!/usr/bin/env python3
"""
Local testing script for dbt-core-mcp server
Run this to test the MCP server functionality locally
"""

import asyncio
import json
from src.server import DbtMCPServer
from mcp.types import TextContent

# Sample dbt_project.yml content
SAMPLE_PROJECT_YML = """
name: 'test_analytics'
version: '1.0.0'
profile: 'test_profile'

model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["data"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]

target-path: "target"
clean-targets:
  - "target"
  - "dbt_packages"

models:
  test_analytics:
    +materialized: view
    staging:
      +materialized: view
      +schema: staging
    marts:
      +materialized: table
      +schema: marts

vars:
  start_date: '2020-01-01'
  warehouse_type: 'bigquery'
"""

# Sample schema.yml content
SAMPLE_SCHEMA_YML = """
version: 2

models:
  - name: customers
    description: "Customer dimension table"
    config:
      materialized: table
      schema: marts
    columns:
      - name: customer_id
        description: "Primary key"
        tests:
          - unique
          - not_null
      - name: customer_name
        description: "Customer full name"
      - name: created_at
        description: "Account creation timestamp"
    tags: ["pii", "customer"]

  - name: orders
    description: "Order fact table"
    config:
      materialized: incremental
      unique_key: order_id
    columns:
      - name: order_id
        tests:
          - unique
          - not_null
      - name: customer_id
        tests:
          - not_null
      - name: order_date
      - name: total_amount
    tags: ["fact", "daily"]
"""

async def test_server():
    """Test the MCP server functionality"""
    print("🚀 Starting dbt-core-mcp local test\n")
    
    # Initialize server
    server = DbtMCPServer()
    print("✅ Server initialized\n")
    
    # Test 1: Parse dbt project
    print("Test 1: Parsing dbt_project.yml")
    print("-" * 50)
    result = await server._parse_dbt_project({
        "dbt_project_yml_content": SAMPLE_PROJECT_YML
    })
    if result and isinstance(result[0], TextContent):
        project_data = json.loads(result[0].text)
        print(f"Project name: {project_data['project_name']}")
        print(f"Inferred warehouse: {project_data['inferred_warehouse']}")
        print(f"Model paths: {project_data['model_paths']}")
        print(f"Variables: {project_data['vars']}")
    print()
    
    # Test 2: Parse schema file
    print("Test 2: Parsing schema.yml")
    print("-" * 50)
    result = await server._parse_dbt_schema({
        "schema_yml_content": SAMPLE_SCHEMA_YML
    })
    if result and isinstance(result[0], TextContent):
        schema_data = json.loads(result[0].text)
        print(f"Models parsed: {schema_data['models_parsed']}")
        print(f"Models:")
        for model in schema_data['models']:
            print(f"  - {model['name']}: {model['materialization']} "
                  f"({model['columns_count']} columns, tags: {model['tags']})")
    print()
    
    # Test 3: Get model info
    print("Test 3: Getting model info for 'customers'")
    print("-" * 50)
    result = await server._get_model_info({
        "model_name": "customers"
    })
    if result and isinstance(result[0], TextContent):
        model_data = json.loads(result[0].text)
        print(f"Model: {model_data['name']}")
        print(f"Description: {model_data['description']}")
        print(f"Materialization: {model_data['materialization']}")
        print(f"Schema: {model_data['schema']}")
        print(f"Tags: {model_data['tags']}")
        print(f"Columns:")
        for col in model_data['columns']:
            print(f"  - {col['name']}: {col.get('description', 'No description')}")
            if col['tests']:
                print(f"    Tests: {col['tests']}")
    print()
    
    # Test 4: Search models
    print("Test 4: Searching for 'customer' models")
    print("-" * 50)
    result = await server._search_models({
        "query": "customer"
    })
    if result and isinstance(result[0], TextContent):
        search_data = json.loads(result[0].text)
        print(f"Found {search_data['total_results']} results")
        for model in search_data['results']:
            print(f"  - {model['name']}: {model.get('description', '')[:50]}")
    print()
    
    # Test 5: List datasets
    print("Test 5: Listing datasets")
    print("-" * 50)
    result = await server._list_datasets({
        "warehouse_type": "bigquery"
    })
    if result and isinstance(result[0], TextContent):
        dataset_data = json.loads(result[0].text)
        print(f"Total models: {dataset_data['total_models']}")
        print(f"Datasets:")
        for dataset, info in dataset_data['datasets'].items():
            print(f"  - {dataset}: {info['count']} models")
            print(f"    Models: {', '.join(info['models'][:3])}")
    print()
    
    # Test 6: List model tags
    print("Test 6: Listing all tags")
    print("-" * 50)
    result = await server._list_model_tags({})
    if result and isinstance(result[0], TextContent):
        tags_data = json.loads(result[0].text)
        print(f"Total tags: {tags_data['total_tags']}")
        for tag_info in tags_data['tags']:
            print(f"  - {tag_info['tag']}: {tag_info['model_count']} models")
    print()
    
    # Test 7: Get models by materialization
    print("Test 7: Getting models by materialization")
    print("-" * 50)
    result = await server._get_models_by_materialization({
        "materialization_type": "table"
    })
    if result and isinstance(result[0], TextContent):
        mat_data = json.loads(result[0].text)
        print(f"Found {mat_data['model_count']} table models")
        for model in mat_data['models']:
            print(f"  - {model['name']} (schema: {model['schema']})")
    print()
    
    # Test 8: Get model lineage
    print("Test 8: Getting model lineage")
    print("-" * 50)
    result = await server._get_model_lineage({
        "model_name": "orders",
        "depth": 1
    })
    if result and isinstance(result[0], TextContent):
        lineage_data = json.loads(result[0].text)
        print(f"Model: {lineage_data['model']}")
        print(f"Upstream models: {lineage_data['upstream']}")
        print(f"Downstream models: {lineage_data['downstream']}")
    print()
    
    print("✅ All tests completed successfully!")

async def test_cache():
    """Test the caching functionality"""
    print("\n🔄 Testing cache functionality\n")
    print("-" * 50)
    
    from src.cache import get_cache_manager
    
    cache = get_cache_manager()
    
    # Test cache set and get
    cache.set_cached_result("test_key", {"data": "test_value"}, ttl=60)
    result = cache.get_cached_result("test_key")
    print(f"Cache set/get test: {'✅ Passed' if result and result['data'] == 'test_value' else '❌ Failed'}")
    
    # Test cache stats
    stats = cache.get_cache_stats()
    print(f"Cache stats: {stats}")
    
    # Clear cache
    cache.clear_cache()
    result_after_clear = cache.get_cached_result("test_key")
    print(f"Cache clear test: {'✅ Passed' if result_after_clear is None else '❌ Failed'}")

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════╗
║     dbt-core-mcp Local Test Suite       ║
╚══════════════════════════════════════════╝
    """)
    
    # Run the tests
    asyncio.run(test_server())
    asyncio.run(test_cache())
    
    print("\n🎉 Local testing complete!")
    print("\nNext steps:")
    print("1. Run unit tests: pytest")
    print("2. Test with Claude Desktop (see README)")
    print("3. Build Docker image: docker build -t dbt-core-mcp .")
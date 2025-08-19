#!/usr/bin/env python3
"""
Test script for FastMCP dbt-context-provider.
Tests the server functionality without needing Claude Desktop.
"""

import os
import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_local():
    """Test the FastMCP server locally."""
    print("🧪 Testing dbt-context-provider (FastMCP version)\n")
    print("=" * 60)
    
    # Check environment
    print("📋 Environment Check:")
    token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")
    patterns = os.getenv("DBT_SCHEMA_PATTERNS", "models/**/*.yml")
    
    if not token:
        print("❌ GITHUB_PERSONAL_ACCESS_TOKEN not set")
        print("   Please set this in your .env file")
        return
    else:
        print(f"✅ GitHub token: ...{token[-4:]}")
    
    if not repo:
        print("❌ GITHUB_REPOSITORY not set")
        print("   Please set this in your .env file")
        return
    else:
        print(f"✅ Repository: {repo}")
    
    print(f"✅ Schema patterns: {patterns}")
    print()
    
    # Import server components
    try:
        from src.server import (
            initialize_github,
            sync_from_github,
            registry,
            get_database_context,
            search_models,
            get_model_context
        )
        print("✅ Server modules imported successfully")
    except Exception as e:
        print(f"❌ Failed to import server modules: {e}")
        return
    
    print("\n" + "=" * 60)
    print("🔄 Initializing and syncing from GitHub...")
    
    # Initialize and sync
    try:
        initialize_github()
        print("✅ GitHub client initialized")
        
        success = await sync_from_github()
        if success:
            print(f"✅ Sync successful!")
            
            # Access the global registry
            from src.server import registry
            if registry:
                print(f"   Loaded {len(registry.project.models)} models")
                print(f"   Loaded {len(registry.project.sources)} sources")
            else:
                print("⚠️  Registry is empty after sync")
        else:
            print("❌ Sync failed - check your repository and patterns")
            return
            
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 60)
    print("🧪 Testing Tools:\n")
    
    # Mock context for testing
    class MockContext:
        pass
    
    ctx = MockContext()
    
    # Test 1: Get database context
    print("1️⃣  Testing get_database_context()...")
    try:
        result = await get_database_context(ctx)
        print("✅ Success!")
        print(f"   Preview: {result[:200]}...")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    print()
    
    # Test 2: Search models
    print("2️⃣  Testing search_models('customer')...")
    try:
        result = await search_models(ctx, "customer")
        print("✅ Success!")
        print(f"   Preview: {result[:200]}...")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    print()
    
    # Test 3: Get specific model (if any exist)
    if registry and registry.project.models:
        first_model = registry.project.models[0].name
        print(f"3️⃣  Testing get_model_context('{first_model}')...")
        try:
            result = await get_model_context(ctx, first_model)
            print("✅ Success!")
            print(f"   Preview: {result[:300]}...")
        except Exception as e:
            print(f"❌ Failed: {e}")
    else:
        print("3️⃣  Skipping get_model_context test (no models loaded)")
    
    print("\n" + "=" * 60)
    print("✨ Test complete!\n")
    
    if registry and registry.project.models:
        print("📊 Summary:")
        print(f"   - Models: {len(registry.project.models)}")
        print(f"   - Sources: {len(registry.project.sources)}")
        print(f"   - Schemas: {len(registry.schema_index)}")
        print(f"   - Tags: {len(registry.tag_index)}")
        
        print("\n📝 Sample models:")
        for model in registry.project.models[:5]:
            print(f"   - {model.name}: {model.description[:50] if model.description else 'No description'}...")
    else:
        print("⚠️  No models were loaded. Check your configuration:")
        print(f"   - Repository: {repo}")
        print(f"   - Patterns: {patterns}")
        print("   - Ensure the patterns match actual files in your repo")


if __name__ == "__main__":
    asyncio.run(test_local())
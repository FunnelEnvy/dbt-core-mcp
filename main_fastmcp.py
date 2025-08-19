#!/usr/bin/env python3
"""
Main entry point for FastMCP-based dbt context provider.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_environment():
    """Validate required environment variables."""
    required = [
        "GITHUB_PERSONAL_ACCESS_TOKEN",
        "GITHUB_REPOSITORY"
    ]
    
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        logger.error("Please set these in your .env file or environment")
        sys.exit(1)
    
    # Log configuration
    logger.info(f"Repository: {os.getenv('GITHUB_REPOSITORY')}")
    logger.info(f"Schema patterns: {os.getenv('DBT_SCHEMA_PATTERNS', 'models/**/*.yml')}")
    logger.info(f"Project path: {os.getenv('DBT_PROJECT_PATH', 'dbt_project.yml')}")
    logger.info(f"Cache TTL: {os.getenv('CACHE_TTL_MINUTES', '60')} minutes")


def main():
    """Main entry point."""
    logger.info("Starting dbt-context-provider MCP server...")
    
    # Validate environment
    validate_environment()
    
    # Import and run the FastMCP app
    from src.server_fastmcp import mcp
    
    # Run the FastMCP server
    mcp.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
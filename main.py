#!/usr/bin/env python3
import asyncio
import logging
import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
from src.server import DbtMCPServer
from src.cache import reset_global_cache

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="dbt-core-mcp: Universal MCP server for dbt project analysis"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=os.getenv("LOG_LEVEL", "INFO"),
        help="Set the logging level"
    )
    parser.add_argument(
        "--cache-size",
        type=int,
        default=int(os.getenv("CACHE_SIZE", "1000")),
        help="Maximum number of items to cache"
    )
    parser.add_argument(
        "--cache-ttl",
        type=int,
        default=int(os.getenv("CACHE_TTL_MINUTES", "60")),
        help="Cache TTL in minutes"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="dbt-core-mcp 1.0.0"
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Run in development mode with verbose logging"
    )
    
    return parser.parse_args()


async def main():
    args = parse_arguments()
    
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    if args.dev:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Running in development mode")
    
    logger.info(f"Starting dbt-core-mcp server")
    logger.info(f"Cache size: {args.cache_size}, TTL: {args.cache_ttl} minutes")
    
    try:
        server = DbtMCPServer()
        logger.info("Server initialized successfully")
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        reset_global_cache()
        logger.info("Server stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
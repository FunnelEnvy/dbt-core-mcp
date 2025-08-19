import json
import logging
from typing import Dict, List, Optional, Any
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent
from src.dbt_parser import DbtParser
from src.models import (
    DbtProject, ModelRegistry, ModelListResponse, ModelDetailResponse,
    DatasetMappingResponse, SearchResultResponse, LineageResponse,
    WarehouseType
)
from src.cache import get_cache_manager

logger = logging.getLogger(__name__)


class DbtMCPServer:
    def __init__(self):
        self.server = Server("dbt-core-mcp")
        self.cache_manager = get_cache_manager()
        self.current_registry: Optional[ModelRegistry] = None
        self._setup_handlers()

    def _setup_handlers(self):
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="parse_dbt_project",
                    description="Parse any dbt_project.yml file to understand project structure",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "dbt_project_yml_content": {
                                "type": "string",
                                "description": "The content of dbt_project.yml file"
                            }
                        },
                        "required": ["dbt_project_yml_content"]
                    }
                ),
                Tool(
                    name="parse_dbt_schema",
                    description="Parse any dbt schema.yml file to extract model definitions",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "schema_yml_content": {
                                "type": "string",
                                "description": "The content of schema.yml file"
                            },
                            "project_context": {
                                "type": "object",
                                "description": "Optional project configuration context",
                                "properties": {}
                            }
                        },
                        "required": ["schema_yml_content"]
                    }
                ),
                Tool(
                    name="get_model_info",
                    description="Get detailed information about any dbt model",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "model_name": {
                                "type": "string",
                                "description": "The name of the dbt model"
                            }
                        },
                        "required": ["model_name"]
                    }
                ),
                Tool(
                    name="search_models",
                    description="Search models by name, description, columns, tags, or meta",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query string"
                            },
                            "filters": {
                                "type": "object",
                                "description": "Optional filters",
                                "properties": {
                                    "tags": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Filter by tags"
                                    },
                                    "schema": {
                                        "type": "string",
                                        "description": "Filter by schema"
                                    },
                                    "materialization": {
                                        "type": "string",
                                        "description": "Filter by materialization type"
                                    }
                                }
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="list_datasets",
                    description="Show how models map to warehouse datasets/schemas",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "warehouse_type": {
                                "type": "string",
                                "description": "Warehouse type (bigquery, snowflake, postgres, etc.)",
                                "enum": ["bigquery", "snowflake", "postgres", "redshift", "databricks", "synapse", "duckdb"]
                            }
                        }
                    }
                ),
                Tool(
                    name="get_model_lineage",
                    description="Extract basic lineage relationships for a model",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "model_name": {
                                "type": "string",
                                "description": "The name of the model"
                            },
                            "depth": {
                                "type": "integer",
                                "description": "Depth of lineage to traverse",
                                "minimum": 1,
                                "maximum": 5,
                                "default": 1
                            }
                        },
                        "required": ["model_name"]
                    }
                ),
                Tool(
                    name="list_model_tags",
                    description="Discover organizational patterns via tags",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="get_models_by_materialization",
                    description="Find tables, views, incremental models, etc.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "materialization_type": {
                                "type": "string",
                                "description": "Type of materialization",
                                "enum": ["table", "view", "incremental", "ephemeral", "snapshot", "seed"]
                            }
                        },
                        "required": ["materialization_type"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            try:
                if name == "parse_dbt_project":
                    return await self._parse_dbt_project(arguments)
                elif name == "parse_dbt_schema":
                    return await self._parse_dbt_schema(arguments)
                elif name == "get_model_info":
                    return await self._get_model_info(arguments)
                elif name == "search_models":
                    return await self._search_models(arguments)
                elif name == "list_datasets":
                    return await self._list_datasets(arguments)
                elif name == "get_model_lineage":
                    return await self._get_model_lineage(arguments)
                elif name == "list_model_tags":
                    return await self._list_model_tags(arguments)
                elif name == "get_models_by_materialization":
                    return await self._get_models_by_materialization(arguments)
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _parse_dbt_project(self, arguments: Dict[str, Any]) -> List[TextContent]:
        yml_content = arguments.get("dbt_project_yml_content", "")
        
        cached_result = self.cache_manager.get_cached_yaml(yml_content, "project")
        if cached_result:
            project = cached_result
        else:
            project = DbtParser.parse_dbt_project(yml_content)
            self.cache_manager.cache_yaml_content(yml_content, project, "project")
        
        warehouse_type = DbtParser.infer_warehouse_type(project)
        
        result = {
            "project_name": project.config.name,
            "version": project.config.version,
            "profile": project.config.profile,
            "inferred_warehouse": warehouse_type.value if warehouse_type else None,
            "model_paths": project.config.model_paths,
            "vars": project.config.vars,
            "models_config": project.config.models,
            "model_count": len(project.models),
            "source_count": len(project.sources)
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _parse_dbt_schema(self, arguments: Dict[str, Any]) -> List[TextContent]:
        yml_content = arguments.get("schema_yml_content", "")
        project_context = arguments.get("project_context")
        
        cache_key = f"schema:{yml_content}:{json.dumps(project_context) if project_context else ''}"
        cached_result = self.cache_manager.get_cached_result(self.cache_manager.generate_cache_key(cache_key))
        
        if cached_result:
            parsed_data = cached_result
        else:
            parsed_data = DbtParser.parse_schema_file(yml_content, project_context)
            self.cache_manager.set_cached_result(
                self.cache_manager.generate_cache_key(cache_key),
                parsed_data
            )
        
        models = parsed_data.get("models", [])
        sources = parsed_data.get("sources", [])
        exposures = parsed_data.get("exposures", [])
        metrics = parsed_data.get("metrics", [])
        
        if self.current_registry and self.current_registry.project:
            self.current_registry.project.models.extend(models)
            self.current_registry.project.sources.extend(sources)
            self.current_registry.project.exposures.extend(exposures)
            self.current_registry.project.metrics.extend(metrics)
            self.current_registry.build_indices()
        else:
            project = DbtProject(
                config=project_context if project_context else {"name": "parsed_schema"},
                models=models,
                sources=sources,
                exposures=exposures,
                metrics=metrics
            )
            self.current_registry = DbtParser.build_model_registry(project)
        
        result = {
            "models_parsed": len(models),
            "sources_parsed": len(sources),
            "exposures_parsed": len(exposures),
            "metrics_parsed": len(metrics),
            "models": [
                {
                    "name": m.name,
                    "description": m.description,
                    "columns_count": len(m.columns),
                    "tests_count": len(m.tests),
                    "materialization": m.get_materialization(),
                    "tags": list(set(m.tags + m.config.tags))
                }
                for m in models[:10]
            ]
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _get_model_info(self, arguments: Dict[str, Any]) -> List[TextContent]:
        model_name = arguments.get("model_name", "")
        
        if not self.current_registry:
            return [TextContent(type="text", text="No models parsed yet. Please parse a dbt project or schema first.")]
        
        model = self.current_registry.model_index.get(model_name.lower())
        if not model:
            return [TextContent(type="text", text=f"Model '{model_name}' not found")]
        
        lineage = DbtParser.extract_basic_lineage([model])
        
        response = ModelDetailResponse(
            model=model,
            lineage=lineage.get(model.name),
            warehouse_location=model.get_full_name()
        )
        
        result = {
            "name": model.name,
            "description": model.description,
            "full_name": model.get_full_name(),
            "materialization": model.get_materialization(),
            "schema": model.config.schema,
            "database": model.config.database,
            "tags": list(set(model.tags + model.config.tags)),
            "columns": [
                {
                    "name": col.name,
                    "description": col.description,
                    "data_type": col.data_type,
                    "tests": [t.name for t in col.tests]
                }
                for col in model.columns
            ],
            "tests": [t.name for t in model.tests],
            "documented_columns": model.get_documented_columns(),
            "tested_columns": model.get_test_columns(),
            "lineage": response.lineage
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _search_models(self, arguments: Dict[str, Any]) -> List[TextContent]:
        query = arguments.get("query", "")
        filters = arguments.get("filters")
        
        if not self.current_registry:
            return [TextContent(type="text", text="No models parsed yet. Please parse a dbt project or schema first.")]
        
        results = self.current_registry.search(query, filters)
        
        response = SearchResultResponse(
            results=results[:20],
            query=query,
            filters=filters or {},
            total_results=len(results)
        )
        
        result = {
            "query": query,
            "filters": filters,
            "total_results": response.total_results,
            "results": [
                {
                    "name": m.name,
                    "description": m.description[:100] if m.description else None,
                    "materialization": m.get_materialization(),
                    "schema": m.config.schema,
                    "tags": list(set(m.tags + m.config.tags))
                }
                for m in response.results
            ]
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _list_datasets(self, arguments: Dict[str, Any]) -> List[TextContent]:
        warehouse_type = arguments.get("warehouse_type")
        
        if not self.current_registry:
            return [TextContent(type="text", text="No models parsed yet. Please parse a dbt project or schema first.")]
        
        mappings = {}
        for model in self.current_registry.project.models:
            dataset = model.config.schema or "default"
            if dataset not in mappings:
                mappings[dataset] = []
            mappings[dataset].append(model.name)
        
        wh_type = None
        if warehouse_type:
            try:
                wh_type = WarehouseType(warehouse_type.lower())
            except ValueError:
                pass
        
        response = DatasetMappingResponse(
            warehouse_type=wh_type,
            mappings=mappings,
            total_models=len(self.current_registry.project.models)
        )
        
        result = {
            "warehouse_type": warehouse_type,
            "total_models": response.total_models,
            "datasets": {
                dataset: {
                    "models": models,
                    "count": len(models)
                }
                for dataset, models in response.mappings.items()
            }
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _get_model_lineage(self, arguments: Dict[str, Any]) -> List[TextContent]:
        model_name = arguments.get("model_name", "")
        depth = arguments.get("depth", 1)
        
        if not self.current_registry:
            return [TextContent(type="text", text="No models parsed yet. Please parse a dbt project or schema first.")]
        
        model = self.current_registry.model_index.get(model_name.lower())
        if not model:
            return [TextContent(type="text", text=f"Model '{model_name}' not found")]
        
        lineage = DbtParser.extract_basic_lineage(self.current_registry.project.models)
        model_lineage = lineage.get(model.name, {"upstream": [], "downstream": []})
        
        response = LineageResponse(
            model_name=model.name,
            upstream=model_lineage["upstream"],
            downstream=model_lineage["downstream"],
            depth=depth
        )
        
        result = {
            "model": model.name,
            "depth": depth,
            "upstream": response.upstream,
            "downstream": response.downstream,
            "upstream_count": len(response.upstream),
            "downstream_count": len(response.downstream)
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _list_model_tags(self, arguments: Dict[str, Any]) -> List[TextContent]:
        if not self.current_registry:
            return [TextContent(type="text", text="No models parsed yet. Please parse a dbt project or schema first.")]
        
        tag_counts = {}
        for tag, model_names in self.current_registry.tag_index.items():
            tag_counts[tag] = len(model_names)
        
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        
        result = {
            "total_tags": len(sorted_tags),
            "tags": [
                {
                    "tag": tag,
                    "model_count": count,
                    "models": self.current_registry.tag_index[tag][:5]
                }
                for tag, count in sorted_tags
            ]
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _get_models_by_materialization(self, arguments: Dict[str, Any]) -> List[TextContent]:
        materialization_type = arguments.get("materialization_type", "")
        
        if not self.current_registry:
            return [TextContent(type="text", text="No models parsed yet. Please parse a dbt project or schema first.")]
        
        models = self.current_registry.get_by_materialization(materialization_type)
        
        result = {
            "materialization": materialization_type,
            "model_count": len(models),
            "models": [
                {
                    "name": m.name,
                    "description": m.description[:100] if m.description else None,
                    "schema": m.config.schema,
                    "database": m.config.database,
                    "tags": list(set(m.tags + m.config.tags))
                }
                for m in models[:20]
            ]
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def run(self):
        async with self.server.run() as conn:
            await conn.initialize(
                InitializationOptions(
                    server_name="dbt-core-mcp",
                    server_version="1.0.0",
                    capabilities={}
                )
            )
            await conn.wait_closed()
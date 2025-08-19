import yaml
import re
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from src.models import (
    DbtModel, DbtColumn, DbtTest, DbtSource, DbtExposure, DbtMetric,
    DbtProject, ProjectConfig, ModelConfig, MaterializationType,
    TestSeverity, ModelRegistry, WarehouseConfig, WarehouseType
)


class DbtParser:
    
    @staticmethod
    def parse_dbt_project(yaml_content: str) -> DbtProject:
        try:
            data = yaml.safe_load(yaml_content)
            if not data:
                data = {}
            
            config = ProjectConfig(
                name=data.get("name", "unknown"),
                version=data.get("version"),
                profile=data.get("profile"),
                model_paths=data.get("model-paths", ["models"]),
                seed_paths=data.get("seed-paths", ["data"]),
                test_paths=data.get("test-paths", ["tests"]),
                analysis_paths=data.get("analysis-paths", ["analyses"]),
                macro_paths=data.get("macro-paths", ["macros"]),
                snapshot_paths=data.get("snapshot-paths", ["snapshots"]),
                target_path=data.get("target-path", "target"),
                clean_targets=data.get("clean-targets", ["target", "dbt_packages"]),
                vars=data.get("vars", {}),
                models=data.get("models", {}),
                seeds=data.get("seeds", {}),
                tests=data.get("tests", {}),
                snapshots=data.get("snapshots", {}),
                sources=data.get("sources", {}),
                quoting=data.get("quoting", {}),
                on_run_start=data.get("on-run-start", []),
                on_run_end=data.get("on-run-end", [])
            )
            
            return DbtProject(config=config)
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in dbt_project.yml: {e}")

    @staticmethod
    def parse_schema_file(yaml_content: str, project_context: Optional[Dict[str, Any]] = None) -> Dict[str, List[Any]]:
        try:
            data = yaml.safe_load(yaml_content)
            if not data:
                return {"models": [], "sources": [], "exposures": [], "metrics": []}
            
            version = data.get("version", 2)
            
            models = []
            sources = []
            exposures = []
            metrics = []
            
            if "models" in data:
                models = DbtParser._parse_models(data["models"], project_context)
            
            if "sources" in data:
                sources = DbtParser._parse_sources(data["sources"])
            
            if "exposures" in data:
                exposures = DbtParser._parse_exposures(data["exposures"])
            
            if "metrics" in data:
                metrics = DbtParser._parse_metrics(data["metrics"])
            
            return {
                "models": models,
                "sources": sources,
                "exposures": exposures,
                "metrics": metrics
            }
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in schema file: {e}")

    @staticmethod
    def _parse_models(models_data: List[Dict], project_context: Optional[Dict] = None) -> List[DbtModel]:
        models = []
        
        for model_data in models_data:
            model = DbtParser._parse_single_model(model_data, project_context)
            models.append(model)
        
        return models

    @staticmethod
    def _parse_single_model(model_data: Dict, project_context: Optional[Dict] = None) -> DbtModel:
        config_data = model_data.get("config", {})
        
        if project_context and "models" in project_context:
            model_name = model_data.get("name", "")
            project_config = DbtParser._get_model_config_from_project(model_name, project_context["models"])
            config_data = {**project_config, **config_data}
        
        config = ModelConfig(
            materialized=MaterializationType(config_data.get("materialized", "view")) if config_data.get("materialized") else None,
            schema=config_data.get("schema"),
            database=config_data.get("database"),
            alias=config_data.get("alias"),
            tags=config_data.get("tags", []),
            meta=config_data.get("meta", {}),
            docs=config_data.get("docs", {}),
            enabled=config_data.get("enabled", True),
            persist_docs=config_data.get("persist_docs", {}),
            pre_hook=config_data.get("pre-hook", config_data.get("pre_hook", [])),
            post_hook=config_data.get("post-hook", config_data.get("post_hook", [])),
            grants=config_data.get("grants", {}),
            contract=config_data.get("contract", {}),
            on_schema_change=config_data.get("on_schema_change"),
            on_configuration_change=config_data.get("on_configuration_change"),
            unique_key=config_data.get("unique_key"),
            cluster_by=config_data.get("cluster_by"),
            partition_by=config_data.get("partition_by")
        )
        
        columns = []
        for col_data in model_data.get("columns", []):
            columns.append(DbtParser._parse_column(col_data))
        
        tests = []
        for test_data in model_data.get("tests", []):
            tests.append(DbtParser._parse_test(test_data))
        
        model = DbtModel(
            name=model_data.get("name", ""),
            description=model_data.get("description"),
            columns=columns,
            config=config,
            tests=tests,
            tags=model_data.get("tags", []),
            meta=model_data.get("meta", {}),
            docs=model_data.get("docs", {}),
            latest_version=model_data.get("latest_version"),
            access=model_data.get("access", "protected"),
            group=model_data.get("group"),
            patch_path=model_data.get("patch_path"),
            original_file_path=model_data.get("original_file_path")
        )
        
        return model

    @staticmethod
    def _parse_column(col_data: Dict) -> DbtColumn:
        tests = []
        for test_data in col_data.get("tests", []):
            tests.append(DbtParser._parse_test(test_data, col_data.get("name")))
        
        constraints = []
        if col_data.get("constraints"):
            for constraint in col_data["constraints"]:
                if isinstance(constraint, str):
                    constraints.append(constraint)
                elif isinstance(constraint, dict):
                    constraints.append(constraint.get("type", ""))
        
        return DbtColumn(
            name=col_data.get("name", ""),
            description=col_data.get("description"),
            data_type=col_data.get("data_type"),
            constraints=constraints,
            tests=tests,
            meta=col_data.get("meta", {}),
            tags=col_data.get("tags", []),
            quote=col_data.get("quote")
        )

    @staticmethod
    def _parse_test(test_data: Any, column_name: Optional[str] = None) -> DbtTest:
        if isinstance(test_data, str):
            return DbtTest(
                name=test_data,
                type="generic",
                column_name=column_name
            )
        elif isinstance(test_data, dict):
            test_name = list(test_data.keys())[0] if test_data else "unknown"
            test_config = test_data.get(test_name, {}) if isinstance(test_data.get(test_name), dict) else {}
            
            return DbtTest(
                name=test_name,
                type="generic",
                severity=TestSeverity(test_config.get("severity", "error")) if test_config.get("severity") else TestSeverity.ERROR,
                config=test_config.get("config", {}),
                column_name=column_name,
                kwargs=test_config
            )
        return DbtTest(name="unknown", column_name=column_name)

    @staticmethod
    def _parse_sources(sources_data: List[Dict]) -> List[DbtSource]:
        sources = []
        
        for source_data in sources_data:
            tables = []
            for table_data in source_data.get("tables", []):
                table_model = DbtParser._parse_single_model(table_data)
                tables.append(table_model)
            
            source = DbtSource(
                name=source_data.get("name", ""),
                database=source_data.get("database"),
                schema=source_data.get("schema"),
                description=source_data.get("description"),
                tables=tables,
                meta=source_data.get("meta", {}),
                tags=source_data.get("tags", []),
                freshness=source_data.get("freshness"),
                loaded_at_field=source_data.get("loaded_at_field"),
                loader=source_data.get("loader")
            )
            sources.append(source)
        
        return sources

    @staticmethod
    def _parse_exposures(exposures_data: List[Dict]) -> List[DbtExposure]:
        exposures = []
        
        for exp_data in exposures_data:
            exposure = DbtExposure(
                name=exp_data.get("name", ""),
                type=exp_data.get("type", "dashboard"),
                owner=exp_data.get("owner", {}),
                description=exp_data.get("description"),
                maturity=exp_data.get("maturity"),
                url=exp_data.get("url"),
                depends_on=exp_data.get("depends_on", []),
                tags=exp_data.get("tags", []),
                meta=exp_data.get("meta", {})
            )
            exposures.append(exposure)
        
        return exposures

    @staticmethod
    def _parse_metrics(metrics_data: List[Dict]) -> List[DbtMetric]:
        metrics = []
        
        for metric_data in metrics_data:
            metric = DbtMetric(
                name=metric_data.get("name", ""),
                label=metric_data.get("label", ""),
                model=metric_data.get("model", ""),
                description=metric_data.get("description"),
                calculation_method=metric_data.get("calculation_method", ""),
                expression=metric_data.get("expression", ""),
                timestamp=metric_data.get("timestamp"),
                time_grains=metric_data.get("time_grains", []),
                dimensions=metric_data.get("dimensions", []),
                filters=metric_data.get("filters", []),
                meta=metric_data.get("meta", {}),
                tags=metric_data.get("tags", [])
            )
            metrics.append(metric)
        
        return metrics

    @staticmethod
    def _get_model_config_from_project(model_name: str, models_config: Dict) -> Dict:
        config = {}
        
        for key, value in models_config.items():
            if key == model_name:
                if isinstance(value, dict):
                    config.update(value)
            elif key.startswith("+"):
                clean_key = key[1:]
                config[clean_key] = value
            elif isinstance(value, dict):
                nested_config = DbtParser._get_model_config_from_project(model_name, value)
                config.update(nested_config)
        
        return config

    @staticmethod
    def build_model_registry(project: DbtProject, warehouse_type: Optional[str] = None) -> ModelRegistry:
        warehouse_config = None
        if warehouse_type:
            try:
                warehouse_config = WarehouseConfig(type=WarehouseType(warehouse_type.lower()))
            except ValueError:
                pass
        
        registry = ModelRegistry(
            project=project,
            warehouse_config=warehouse_config
        )
        registry.build_indices()
        
        return registry

    @staticmethod
    def extract_basic_lineage(models: List[DbtModel]) -> Dict[str, Dict[str, List[str]]]:
        lineage = {}
        
        for model in models:
            model_lineage = {
                "upstream": [],
                "downstream": []
            }
            
            if model.refs:
                model_lineage["upstream"].extend(model.refs)
            if model.sources:
                model_lineage["upstream"].extend(model.sources)
            
            lineage[model.name] = model_lineage
        
        for model_name, model_deps in lineage.items():
            for upstream in model_deps["upstream"]:
                if upstream in lineage:
                    lineage[upstream]["downstream"].append(model_name)
        
        return lineage

    @staticmethod
    def search_models(models: List[DbtModel], query: str, filters: Optional[Dict[str, Any]] = None) -> List[DbtModel]:
        query_lower = query.lower()
        results = []
        
        for model in models:
            score = 0
            
            if query_lower in model.name.lower():
                score += 10
            
            if model.description and query_lower in model.description.lower():
                score += 5
            
            for col in model.columns:
                if query_lower in col.name.lower():
                    score += 3
                if col.description and query_lower in col.description.lower():
                    score += 2
            
            for tag in model.tags + model.config.tags:
                if query_lower in tag.lower():
                    score += 4
            
            if score > 0:
                if filters:
                    if "tags" in filters:
                        filter_tags = filters["tags"]
                        if isinstance(filter_tags, str):
                            filter_tags = [filter_tags]
                        if not any(t in model.tags + model.config.tags for t in filter_tags):
                            continue
                    
                    if "schema" in filters and model.config.schema != filters["schema"]:
                        continue
                    
                    if "materialization" in filters and model.get_materialization() != filters["materialization"]:
                        continue
                
                results.append((model, score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return [model for model, _ in results]

    @staticmethod
    def infer_warehouse_type(project: DbtProject) -> Optional[WarehouseType]:
        profile_name = project.config.profile
        
        if profile_name:
            profile_lower = profile_name.lower()
            if "bigquery" in profile_lower or "bq" in profile_lower:
                return WarehouseType.BIGQUERY
            elif "snowflake" in profile_lower:
                return WarehouseType.SNOWFLAKE
            elif "postgres" in profile_lower or "pg" in profile_lower:
                return WarehouseType.POSTGRES
            elif "redshift" in profile_lower:
                return WarehouseType.REDSHIFT
            elif "databricks" in profile_lower:
                return WarehouseType.DATABRICKS
            elif "synapse" in profile_lower:
                return WarehouseType.SYNAPSE
            elif "duckdb" in profile_lower:
                return WarehouseType.DUCKDB
        
        if project.config.vars:
            for key, value in project.config.vars.items():
                key_lower = key.lower()
                value_str = str(value).lower() if value else ""
                
                if "warehouse" in key_lower or "adapter" in key_lower:
                    if "bigquery" in value_str:
                        return WarehouseType.BIGQUERY
                    elif "snowflake" in value_str:
                        return WarehouseType.SNOWFLAKE
        
        return None
from typing import Dict, List, Optional, Any, Set
from pydantic import BaseModel, Field
from enum import Enum


class TestSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class MaterializationType(str, Enum):
    TABLE = "table"
    VIEW = "view"
    INCREMENTAL = "incremental"
    EPHEMERAL = "ephemeral"
    SNAPSHOT = "snapshot"
    SEED = "seed"


class DbtTest(BaseModel):
    name: str
    type: str = "generic"
    severity: TestSeverity = TestSeverity.ERROR
    config: Dict[str, Any] = Field(default_factory=dict)
    column_name: Optional[str] = None
    kwargs: Dict[str, Any] = Field(default_factory=dict)


class DbtColumn(BaseModel):
    name: str
    description: Optional[str] = None
    data_type: Optional[str] = None
    constraints: List[str] = Field(default_factory=list)
    tests: List[DbtTest] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    quote: Optional[bool] = None

    def has_tests(self) -> bool:
        return len(self.tests) > 0

    def has_documentation(self) -> bool:
        return self.description is not None and len(self.description) > 0


class ModelConfig(BaseModel):
    materialized: Optional[MaterializationType] = None
    schema: Optional[str] = None
    database: Optional[str] = None
    alias: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    docs: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    persist_docs: Dict[str, bool] = Field(default_factory=dict)
    pre_hook: List[str] = Field(default_factory=list)
    post_hook: List[str] = Field(default_factory=list)
    grants: Dict[str, List[str]] = Field(default_factory=dict)
    contract: Dict[str, Any] = Field(default_factory=dict)
    on_schema_change: Optional[str] = None
    on_configuration_change: Optional[str] = None
    unique_key: Optional[str] = None
    cluster_by: Optional[List[str]] = None
    partition_by: Optional[Dict[str, Any]] = None


class DbtModel(BaseModel):
    name: str
    description: Optional[str] = None
    columns: List[DbtColumn] = Field(default_factory=list)
    config: ModelConfig = Field(default_factory=ModelConfig)
    tests: List[DbtTest] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    docs: Dict[str, Any] = Field(default_factory=dict)
    latest_version: Optional[int] = None
    access: Optional[str] = "protected"
    group: Optional[str] = None
    sql_path: Optional[str] = None
    original_file_path: Optional[str] = None
    patch_path: Optional[str] = None
    depends_on: List[str] = Field(default_factory=list)
    refs: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)

    def get_test_columns(self) -> List[str]:
        return [col.name for col in self.columns if col.has_tests()]

    def get_documented_columns(self) -> List[str]:
        return [col.name for col in self.columns if col.has_documentation()]

    def get_column_by_name(self, name: str) -> Optional[DbtColumn]:
        for col in self.columns:
            if col.name.lower() == name.lower():
                return col
        return None

    def get_materialization(self) -> str:
        return self.config.materialized.value if self.config.materialized else "view"

    def get_full_name(self) -> str:
        parts = []
        if self.config.database:
            parts.append(self.config.database)
        if self.config.schema:
            parts.append(self.config.schema)
        parts.append(self.config.alias or self.name)
        return ".".join(parts)


class DbtSource(BaseModel):
    name: str
    database: Optional[str] = None
    schema: Optional[str] = None
    description: Optional[str] = None
    tables: List[DbtModel] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    freshness: Optional[Dict[str, Any]] = None
    loaded_at_field: Optional[str] = None
    loader: Optional[str] = None


class DbtExposure(BaseModel):
    name: str
    type: str
    owner: Dict[str, str]
    description: Optional[str] = None
    maturity: Optional[str] = None
    url: Optional[str] = None
    depends_on: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class DbtMetric(BaseModel):
    name: str
    label: str
    model: str
    description: Optional[str] = None
    calculation_method: str
    expression: str
    timestamp: Optional[str] = None
    time_grains: List[str] = Field(default_factory=list)
    dimensions: List[str] = Field(default_factory=list)
    filters: List[Dict[str, Any]] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class ProjectConfig(BaseModel):
    name: str
    version: Optional[str] = None
    profile: Optional[str] = None
    model_paths: List[str] = Field(default_factory=lambda: ["models"])
    seed_paths: List[str] = Field(default_factory=lambda: ["data"])
    test_paths: List[str] = Field(default_factory=lambda: ["tests"])
    analysis_paths: List[str] = Field(default_factory=lambda: ["analyses"])
    macro_paths: List[str] = Field(default_factory=lambda: ["macros"])
    snapshot_paths: List[str] = Field(default_factory=lambda: ["snapshots"])
    target_path: str = "target"
    clean_targets: List[str] = Field(default_factory=lambda: ["target", "dbt_packages"])
    vars: Dict[str, Any] = Field(default_factory=dict)
    models: Dict[str, Any] = Field(default_factory=dict)
    seeds: Dict[str, Any] = Field(default_factory=dict)
    tests: Dict[str, Any] = Field(default_factory=dict)
    snapshots: Dict[str, Any] = Field(default_factory=dict)
    sources: Dict[str, Any] = Field(default_factory=dict)
    quoting: Dict[str, bool] = Field(default_factory=dict)
    on_run_start: List[str] = Field(default_factory=list)
    on_run_end: List[str] = Field(default_factory=list)


class DbtProject(BaseModel):
    config: ProjectConfig
    models: List[DbtModel] = Field(default_factory=list)
    sources: List[DbtSource] = Field(default_factory=list)
    exposures: List[DbtExposure] = Field(default_factory=list)
    metrics: List[DbtMetric] = Field(default_factory=list)

    def get_model_by_name(self, name: str) -> Optional[DbtModel]:
        for model in self.models:
            if model.name.lower() == name.lower():
                return model
        return None

    def get_models_by_tag(self, tag: str) -> List[DbtModel]:
        return [m for m in self.models if tag in m.tags or tag in m.config.tags]

    def get_models_by_schema(self, schema: str) -> List[DbtModel]:
        return [m for m in self.models if m.config.schema == schema]

    def get_models_by_materialization(self, materialization: str) -> List[DbtModel]:
        return [m for m in self.models if m.get_materialization() == materialization]

    def get_all_tags(self) -> Set[str]:
        tags = set()
        for model in self.models:
            tags.update(model.tags)
            tags.update(model.config.tags)
        return tags


class WarehouseType(str, Enum):
    BIGQUERY = "bigquery"
    SNOWFLAKE = "snowflake"
    POSTGRES = "postgres"
    REDSHIFT = "redshift"
    DATABRICKS = "databricks"
    SYNAPSE = "synapse"
    DUCKDB = "duckdb"


class WarehouseConfig(BaseModel):
    type: WarehouseType
    dataset_mappings: Dict[str, str] = Field(default_factory=dict)
    schema_pattern: Optional[str] = None
    database_pattern: Optional[str] = None


class ModelRegistry(BaseModel):
    project: DbtProject
    warehouse_config: Optional[WarehouseConfig] = None
    model_index: Dict[str, DbtModel] = Field(default_factory=dict)
    tag_index: Dict[str, List[str]] = Field(default_factory=dict)
    schema_index: Dict[str, List[str]] = Field(default_factory=dict)
    materialization_index: Dict[str, List[str]] = Field(default_factory=dict)

    def build_indices(self):
        self.model_index.clear()
        self.tag_index.clear()
        self.schema_index.clear()
        self.materialization_index.clear()

        for model in self.project.models:
            self.model_index[model.name.lower()] = model

            for tag in model.tags + model.config.tags:
                if tag not in self.tag_index:
                    self.tag_index[tag] = []
                self.tag_index[tag].append(model.name)

            if model.config.schema:
                if model.config.schema not in self.schema_index:
                    self.schema_index[model.config.schema] = []
                self.schema_index[model.config.schema].append(model.name)

            mat = model.get_materialization()
            if mat not in self.materialization_index:
                self.materialization_index[mat] = []
            self.materialization_index[mat].append(model.name)

    def search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[DbtModel]:
        query_lower = query.lower()
        results = []
        scores = {}

        for model in self.project.models:
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
                    if "tags" in filters and not any(t in model.tags + model.config.tags for t in filters["tags"]):
                        continue
                    if "schema" in filters and model.config.schema != filters["schema"]:
                        continue
                    if "materialization" in filters and model.get_materialization() != filters["materialization"]:
                        continue
                
                scores[model.name] = score
                results.append(model)

        results.sort(key=lambda m: scores[m.name], reverse=True)
        return results

    def get_by_tag(self, tag: str) -> List[DbtModel]:
        model_names = self.tag_index.get(tag, [])
        return [self.model_index[name.lower()] for name in model_names if name.lower() in self.model_index]

    def get_by_materialization(self, materialization_type: str) -> List[DbtModel]:
        model_names = self.materialization_index.get(materialization_type, [])
        return [self.model_index[name.lower()] for name in model_names if name.lower() in self.model_index]


class ModelListResponse(BaseModel):
    models: List[DbtModel]
    total_count: int
    page: int = 1
    page_size: int = 50
    has_more: bool = False


class ModelDetailResponse(BaseModel):
    model: DbtModel
    lineage: Optional[Dict[str, List[str]]] = None
    warehouse_location: Optional[str] = None


class DatasetMappingResponse(BaseModel):
    warehouse_type: Optional[WarehouseType] = None
    mappings: Dict[str, List[str]] = Field(default_factory=dict)
    total_models: int = 0


class SearchResultResponse(BaseModel):
    results: List[DbtModel]
    query: str
    filters: Dict[str, Any] = Field(default_factory=dict)
    total_results: int = 0


class LineageResponse(BaseModel):
    model_name: str
    upstream: List[str] = Field(default_factory=list)
    downstream: List[str] = Field(default_factory=list)
    depth: int = 1
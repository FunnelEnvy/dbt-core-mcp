import pytest
from src.models import (
    DbtColumn, DbtModel, DbtTest, DbtProject, ProjectConfig,
    ModelConfig, MaterializationType, TestSeverity, ModelRegistry,
    DbtSource, DbtExposure, DbtMetric, WarehouseType, WarehouseConfig
)


class TestModels:
    
    def test_dbt_column_creation(self):
        column = DbtColumn(
            name="customer_id",
            description="Unique customer identifier",
            data_type="string",
            constraints=["not_null", "unique"],
            tests=[
                DbtTest(name="unique", column_name="customer_id"),
                DbtTest(name="not_null", column_name="customer_id")
            ]
        )
        
        assert column.name == "customer_id"
        assert column.has_tests() is True
        assert column.has_documentation() is True
        assert len(column.tests) == 2
    
    def test_dbt_model_creation(self):
        model = DbtModel(
            name="customer_summary",
            description="Customer aggregations",
            config=ModelConfig(
                materialized=MaterializationType.TABLE,
                schema="marts",
                database="analytics"
            ),
            columns=[
                DbtColumn(name="customer_id", data_type="string"),
                DbtColumn(name="total_orders", data_type="integer")
            ],
            tags=["customer", "daily"]
        )
        
        assert model.name == "customer_summary"
        assert model.get_materialization() == "table"
        assert model.get_full_name() == "analytics.marts.customer_summary"
        assert len(model.columns) == 2
        assert model.get_column_by_name("customer_id") is not None
        assert model.get_column_by_name("nonexistent") is None
    
    def test_dbt_test_creation(self):
        test = DbtTest(
            name="not_null",
            type="generic",
            severity=TestSeverity.ERROR,
            column_name="customer_id"
        )
        
        assert test.name == "not_null"
        assert test.severity == TestSeverity.ERROR
        assert test.column_name == "customer_id"
    
    def test_project_config(self):
        config = ProjectConfig(
            name="test_project",
            version="1.0.0",
            profile="test_profile",
            vars={"warehouse": "bigquery"}
        )
        
        assert config.name == "test_project"
        assert config.version == "1.0.0"
        assert config.vars["warehouse"] == "bigquery"
        assert config.model_paths == ["models"]
    
    def test_dbt_project(self):
        project = DbtProject(
            config=ProjectConfig(name="test_project"),
            models=[
                DbtModel(name="model1", tags=["tag1"]),
                DbtModel(name="model2", tags=["tag2"]),
                DbtModel(name="model3", config=ModelConfig(schema="custom"))
            ]
        )
        
        assert len(project.models) == 3
        assert project.get_model_by_name("model1") is not None
        assert project.get_model_by_name("MODEL1") is not None
        assert len(project.get_models_by_tag("tag1")) == 1
        assert len(project.get_models_by_schema("custom")) == 1
        assert len(project.get_all_tags()) == 2
    
    def test_model_registry(self):
        project = DbtProject(
            config=ProjectConfig(name="test_project"),
            models=[
                DbtModel(
                    name="model1",
                    description="Test model 1",
                    tags=["tag1", "shared"],
                    config=ModelConfig(
                        materialized=MaterializationType.TABLE,
                        schema="marts"
                    )
                ),
                DbtModel(
                    name="model2",
                    description="Customer data",
                    tags=["tag2", "shared"],
                    config=ModelConfig(
                        materialized=MaterializationType.VIEW,
                        schema="staging"
                    ),
                    columns=[
                        DbtColumn(name="customer_id", description="Customer ID")
                    ]
                )
            ]
        )
        
        registry = ModelRegistry(project=project)
        registry.build_indices()
        
        assert len(registry.model_index) == 2
        assert "model1" in registry.model_index
        assert len(registry.tag_index["shared"]) == 2
        assert len(registry.schema_index["marts"]) == 1
        assert len(registry.materialization_index["table"]) == 1
        
        search_results = registry.search("customer")
        assert len(search_results) == 1
        assert search_results[0].name == "model2"
        
        search_results = registry.search("model", {"tags": ["tag1"]})
        assert len(search_results) == 1
        assert search_results[0].name == "model1"
        
        tag_models = registry.get_by_tag("shared")
        assert len(tag_models) == 2
        
        table_models = registry.get_by_materialization("table")
        assert len(table_models) == 1
        assert table_models[0].name == "model1"
    
    def test_warehouse_config(self):
        config = WarehouseConfig(
            type=WarehouseType.BIGQUERY,
            dataset_mappings={"marts": "analytics_marts"}
        )
        
        assert config.type == WarehouseType.BIGQUERY
        assert config.dataset_mappings["marts"] == "analytics_marts"
    
    def test_dbt_source(self):
        source = DbtSource(
            name="raw_data",
            database="prod",
            schema="raw",
            description="Raw data from production",
            tables=[
                DbtModel(name="customers"),
                DbtModel(name="orders")
            ]
        )
        
        assert source.name == "raw_data"
        assert len(source.tables) == 2
        assert source.database == "prod"
    
    def test_dbt_exposure(self):
        exposure = DbtExposure(
            name="dashboard",
            type="dashboard",
            owner={"name": "Analytics Team", "email": "analytics@company.com"},
            depends_on=["model1", "model2"]
        )
        
        assert exposure.name == "dashboard"
        assert exposure.type == "dashboard"
        assert len(exposure.depends_on) == 2
    
    def test_dbt_metric(self):
        metric = DbtMetric(
            name="revenue",
            label="Total Revenue",
            model="order_facts",
            calculation_method="sum",
            expression="total_amount",
            time_grains=["day", "month", "year"]
        )
        
        assert metric.name == "revenue"
        assert metric.model == "order_facts"
        assert len(metric.time_grains) == 3
    
    def test_model_with_alias(self):
        model = DbtModel(
            name="long_model_name",
            config=ModelConfig(
                alias="short_name",
                schema="marts",
                database="prod"
            )
        )
        
        assert model.get_full_name() == "prod.marts.short_name"
    
    def test_empty_model_registry_search(self):
        project = DbtProject(config=ProjectConfig(name="empty"))
        registry = ModelRegistry(project=project)
        registry.build_indices()
        
        results = registry.search("anything")
        assert results == []
        
        tag_models = registry.get_by_tag("nonexistent")
        assert tag_models == []
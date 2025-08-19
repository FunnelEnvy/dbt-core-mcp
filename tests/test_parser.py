import pytest
import yaml
from pathlib import Path
from src.dbt_parser import DbtParser
from src.models import DbtProject, DbtModel, MaterializationType, WarehouseType


class TestDbtParser:
    
    @pytest.fixture
    def sample_project_yml(self):
        fixture_path = Path(__file__).parent / "fixtures" / "sample_dbt_project.yml"
        with open(fixture_path, 'r') as f:
            return f.read()
    
    @pytest.fixture
    def sample_schema_yml(self):
        fixture_path = Path(__file__).parent / "fixtures" / "sample_schema.yml"
        with open(fixture_path, 'r') as f:
            return f.read()
    
    def test_parse_dbt_project(self, sample_project_yml):
        project = DbtParser.parse_dbt_project(sample_project_yml)
        
        assert isinstance(project, DbtProject)
        assert project.config.name == "analytics_dbt"
        assert project.config.version == "1.0.0"
        assert project.config.profile == "analytics"
        assert "models" in project.config.model_paths
        assert project.config.vars["warehouse_type"] == "bigquery"
    
    def test_parse_schema_file(self, sample_schema_yml):
        result = DbtParser.parse_schema_file(sample_schema_yml)
        
        assert "models" in result
        assert "sources" in result
        assert "exposures" in result
        assert "metrics" in result
        
        models = result["models"]
        assert len(models) == 2
        
        customer_summary = models[0]
        assert customer_summary.name == "customer_summary"
        assert customer_summary.description
        assert len(customer_summary.columns) == 7
        assert customer_summary.config.materialized == MaterializationType.TABLE
        assert customer_summary.config.schema == "marts_core"
        
        customer_id_col = customer_summary.get_column_by_name("customer_id")
        assert customer_id_col is not None
        assert customer_id_col.data_type == "string"
        assert len(customer_id_col.tests) == 2
    
    def test_infer_warehouse_type(self, sample_project_yml):
        project = DbtParser.parse_dbt_project(sample_project_yml)
        warehouse_type = DbtParser.infer_warehouse_type(project)
        
        assert warehouse_type == WarehouseType.BIGQUERY
    
    def test_search_models(self, sample_schema_yml):
        result = DbtParser.parse_schema_file(sample_schema_yml)
        models = result["models"]
        
        search_results = DbtParser.search_models(models, "customer")
        assert len(search_results) == 2
        assert search_results[0].name == "customer_summary"
        
        search_results = DbtParser.search_models(models, "order", {"materialization": "incremental"})
        assert len(search_results) == 1
        assert search_results[0].name == "order_facts"
    
    def test_extract_basic_lineage(self, sample_schema_yml):
        result = DbtParser.parse_schema_file(sample_schema_yml)
        models = result["models"]
        
        lineage = DbtParser.extract_basic_lineage(models)
        assert "customer_summary" in lineage
        assert "order_facts" in lineage
    
    def test_parse_invalid_yaml(self):
        invalid_yaml = "invalid: yaml: content: {"
        
        with pytest.raises(ValueError, match="Invalid YAML"):
            DbtParser.parse_dbt_project(invalid_yaml)
    
    def test_parse_empty_yaml(self):
        empty_yaml = ""
        
        project = DbtParser.parse_dbt_project(empty_yaml)
        assert project.config.name == "unknown"
        
        result = DbtParser.parse_schema_file(empty_yaml)
        assert result["models"] == []
        assert result["sources"] == []
    
    def test_build_model_registry(self, sample_project_yml, sample_schema_yml):
        project = DbtParser.parse_dbt_project(sample_project_yml)
        schema_result = DbtParser.parse_schema_file(sample_schema_yml)
        project.models = schema_result["models"]
        
        registry = DbtParser.build_model_registry(project, "bigquery")
        
        assert registry.project == project
        assert registry.warehouse_config.type == WarehouseType.BIGQUERY
        assert len(registry.model_index) == 2
        assert "customer_summary" in registry.model_index
        assert "order_facts" in registry.model_index
    
    def test_model_config_inheritance(self):
        project_yml = """
        name: test_project
        models:
          test_project:
            +materialized: view
            staging:
              +schema: staging
              model_a:
                +materialized: table
        """
        
        schema_yml = """
        version: 2
        models:
          - name: model_a
            description: "Test model"
        """
        
        project = DbtParser.parse_dbt_project(project_yml)
        result = DbtParser.parse_schema_file(schema_yml, {"models": project.config.models})
        
        model = result["models"][0]
        assert model.name == "model_a"
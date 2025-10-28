# Fertilizer Recommendation Feature Documentation

## Overview
The fertilizer recommendation feature provides crop-specific N-P-K fertilizer plans using LLM-assisted retrieval and structuring. It determines total nutrient requirements, basal vs topdressing applications, timing, and provides structured JSON output ready for agricultural planning.

## Quick Start
```bash
# Generate crop profile
agrr crop --query "tomato" > tomato_profile.json

# Get fertilizer recommendation
agrr fertilize recommend --crop-file tomato_profile.json --json
```

## Documentation Structure

### 📋 Design & Architecture
- **[FERTILIZER_RECOMMENDATION_DESIGN.md](architecture/FERTILIZER_RECOMMENDATION_DESIGN.md)** - Complete design document with Clean Architecture mapping, data contracts, and implementation guidelines

### 🔌 API & CLI Reference
- **[fertilizer_recommendation_api_reference.md](api/fertilizer_recommendation_api_reference.md)** - CLI and HTTP API contracts, input/output specifications

### 🧪 Technical Implementation
- **[CROP_PROFILE_FILE_SCHEMA.md](technical/CROP_PROFILE_FILE_SCHEMA.md)** - JSON schema for crop profile input files
- **[FERTILIZER_RECOMMENDATION_LLM_STRATEGY.md](guides/FERTILIZER_RECOMMENDATION_LLM_STRATEGY.md)** - LLM prompting, retrieval, and validation strategy
- **[FERTILIZER_RECOMMENDATION_TESTING_STRATEGY.md](guides/FERTILIZER_RECOMMENDATION_TESTING_STRATEGY.md)** - Testing approach, fixtures, and validation helpers

## Key Features

### ✅ Implemented Features
- **CLI Integration**: `agrr fertilize recommend` command with full help documentation
- **Mock Gateway**: In-memory gateway for testing and development (`--mock-fertilizer` flag)
- **LLM Gateway**: Real LLM-based recommendations with academic source citations
- **Structured Output**: JSON format with N-P-K totals, application schedules, and confidence scores
- **Unit Consistency**: All outputs in g/m² (grams per square meter)
- **Validation**: Input validation and error handling

### 🎯 Output Format
```json
{
  "crop": { "crop_id": "tomato", "name": "Tomato" },
  "totals": { "N": 18.0, "P": 5.2, "K": 12.4 },
  "applications": [
    {
      "type": "basal",
      "count": 1,
      "schedule_hint": "pre-plant",
      "nutrients": { "N": 6.0, "P": 2.0, "K": 3.0 }
    },
    {
      "type": "topdress",
      "count": 2,
      "schedule_hint": "early fruit set; mid fruiting",
      "nutrients": { "N": 12.0, "P": 3.2, "K": 9.4 },
      "per_application": { "N": 6.0, "P": 1.6, "K": 4.7 }
    }
  ],
  "sources": ["https://example.org/tomato-fertilizer", "JAガイド 2021 p.12-18"],
  "confidence": 0.7,
  "notes": "Adjust based on soil test results"
}
```

## Architecture

### Clean Architecture Layers
- **Entities**: `Nutrients`, `FertilizerApplication`, `FertilizerPlan`
- **UseCase**: `FertilizerLLMRecommendInteractor` (1クラス1ユースケース)
- **Gateway**: `FertilizerRecommendGateway` interface with LLM and in-memory implementations
- **Adapter**: CLI controller, presenter, and file service integration

### File Structure
```
src/agrr_core/
├── entity/entities/fertilizer_recommendation_entity.py
├── usecase/
│   ├── gateways/fertilizer_recommend_gateway.py
│   └── interactors/fertilizer_llm_recommend_interactor.py
└── adapter/
    ├── controllers/fertilizer_cli_recommend_controller.py
    ├── gateways/
    │   ├── fertilizer_llm_recommend_gateway.py
    │   └── fertilizer_recommend_inmemory_gateway.py
    └── presenters/fertilizer_recommend_cli_presenter.py
```

## Testing

### Test Coverage
- **Unit Tests**: UseCase interactor with fake gateway
- **Integration Tests**: CLI controller with mock data
- **End-to-End**: Full CLI workflow with both mock and LLM gateways

### Running Tests
```bash
# Unit tests
python -m pytest tests/test_usecase/test_fertilizer_llm_recommend_interactor.py -v

# Integration tests  
python -m pytest tests/test_adapter/test_fertilizer_cli_recommend_controller.py -v

# All fertilizer tests
python -m pytest tests/test_usecase/test_fertilizer_llm_recommend_interactor.py tests/test_adapter/test_fertilizer_cli_recommend_controller.py -v
```

## Usage Examples

### Basic Usage
```bash
# Generate crop profile
agrr crop --query "rice" > rice_profile.json

# Get recommendation (JSON output)
agrr fertilize recommend --crop-file rice_profile.json --json

# Save to file
agrr fertilize recommend --crop-file rice_profile.json --output rice_fertilizer.json
```

### Development/Testing
```bash
# Use mock gateway for testing
agrr fertilize recommend --crop-file rice_profile.json --mock-fertilizer --json
```

## Implementation Status

### ✅ Completed
- [x] Design documentation
- [x] Domain entities
- [x] UseCase interactor
- [x] Gateway interfaces and implementations
- [x] CLI controller and presenter
- [x] Unit and integration tests
- [x] CLI integration and help documentation
- [x] Mock gateway for testing
- [x] LLM gateway with academic sources

### 🔄 Future Enhancements
- [ ] HTTP API endpoint
- [ ] Additional crop types and regions
- [ ] Soil-specific recommendations
- [ ] Weather-based timing adjustments
- [ ] Cost optimization features

## Contributing

When extending this feature:
1. Follow Clean Architecture principles
2. Maintain test-first approach
3. Update documentation for new features
4. Ensure CLI help documentation is current
5. Add appropriate validation and error handling

## Related Documentation
- [Architecture Overview](architecture/ARCHITECTURE.md)
- [Clean Architecture Guidelines](architecture/CLEAN_ARCHITECTURE_GATEWAY_GUIDELINES.md)
- [CLI User Guide](../CLI_HELP_TEST_CASES.md)

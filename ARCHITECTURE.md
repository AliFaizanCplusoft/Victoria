# Victoria Project - Clean Modular Architecture

## Project Structure
```
Victoria_Project/
├── app/                          # Application entry points
│   ├── api/                      # FastAPI application
│   └── streamlit/                # Streamlit UI application
├── victoria/                     # Core business logic package
│   ├── config/                   # Configuration management
│   ├── core/                     # Core domain models and services
│   ├── processing/               # Data processing pipeline
│   ├── scoring/                  # Psychometric scoring
│   ├── clustering/               # Trait clustering
│   ├── reporting/                # Report generation
│   └── utils/                    # Shared utilities
├── data/                         # Data files
├── tests/                        # Test files
└── scripts/                      # Utility scripts
```

## Module Responsibilities

### victoria.config
- Environment configuration
- File path management
- Feature flags
- Constants

### victoria.core
- Domain models (TraitScore, PersonProfile, etc.)
- Core business interfaces
- Shared types and enums

### victoria.processing
- Data validation and cleaning
- RaschPy integration
- Data transformation pipeline

### victoria.scoring
- Individual trait scoring
- Percentile calculations
- Profile generation

### victoria.clustering
- Trait correlation analysis
- Clustering algorithms
- Archetype mapping (Vertria integration)

### victoria.reporting
- HTML report generation
- PDF export
- Visualization creation

### victoria.utils
- Common utilities
- Data helpers
- Logging setup

## Import Guidelines
- Use absolute imports: `from victoria.scoring import TraitScorer`
- Keep dependencies minimal between modules
- Core modules should not depend on app-specific modules
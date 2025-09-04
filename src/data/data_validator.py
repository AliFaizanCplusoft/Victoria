"""
Data Validation Module for Psychometric Assessment System

Validates data integrity, completeness, and format compliance
for incoming assessment data.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
from dataclasses import dataclass

# Fix the import - handle multiple import scenarios
try:
    from .item_mapper import ItemMapper, ITEM_TO_CONSTRUCT
except ImportError:
    try:
        from item_mapper import ItemMapper, ITEM_TO_CONSTRUCT
    except ImportError:
        # Create a fallback class if imports fail
        print("Warning: Could not import ItemMapper. Using fallback.")
        
        class ItemMapper:
            def __init__(self):
                self.constructs = {
                    'RT': 'Risk Taking',
                    'DA': 'Drive & Ambition',
                    'IO': 'Innovation Orientation',
                    'DM': 'Decision Making',
                    'RG': 'Resilience & Grit',
                    'SL': 'Servant Leadership',
                    'TB': 'Team Building',
                    'EI': 'Emotional Intelligence',
                    'A': 'Accountability',
                    'PS': 'Problem Solving',
                    'CT': 'Critical Thinking',
                    'F': 'Failure Response',
                    'AD': 'Adaptability',
                    'C': 'Conflict Management',
                    'N': 'Negotiation',
                    'RB': 'Relationship Building',
                    'IN': 'Influence',
                    'IIN': 'Interpersonal Intelligence'
                }
                self.item_construct_map = {}
                self.reverse_items = set()
            
            def get_all_constructs(self):
                return self.constructs
            
            def get_construct_for_item(self, item):
                return self.item_construct_map.get(item)
            
            def get_items_for_construct(self, construct):
                return [item for item, const in self.item_construct_map.items() if const == construct]
            
            def get_construct_name(self, construct_code):
                return self.constructs.get(construct_code, construct_code)
            
            def get_all_items(self):
                return list(self.item_construct_map.keys())
        
        ITEM_TO_CONSTRUCT = {}


@dataclass
class ValidationResult:
    """Container for validation results."""
    is_valid: bool
    person_id: str
    total_items: int
    missing_items: List[str]
    invalid_measures: List[str]
    warnings: List[str]
    errors: List[str]


@dataclass
class DatasetValidationSummary:
    """Summary of validation results for entire dataset."""
    total_persons: int
    valid_persons: int
    invalid_persons: int
    person_results: List[ValidationResult]
    overall_errors: List[str]
    overall_warnings: List[str]


class DataValidator:
    """
    Validates psychometric assessment data for integrity and completeness.
    
    Checks include:
    - Required item coverage per person
    - Rasch measure value ranges
    - Data format consistency
    - Person ID uniqueness
    - Item ID validity
    """
    
    def __init__(self, item_mapper: Optional[ItemMapper] = None):
        """
        Initialize validator with item mapping configuration.
        
        Args:
            item_mapper: ItemMapper instance for validation rules
        """
        self.logger = logging.getLogger(__name__)
        self.item_mapper = item_mapper or ItemMapper()
        
        # Validation thresholds
        self.min_rasch_measure = -4.0
        self.max_rasch_measure = 4.0
        self.required_items_per_person = 147  # Based on your data analysis
        self.min_completion_rate = 0.95  # 95% item completion required
        
        self.logger.info("DataValidator initialized with validation thresholds")
    
    def validate_dataset(self, data: pd.DataFrame) -> DatasetValidationSummary:
        """
        Validate entire dataset of assessment responses.
        
        Args:
            data: DataFrame with columns ['Measure', 'E1', 'E2', 'Persons', 'Assessment_Items']
            
        Returns:
            DatasetValidationSummary with validation results
        """
        self.logger.info(f"Starting validation of dataset with {len(data)} records")
        
        # Overall dataset checks
        overall_errors = []
        overall_warnings = []
        
        # Check required columns
        required_columns = ['Measure', 'E1', 'E2', 'Persons', 'Assessment_Items']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            overall_errors.append(f"Missing required columns: {missing_columns}")
            return DatasetValidationSummary(
                total_persons=0,
                valid_persons=0, 
                invalid_persons=0,
                person_results=[],
                overall_errors=overall_errors,
                overall_warnings=overall_warnings
            )
        
        # Check for duplicate records
        duplicates = data.duplicated(subset=['Persons', 'Assessment_Items']).sum()
        if duplicates > 0:
            overall_warnings.append(f"Found {duplicates} duplicate person-item combinations")
        
        # Group by person and validate each
        person_groups = data.groupby('Persons')
        person_results = []
        
        for person_id, person_data in person_groups:
            result = self.validate_person_data(person_id, person_data)
            person_results.append(result)
        
        # Summary statistics
        valid_persons = sum(1 for r in person_results if r.is_valid)
        invalid_persons = len(person_results) - valid_persons
        
        # Overall data quality checks
        self._check_overall_data_quality(data, overall_warnings, overall_errors)
        
        summary = DatasetValidationSummary(
            total_persons=len(person_results),
            valid_persons=valid_persons,
            invalid_persons=invalid_persons,
            person_results=person_results,
            overall_errors=overall_errors,
            overall_warnings=overall_warnings
        )
        
        self.logger.info(f"Validation complete: {valid_persons}/{len(person_results)} persons valid")
        
        return summary
    
    def validate_person_data(self, person_id: str, person_data: pd.DataFrame) -> ValidationResult:
        """
        Validate assessment data for a single person.
        
        Args:
            person_id: Unique person identifier
            person_data: DataFrame with person's assessment responses
            
        Returns:
            ValidationResult with validation details
        """
        errors = []
        warnings = []
        missing_items = []
        invalid_measures = []
        
        # Check item completeness
        person_items = set(person_data['Assessment_Items'].tolist())
        expected_items = set(self.item_mapper.get_all_items())
        
        missing_items = list(expected_items - person_items)
        completion_rate = len(person_items) / len(expected_items) if expected_items else 0
        
        if completion_rate < self.min_completion_rate:
            errors.append(f"Low completion rate: {completion_rate:.2%} (required: {self.min_completion_rate:.2%})")
        
        if len(missing_items) > 0:
            if len(missing_items) <= 5:
                warnings.append(f"Missing items: {missing_items}")
            else:
                warnings.append(f"Missing {len(missing_items)} items (showing first 5): {missing_items[:5]}")
        
        # Check measure value ranges
        measures = person_data['Measure'].dropna()
        
        # Check for extreme values
        extreme_low = measures[measures < self.min_rasch_measure]
        extreme_high = measures[measures > self.max_rasch_measure]
        
        if len(extreme_low) > 0:
            invalid_measures.extend(extreme_low.index.tolist())
            warnings.append(f"Found {len(extreme_low)} measures below {self.min_rasch_measure}")
        
        if len(extreme_high) > 0:
            invalid_measures.extend(extreme_high.index.tolist())
            warnings.append(f"Found {len(extreme_high)} measures above {self.max_rasch_measure}")
        
        # Check for missing measures
        missing_measures = person_data['Measure'].isna().sum()
        if missing_measures > 0:
            errors.append(f"Missing {missing_measures} measure values")
        
        # Check E1/E2 consistency
        e1_values = person_data['E1'].unique()
        if len(e1_values) > 1:
            warnings.append(f"Inconsistent E1 values for person: {e1_values}")
        
        # Check for item sequence issues
        e2_values = sorted(person_data['E2'].dropna().tolist())
        expected_sequence = list(range(1, len(e2_values) + 1))
        if e2_values != expected_sequence[:len(e2_values)]:
            warnings.append("Item sequence (E2) has gaps or duplicates")
        
        # Check for unmapped items
        unmapped_items = [item for item in person_items 
                         if self.item_mapper.get_construct_for_item(item) is None]
        if unmapped_items:
            warnings.append(f"Found {len(unmapped_items)} unmapped items: {unmapped_items[:3]}...")
        
        # Determine overall validity
        is_valid = (len(errors) == 0 and 
                   completion_rate >= self.min_completion_rate and
                   missing_measures == 0)
        
        return ValidationResult(
            is_valid=is_valid,
            person_id=person_id,
            total_items=len(person_items),
            missing_items=missing_items,
            invalid_measures=invalid_measures,
            warnings=warnings,
            errors=errors
        )
    
    def _check_overall_data_quality(self, data: pd.DataFrame, 
                                   warnings: List[str], 
                                   errors: List[str]):
        """Check overall data quality metrics."""
        
        # Check for consistent person counts per item
        items_per_person = data.groupby('Persons')['Assessment_Items'].count()
        item_count_variation = items_per_person.std()
        
        if item_count_variation > 5:  # Allow some variation
            warnings.append(f"High variation in items per person (std: {item_count_variation:.1f})")
        
        # Check measure distribution
        measures = data['Measure'].dropna()
        if len(measures) > 0:
            mean_measure = measures.mean()
            std_measure = measures.std()
            
            # Rasch measures should be roughly centered around 0
            if abs(mean_measure) > 0.5:
                warnings.append(f"Measure distribution not centered (mean: {mean_measure:.2f})")
            
            # Check for reasonable spread
            if std_measure < 0.5:
                warnings.append(f"Low measure variability (std: {std_measure:.2f})")
            elif std_measure > 2.0:
                warnings.append(f"High measure variability (std: {std_measure:.2f})")
        
        # Check for person ID format consistency
        person_ids = data['Persons'].unique()
        id_lengths = [len(str(pid)) for pid in person_ids]
        if len(set(id_lengths)) > 1:
            warnings.append("Inconsistent person ID format lengths")
    
    def generate_validation_report(self, summary: DatasetValidationSummary) -> str:
        """
        Generate a human-readable validation report.
        
        Args:
            summary: DatasetValidationSummary from validation
            
        Returns:
            Formatted validation report string
        """
        report = []
        report.append("=" * 60)
        report.append("PSYCHOMETRIC DATA VALIDATION REPORT")
        report.append("=" * 60)
        
        # Overall summary
        report.append(f"\nDATASET SUMMARY:")
        report.append(f"Total Persons: {summary.total_persons}")
        report.append(f"Valid Persons: {summary.valid_persons}")
        report.append(f"Invalid Persons: {summary.invalid_persons}")
        report.append(f"Success Rate: {(summary.valid_persons/summary.total_persons)*100:.1f}%")
        
        # Overall issues
        if summary.overall_errors:
            report.append(f"\nCRITICAL ERRORS:")
            for error in summary.overall_errors:
                report.append(f"  • {error}")
        
        if summary.overall_warnings:
            report.append(f"\nWARNINGS:")
            for warning in summary.overall_warnings[:10]:  # Limit to first 10
                report.append(f"  • {warning}")
            if len(summary.overall_warnings) > 10:
                report.append(f"  ... and {len(summary.overall_warnings) - 10} more warnings")
        
        # Person-level issues
        invalid_persons = [r for r in summary.person_results if not r.is_valid]
        if invalid_persons:
            report.append(f"\nINVALID PERSONS ({len(invalid_persons)}):")
            for result in invalid_persons[:5]:  # Show first 5
                report.append(f"  Person {result.person_id}:")
                report.append(f"    Items: {result.total_items}, Missing: {len(result.missing_items)}")
                for error in result.errors:
                    report.append(f"    ERROR: {error}")
            if len(invalid_persons) > 5:
                report.append(f"  ... and {len(invalid_persons) - 5} more invalid persons")
        
        # Item coverage analysis
        all_missing_items = []
        for result in summary.person_results:
            all_missing_items.extend(result.missing_items)
        
        if all_missing_items:
            from collections import Counter
            missing_counts = Counter(all_missing_items)
            most_missing = missing_counts.most_common(5)
            
            report.append(f"\nMOST FREQUENTLY MISSING ITEMS:")
            for item, count in most_missing:
                construct = self.item_mapper.get_construct_for_item(item)
                report.append(f"  {item} ({construct}): missing in {count} persons")
        
        # Construct coverage
        construct_coverage = self._analyze_construct_coverage(summary.person_results)
        if construct_coverage:
            report.append(f"\nCONSTRUCT COVERAGE ANALYSIS:")
            for construct, stats in construct_coverage.items():
                construct_name = self.item_mapper.get_construct_name(construct)
                report.append(f"  {construct} ({construct_name}):")
                report.append(f"    Complete: {stats['complete_persons']}/{summary.total_persons} persons")
                report.append(f"    Avg items: {stats['avg_items']:.1f}/{stats['total_items']}")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)
    
    def _analyze_construct_coverage(self, person_results: List[ValidationResult]) -> Dict[str, Dict]:
        """Analyze coverage by construct."""
        construct_stats = {}
        
        for construct_code in self.item_mapper.get_all_constructs().keys():
            construct_items = set(self.item_mapper.get_items_for_construct(construct_code))
            
            complete_persons = 0
            total_items_found = 0
            
            for result in person_results:
                person_items = set(self.item_mapper.get_all_items()) - set(result.missing_items)
                construct_person_items = person_items.intersection(construct_items)
                
                if len(construct_person_items) == len(construct_items):
                    complete_persons += 1
                
                total_items_found += len(construct_person_items)
            
            if len(construct_items) > 0:  # Only include constructs with mapped items
                construct_stats[construct_code] = {
                    'complete_persons': complete_persons,
                    'total_items': len(construct_items),
                    'avg_items': total_items_found / len(person_results) if person_results else 0
                }
        
        return construct_stats
    
    def export_validation_results(self, summary: DatasetValidationSummary, 
                                 filepath: str, format: str = 'csv'):
        """
        Export validation results to file.
        
        Args:
            summary: DatasetValidationSummary to export
            filepath: Output file path
            format: Export format ('csv' or 'json')
        """
        if format.lower() == 'csv':
            self._export_csv(summary, filepath)
        elif format.lower() == 'json':
            self._export_json(summary, filepath)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_csv(self, summary: DatasetValidationSummary, filepath: str):
        """Export validation results as CSV."""
        results_data = []
        
        for result in summary.person_results:
            results_data.append({
                'Person_ID': result.person_id,
                'Is_Valid': result.is_valid,
                'Total_Items': result.total_items,
                'Missing_Items_Count': len(result.missing_items),
                'Missing_Items': '; '.join(result.missing_items),
                'Invalid_Measures_Count': len(result.invalid_measures),
                'Errors_Count': len(result.errors),
                'Warnings_Count': len(result.warnings),
                'Errors': '; '.join(result.errors),
                'Warnings': '; '.join(result.warnings)
            })
        
        df = pd.DataFrame(results_data)
        df.to_csv(filepath, index=False)
        self.logger.info(f"Validation results exported to {filepath}")
    
    def _export_json(self, summary: DatasetValidationSummary, filepath: str):
        """Export validation results as JSON."""
        import json
        
        # Convert to serializable format
        export_data = {
            'summary': {
                'total_persons': summary.total_persons,
                'valid_persons': summary.valid_persons,
                'invalid_persons': summary.invalid_persons,
                'overall_errors': summary.overall_errors,
                'overall_warnings': summary.overall_warnings
            },
            'person_results': []
        }
        
        for result in summary.person_results:
            export_data['person_results'].append({
                'person_id': result.person_id,
                'is_valid': result.is_valid,
                'total_items': result.total_items,
                'missing_items': result.missing_items,
                'invalid_measures': result.invalid_measures,
                'warnings': result.warnings,
                'errors': result.errors
            })
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        self.logger.info(f"Validation results exported to {filepath}")


def validate_file(filepath: str, item_mapper: Optional[ItemMapper] = None) -> DatasetValidationSummary:
    """
    Convenience function to validate a data file directly.
    
    Args:
        filepath: Path to CSV or tab-delimited file
        item_mapper: Optional ItemMapper instance
        
    Returns:
        DatasetValidationSummary with validation results
    """
    # Try to detect delimiter
    with open(filepath, 'r') as f:
        first_line = f.readline()
        delimiter = '\t' if '\t' in first_line else ','
    
    # Read data
    data = pd.read_csv(filepath, delimiter=delimiter)
    
    # Validate
    validator = DataValidator(item_mapper)
    return validator.validate_dataset(data)


if __name__ == "__main__":
    # Demo usage
    import sys
    
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        summary = validate_file(filepath)
        
        validator = DataValidator()
        report = validator.generate_validation_report(summary)
        print(report)
        
        # Export results
        validator.export_validation_results(summary, 'validation_results.csv')
    else:
        print("Usage: python data_validator.py <data_file_path>")
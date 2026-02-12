"""Data analysis engine for imported Excel data.

Computes comprehensive statistics per column based on detected data types,
including numerical stats, categorical distributions, and data quality metrics.
"""

import math
from collections import Counter
from datetime import datetime, date, time
from typing import Any, Optional

from task_manager.excel_report.importer import DataType, ImportResult, SheetData


class ColumnStats:
    """Statistical analysis results for a single column."""

    def __init__(self, header: str, data_type: DataType):
        self.header = header
        self.data_type = data_type
        self.total_count: int = 0
        self.non_empty_count: int = 0
        self.empty_count: int = 0
        self.unique_count: int = 0
        self.completeness: float = 0.0

        # Numeric stats (for Integer, Float, Currency, Percentage)
        self.min_val: Optional[float] = None
        self.max_val: Optional[float] = None
        self.sum_val: Optional[float] = None
        self.mean_val: Optional[float] = None
        self.median_val: Optional[float] = None
        self.std_dev: Optional[float] = None

        # Text stats
        self.min_length: Optional[int] = None
        self.max_length: Optional[int] = None
        self.avg_length: Optional[float] = None

        # Categorical stats
        self.top_values: list[tuple[str, int]] = []

        # Date stats
        self.earliest: Optional[str] = None
        self.latest: Optional[str] = None

        # Boolean stats
        self.true_count: int = 0
        self.false_count: int = 0

        # Data quality
        self.duplicate_count: int = 0
        self.has_outliers: bool = False
        self.outlier_count: int = 0

    def to_dict(self) -> dict:
        result: dict[str, Any] = {
            "header": self.header,
            "data_type": self.data_type.value,
            "total_count": self.total_count,
            "non_empty_count": self.non_empty_count,
            "empty_count": self.empty_count,
            "unique_count": self.unique_count,
            "completeness": round(self.completeness, 2),
            "duplicate_count": self.duplicate_count,
        }

        if self.data_type in (
            DataType.INTEGER,
            DataType.FLOAT,
            DataType.CURRENCY,
            DataType.PERCENTAGE,
        ):
            result["numeric_stats"] = {
                "min": self.min_val,
                "max": self.max_val,
                "sum": round(self.sum_val, 4) if self.sum_val is not None else None,
                "mean": round(self.mean_val, 4) if self.mean_val is not None else None,
                "median": self.median_val,
                "std_dev": (
                    round(self.std_dev, 4) if self.std_dev is not None else None
                ),
                "has_outliers": self.has_outliers,
                "outlier_count": self.outlier_count,
            }

        if self.data_type in (DataType.TEXT, DataType.EMAIL, DataType.URL):
            result["text_stats"] = {
                "min_length": self.min_length,
                "max_length": self.max_length,
                "avg_length": (
                    round(self.avg_length, 1) if self.avg_length is not None else None
                ),
            }

        if self.data_type == DataType.BOOLEAN:
            result["boolean_stats"] = {
                "true_count": self.true_count,
                "false_count": self.false_count,
                "true_pct": (
                    round(self.true_count / self.non_empty_count * 100, 1)
                    if self.non_empty_count > 0
                    else 0
                ),
            }

        if self.data_type in (DataType.DATE, DataType.DATETIME):
            result["date_stats"] = {
                "earliest": self.earliest,
                "latest": self.latest,
            }

        if self.top_values:
            result["top_values"] = [
                {"value": v, "count": c} for v, c in self.top_values
            ]

        return result


class SheetAnalysis:
    """Full analysis of a single sheet."""

    def __init__(self, sheet_name: str):
        self.sheet_name = sheet_name
        self.row_count: int = 0
        self.col_count: int = 0
        self.column_stats: list[ColumnStats] = []
        self.data_quality_score: float = 0.0
        self.type_summary: dict[str, int] = {}
        self.duplicate_rows: int = 0
        self.completely_empty_rows: int = 0

    def to_dict(self) -> dict:
        return {
            "sheet_name": self.sheet_name,
            "row_count": self.row_count,
            "col_count": self.col_count,
            "data_quality_score": round(self.data_quality_score, 1),
            "type_summary": self.type_summary,
            "duplicate_rows": self.duplicate_rows,
            "completely_empty_rows": self.completely_empty_rows,
            "columns": [cs.to_dict() for cs in self.column_stats],
        }


class AnalysisResult:
    """Full analysis result for an entire workbook."""

    def __init__(self, file_name: str):
        self.file_name = file_name
        self.analysis_time: str = datetime.now().isoformat()
        self.sheets: list[SheetAnalysis] = []
        self.overall_quality_score: float = 0.0
        self.total_rows: int = 0
        self.total_columns: int = 0

    def to_dict(self) -> dict:
        return {
            "file_name": self.file_name,
            "analysis_time": self.analysis_time,
            "overall_quality_score": round(self.overall_quality_score, 1),
            "total_rows": self.total_rows,
            "total_columns": self.total_columns,
            "sheet_count": len(self.sheets),
            "sheets": [s.to_dict() for s in self.sheets],
        }


def _to_numeric(value: Any) -> Optional[float]:
    """Attempt to convert a value to a float for numeric analysis."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        # Strip currency symbols
        for sym in ("$", "\u20ac", "\u00a3", "\u00a5", "\u20b9"):
            cleaned = cleaned.replace(sym, "")
        # Strip percentage
        cleaned = cleaned.rstrip("%").strip()
        try:
            return float(cleaned)
        except (ValueError, OverflowError):
            return None
    return None


def _to_date_sortable(value: Any) -> Optional[datetime]:
    """Convert a value to datetime for date comparisons."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    return None


def _is_truthy(value: Any) -> bool:
    """Check if a boolean-ish value is truthy."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("true", "yes")
    return False


class DataAnalyzer:
    """Analyzes imported Excel data and produces comprehensive statistics."""

    def analyze(self, import_result: ImportResult) -> AnalysisResult:
        """Run full analysis on an import result.

        Args:
            import_result: The result from ExcelImporter.import_file().

        Returns:
            AnalysisResult with statistics for every column of every sheet.
        """
        result = AnalysisResult(import_result.file_name)
        result.total_rows = import_result.total_rows
        result.total_columns = import_result.total_columns

        quality_scores = []

        for sheet_data in import_result.sheets:
            sheet_analysis = self._analyze_sheet(sheet_data)
            result.sheets.append(sheet_analysis)
            quality_scores.append(sheet_analysis.data_quality_score)

        if quality_scores:
            result.overall_quality_score = sum(quality_scores) / len(quality_scores)

        return result

    def _analyze_sheet(self, sheet: SheetData) -> SheetAnalysis:
        """Analyze a single sheet."""
        analysis = SheetAnalysis(sheet.name)
        analysis.row_count = sheet.row_count
        analysis.col_count = sheet.col_count

        type_summary: dict[str, int] = {}

        # Count duplicate and empty rows
        seen_rows: set[tuple] = set()
        for row in sheet.rows:
            row_tuple = tuple(str(v) if v is not None else "" for v in row)
            if all(v == "" for v in row_tuple):
                analysis.completely_empty_rows += 1
            elif row_tuple in seen_rows:
                analysis.duplicate_rows += 1
            seen_rows.add(row_tuple)

        completeness_scores = []

        for col_info in sheet.columns:
            col_values = [row[col_info.index] for row in sheet.rows]
            stats = self._analyze_column(col_info, col_values)
            analysis.column_stats.append(stats)
            completeness_scores.append(stats.completeness)

            dtype_name = col_info.detected_type.value
            type_summary[dtype_name] = type_summary.get(dtype_name, 0) + 1

        analysis.type_summary = type_summary

        # Data quality score: combination of completeness and uniqueness
        if completeness_scores:
            avg_completeness = sum(completeness_scores) / len(completeness_scores)
            dup_penalty = (
                min(analysis.duplicate_rows / max(analysis.row_count, 1) * 100, 30)
            )
            analysis.data_quality_score = max(avg_completeness - dup_penalty, 0)
        else:
            analysis.data_quality_score = 0.0

        return analysis

    def _analyze_column(
        self, col_info: Any, values: list[Any]
    ) -> ColumnStats:
        """Compute full statistics for a single column."""
        stats = ColumnStats(col_info.header, col_info.detected_type)
        stats.total_count = col_info.total_count
        stats.non_empty_count = col_info.non_empty_count
        stats.empty_count = col_info.empty_count
        stats.unique_count = col_info.unique_count

        if stats.total_count > 0:
            stats.completeness = (stats.non_empty_count / stats.total_count) * 100
        else:
            stats.completeness = 0.0

        # Duplicates
        non_empty_vals = [v for v in values if v is not None and str(v).strip() != ""]
        val_counts = Counter(str(v) for v in non_empty_vals)
        stats.duplicate_count = sum(c - 1 for c in val_counts.values() if c > 1)

        # Top values (most frequent)
        if val_counts:
            stats.top_values = val_counts.most_common(10)

        dtype = col_info.detected_type

        # Numeric analysis
        if dtype in (
            DataType.INTEGER,
            DataType.FLOAT,
            DataType.CURRENCY,
            DataType.PERCENTAGE,
        ):
            self._compute_numeric_stats(stats, values)

        # Text analysis
        elif dtype in (DataType.TEXT, DataType.EMAIL, DataType.URL, DataType.PHONE):
            self._compute_text_stats(stats, values)

        # Boolean analysis
        elif dtype == DataType.BOOLEAN:
            self._compute_boolean_stats(stats, values)

        # Date analysis
        elif dtype in (DataType.DATE, DataType.DATETIME):
            self._compute_date_stats(stats, values)

        return stats

    def _compute_numeric_stats(
        self, stats: ColumnStats, values: list[Any]
    ) -> None:
        """Compute min, max, mean, median, std deviation, outliers."""
        nums = [n for n in (_to_numeric(v) for v in values) if n is not None]
        if not nums:
            return

        nums_sorted = sorted(nums)
        stats.min_val = nums_sorted[0]
        stats.max_val = nums_sorted[-1]
        stats.sum_val = sum(nums)
        stats.mean_val = stats.sum_val / len(nums)

        # Median
        n = len(nums_sorted)
        if n % 2 == 1:
            stats.median_val = nums_sorted[n // 2]
        else:
            stats.median_val = (nums_sorted[n // 2 - 1] + nums_sorted[n // 2]) / 2

        # Standard deviation
        if len(nums) > 1:
            variance = sum((x - stats.mean_val) ** 2 for x in nums) / (len(nums) - 1)
            stats.std_dev = math.sqrt(variance)
        else:
            stats.std_dev = 0.0

        # Outlier detection using IQR method
        if len(nums) >= 4:
            q1_idx = len(nums_sorted) // 4
            q3_idx = 3 * len(nums_sorted) // 4
            q1 = nums_sorted[q1_idx]
            q3 = nums_sorted[q3_idx]
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outliers = [x for x in nums if x < lower_bound or x > upper_bound]
            stats.outlier_count = len(outliers)
            stats.has_outliers = len(outliers) > 0

    def _compute_text_stats(
        self, stats: ColumnStats, values: list[Any]
    ) -> None:
        """Compute text length statistics."""
        lengths = []
        for v in values:
            if v is not None:
                s = str(v).strip()
                if s:
                    lengths.append(len(s))

        if lengths:
            stats.min_length = min(lengths)
            stats.max_length = max(lengths)
            stats.avg_length = sum(lengths) / len(lengths)

    def _compute_boolean_stats(
        self, stats: ColumnStats, values: list[Any]
    ) -> None:
        """Count true/false distribution."""
        for v in values:
            if v is None:
                continue
            if isinstance(v, str) and v.strip() == "":
                continue
            if _is_truthy(v):
                stats.true_count += 1
            else:
                stats.false_count += 1

    def _compute_date_stats(
        self, stats: ColumnStats, values: list[Any]
    ) -> None:
        """Determine earliest and latest dates."""
        dates = [d for d in (_to_date_sortable(v) for v in values) if d is not None]
        if dates:
            dates_sorted = sorted(dates)
            stats.earliest = dates_sorted[0].isoformat()
            stats.latest = dates_sorted[-1].isoformat()

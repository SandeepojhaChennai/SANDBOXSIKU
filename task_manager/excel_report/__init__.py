"""Excel Import and Report Generation Module.

Provides smart Excel file importing with automatic data type detection,
statistical analysis, and professional report generation in both HTML
and Excel formats.
"""

from task_manager.excel_report.importer import ExcelImporter
from task_manager.excel_report.analyzer import DataAnalyzer
from task_manager.excel_report.report_html import HTMLReportGenerator
from task_manager.excel_report.report_excel import ExcelReportGenerator

__all__ = [
    "ExcelImporter",
    "DataAnalyzer",
    "HTMLReportGenerator",
    "ExcelReportGenerator",
]

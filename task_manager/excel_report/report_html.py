"""HTML report generator with professional styling.

Produces a self-contained HTML file with interactive sections,
data type badges, statistics cards, and data preview tables.
"""

import html
from typing import Any

from jinja2 import Template

from task_manager.excel_report.analyzer import AnalysisResult, ColumnStats
from task_manager.excel_report.importer import DataType, ImportResult

# Color mapping for data type badges
TYPE_COLORS = {
    DataType.INTEGER.value: "#2196F3",
    DataType.FLOAT.value: "#03A9F4",
    DataType.PERCENTAGE.value: "#00BCD4",
    DataType.CURRENCY.value: "#4CAF50",
    DataType.TEXT.value: "#FF9800",
    DataType.BOOLEAN.value: "#9C27B0",
    DataType.DATE.value: "#E91E63",
    DataType.TIME.value: "#F44336",
    DataType.DATETIME.value: "#E91E63",
    DataType.EMAIL.value: "#795548",
    DataType.URL.value: "#607D8B",
    DataType.PHONE.value: "#009688",
    DataType.EMPTY.value: "#9E9E9E",
    DataType.MIXED.value: "#FF5722",
}


HTML_TEMPLATE = Template(
    """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Excel Import Report - {{ file_name }}</title>
<style>
  :root {
    --primary: #1a73e8;
    --primary-light: #e8f0fe;
    --success: #34a853;
    --warning: #fbbc04;
    --danger: #ea4335;
    --bg: #f8f9fa;
    --card-bg: #ffffff;
    --text: #202124;
    --text-secondary: #5f6368;
    --border: #dadce0;
    --shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.08);
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    padding: 20px;
  }
  .container { max-width: 1400px; margin: 0 auto; }

  /* Header */
  .report-header {
    background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%);
    color: white;
    border-radius: 12px;
    padding: 32px 40px;
    margin-bottom: 24px;
    box-shadow: var(--shadow);
  }
  .report-header h1 { font-size: 28px; font-weight: 600; margin-bottom: 8px; }
  .report-header .subtitle { opacity: 0.9; font-size: 15px; }
  .report-header .meta { display: flex; gap: 32px; margin-top: 16px; flex-wrap: wrap; }
  .report-header .meta-item { font-size: 14px; opacity: 0.85; }
  .report-header .meta-item strong { font-weight: 600; opacity: 1; }

  /* Summary Cards */
  .summary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
  }
  .summary-card {
    background: var(--card-bg);
    border-radius: 10px;
    padding: 20px 24px;
    box-shadow: var(--shadow);
    text-align: center;
  }
  .summary-card .value {
    font-size: 36px;
    font-weight: 700;
    color: var(--primary);
    line-height: 1.2;
  }
  .summary-card .label {
    font-size: 13px;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 4px;
  }
  .quality-score .value {
    color: {{ quality_color }};
  }

  /* Sections */
  .section {
    background: var(--card-bg);
    border-radius: 10px;
    margin-bottom: 20px;
    box-shadow: var(--shadow);
    overflow: hidden;
  }
  .section-header {
    padding: 18px 24px;
    background: #fafafa;
    border-bottom: 1px solid var(--border);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .section-header h2 { font-size: 18px; font-weight: 600; }
  .section-header .toggle { font-size: 20px; color: var(--text-secondary); transition: transform 0.2s; }
  .section-content { padding: 24px; }

  /* Data type badges */
  .type-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
    color: white;
    white-space: nowrap;
  }

  /* Column cards */
  .column-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 16px;
  }
  .col-card {
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 18px;
    transition: box-shadow 0.2s;
  }
  .col-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
  .col-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
  }
  .col-card-header h3 { font-size: 15px; font-weight: 600; }
  .col-card .stat-row {
    display: flex;
    justify-content: space-between;
    padding: 4px 0;
    font-size: 13px;
    border-bottom: 1px solid #f0f0f0;
  }
  .col-card .stat-row:last-child { border-bottom: none; }
  .col-card .stat-label { color: var(--text-secondary); }
  .col-card .stat-value { font-weight: 600; }

  /* Completeness bar */
  .completeness-bar {
    height: 6px;
    background: #e0e0e0;
    border-radius: 3px;
    margin: 8px 0;
    overflow: hidden;
  }
  .completeness-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.3s;
  }

  /* Top values */
  .top-values { margin-top: 8px; }
  .top-value-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 3px 0;
    font-size: 12px;
  }
  .top-value-bar {
    height: 4px;
    background: var(--primary-light);
    border-radius: 2px;
    margin-top: 2px;
  }
  .top-value-bar-fill {
    height: 100%;
    background: var(--primary);
    border-radius: 2px;
  }

  /* Data preview table */
  .data-table-wrapper { overflow-x: auto; }
  .data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }
  .data-table th {
    background: #f5f5f5;
    padding: 10px 14px;
    text-align: left;
    font-weight: 600;
    border-bottom: 2px solid var(--border);
    white-space: nowrap;
  }
  .data-table td {
    padding: 8px 14px;
    border-bottom: 1px solid #f0f0f0;
    max-width: 250px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .data-table tr:hover td { background: #fafafa; }
  .data-table .type-row td {
    padding: 4px 14px;
    background: #fafcff;
    border-bottom: 2px solid var(--border);
  }

  /* Type Distribution */
  .type-dist {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    margin-top: 8px;
  }
  .type-dist-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
  }
  .type-dist-count { font-weight: 600; }

  /* Footer */
  .report-footer {
    text-align: center;
    padding: 20px;
    color: var(--text-secondary);
    font-size: 13px;
  }

  /* Responsive */
  @media (max-width: 768px) {
    body { padding: 12px; }
    .report-header { padding: 20px 24px; }
    .report-header h1 { font-size: 22px; }
    .column-grid { grid-template-columns: 1fr; }
  }

  /* Collapsible sections */
  .section-content.collapsed { display: none; }
</style>
</head>
<body>
<div class="container">

  <!-- Header -->
  <div class="report-header">
    <h1>Excel Import Report</h1>
    <div class="subtitle">Comprehensive data analysis with smart type detection</div>
    <div class="meta">
      <div class="meta-item"><strong>File:</strong> {{ file_name }}</div>
      <div class="meta-item"><strong>Generated:</strong> {{ analysis_time }}</div>
      <div class="meta-item"><strong>Sheets:</strong> {{ sheet_count }}</div>
    </div>
  </div>

  <!-- Summary Cards -->
  <div class="summary-grid">
    <div class="summary-card">
      <div class="value">{{ total_rows }}</div>
      <div class="label">Total Data Rows</div>
    </div>
    <div class="summary-card">
      <div class="value">{{ total_columns }}</div>
      <div class="label">Total Columns</div>
    </div>
    <div class="summary-card">
      <div class="value">{{ sheet_count }}</div>
      <div class="label">Worksheets</div>
    </div>
    <div class="summary-card quality-score">
      <div class="value">{{ quality_score }}%</div>
      <div class="label">Data Quality Score</div>
    </div>
  </div>

  {% for sheet in sheets %}
  <!-- Sheet: {{ sheet.sheet_name }} -->
  <div class="section">
    <div class="section-header" onclick="toggleSection(this)">
      <h2>Sheet: {{ sheet.sheet_name }} ({{ sheet.row_count }} rows, {{ sheet.col_count }} columns)</h2>
      <span class="toggle">&#9660;</span>
    </div>
    <div class="section-content">

      <!-- Type Distribution -->
      <h3 style="margin-bottom: 8px; font-size: 15px;">Data Type Distribution</h3>
      <div class="type-dist">
        {% for type_name, count in sheet.type_summary.items() %}
        <div class="type-dist-item">
          <span class="type-badge" style="background: {{ type_colors.get(type_name, '#999') }}">{{ type_name }}</span>
          <span class="type-dist-count">{{ count }} col{{ 's' if count != 1 else '' }}</span>
        </div>
        {% endfor %}
      </div>

      {% if sheet.duplicate_rows > 0 or sheet.completely_empty_rows > 0 %}
      <div style="margin-top: 12px; padding: 10px 16px; background: #fff3e0; border-radius: 6px; font-size: 13px;">
        {% if sheet.duplicate_rows > 0 %}
        <span style="color: #e65100;">&#9888; {{ sheet.duplicate_rows }} duplicate row{{ 's' if sheet.duplicate_rows != 1 else '' }} detected.</span>
        {% endif %}
        {% if sheet.completely_empty_rows > 0 %}
        <span style="color: #e65100;">&#9888; {{ sheet.completely_empty_rows }} completely empty row{{ 's' if sheet.completely_empty_rows != 1 else '' }}.</span>
        {% endif %}
      </div>
      {% endif %}

      <!-- Column Analysis Cards -->
      <h3 style="margin: 20px 0 12px; font-size: 15px;">Column Analysis</h3>
      <div class="column-grid">
        {% for col in sheet.columns %}
        <div class="col-card">
          <div class="col-card-header">
            <h3>{{ col.header }}</h3>
            <span class="type-badge" style="background: {{ type_colors.get(col.data_type, '#999') }}">{{ col.data_type }}</span>
          </div>

          <div class="completeness-bar">
            <div class="completeness-fill" style="width: {{ col.completeness }}%; background: {{ '#34a853' if col.completeness >= 90 else '#fbbc04' if col.completeness >= 70 else '#ea4335' }};"></div>
          </div>
          <div style="font-size: 11px; color: var(--text-secondary); margin-bottom: 8px;">
            {{ col.completeness }}% complete ({{ col.non_empty_count }}/{{ col.total_count }})
          </div>

          <div class="stat-row">
            <span class="stat-label">Unique values</span>
            <span class="stat-value">{{ col.unique_count }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Empty cells</span>
            <span class="stat-value">{{ col.empty_count }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Duplicates</span>
            <span class="stat-value">{{ col.duplicate_count }}</span>
          </div>

          {% if col.numeric_stats %}
          <div class="stat-row">
            <span class="stat-label">Min</span>
            <span class="stat-value">{{ col.numeric_stats.min }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Max</span>
            <span class="stat-value">{{ col.numeric_stats.max }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Mean</span>
            <span class="stat-value">{{ col.numeric_stats.mean }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Median</span>
            <span class="stat-value">{{ col.numeric_stats.median }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Std Dev</span>
            <span class="stat-value">{{ col.numeric_stats.std_dev }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Sum</span>
            <span class="stat-value">{{ col.numeric_stats.sum }}</span>
          </div>
          {% if col.numeric_stats.has_outliers %}
          <div class="stat-row" style="color: #ea4335;">
            <span class="stat-label">Outliers</span>
            <span class="stat-value">{{ col.numeric_stats.outlier_count }}</span>
          </div>
          {% endif %}
          {% endif %}

          {% if col.text_stats %}
          <div class="stat-row">
            <span class="stat-label">Min length</span>
            <span class="stat-value">{{ col.text_stats.min_length }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Max length</span>
            <span class="stat-value">{{ col.text_stats.max_length }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Avg length</span>
            <span class="stat-value">{{ col.text_stats.avg_length }}</span>
          </div>
          {% endif %}

          {% if col.boolean_stats %}
          <div class="stat-row">
            <span class="stat-label">True</span>
            <span class="stat-value">{{ col.boolean_stats.true_count }} ({{ col.boolean_stats.true_pct }}%)</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">False</span>
            <span class="stat-value">{{ col.boolean_stats.false_count }}</span>
          </div>
          {% endif %}

          {% if col.date_stats %}
          <div class="stat-row">
            <span class="stat-label">Earliest</span>
            <span class="stat-value">{{ col.date_stats.earliest }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Latest</span>
            <span class="stat-value">{{ col.date_stats.latest }}</span>
          </div>
          {% endif %}

          {% if col.top_values %}
          <div class="top-values">
            <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 4px;">Top Values:</div>
            {% for tv in col.top_values[:5] %}
            <div class="top-value-item">
              <span style="overflow:hidden; text-overflow:ellipsis; max-width: 200px;" title="{{ tv.value }}">{{ tv.value }}</span>
              <span style="color: var(--text-secondary);">{{ tv.count }}</span>
            </div>
            <div class="top-value-bar">
              <div class="top-value-bar-fill" style="width: {{ (tv.count / col.non_empty_count * 100) if col.non_empty_count > 0 else 0 }}%"></div>
            </div>
            {% endfor %}
          </div>
          {% endif %}

        </div>
        {% endfor %}
      </div>

      <!-- Data Preview -->
      {% if sheet.preview_rows %}
      <h3 style="margin: 24px 0 12px; font-size: 15px;">Data Preview (first {{ sheet.preview_rows|length }} rows)</h3>
      <div class="data-table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>#</th>
              {% for h in sheet.headers %}
              <th>{{ h }}</th>
              {% endfor %}
            </tr>
            <tr class="type-row">
              <td></td>
              {% for col in sheet.columns %}
              <td><span class="type-badge" style="background: {{ type_colors.get(col.data_type, '#999') }}; font-size: 10px;">{{ col.data_type }}</span></td>
              {% endfor %}
            </tr>
          </thead>
          <tbody>
            {% for row in sheet.preview_rows %}
            <tr>
              <td style="color: var(--text-secondary);">{{ loop.index }}</td>
              {% for cell in row %}
              <td title="{{ cell }}">{{ cell }}</td>
              {% endfor %}
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
      {% endif %}

    </div>
  </div>
  {% endfor %}

  <div class="report-footer">
    Generated by Excel Import Report System &middot; Task Manager v1.0
  </div>

</div>

<script>
function toggleSection(header) {
  const content = header.nextElementSibling;
  const toggle = header.querySelector('.toggle');
  content.classList.toggle('collapsed');
  toggle.style.transform = content.classList.contains('collapsed') ? 'rotate(-90deg)' : '';
}
</script>
</body>
</html>
"""
)


class HTMLReportGenerator:
    """Generates a professional HTML report from import and analysis results."""

    def __init__(self, preview_rows: int = 20):
        self.preview_rows = preview_rows

    def generate(
        self,
        import_result: ImportResult,
        analysis_result: AnalysisResult,
        output_path: str,
    ) -> str:
        """Generate an HTML report and write it to output_path.

        Args:
            import_result: Data from the importer.
            analysis_result: Statistics from the analyzer.
            output_path: File path for the HTML output.

        Returns:
            The output file path.
        """
        # Build template context
        quality_score = round(analysis_result.overall_quality_score, 1)
        if quality_score >= 80:
            quality_color = "#34a853"
        elif quality_score >= 60:
            quality_color = "#fbbc04"
        else:
            quality_color = "#ea4335"

        sheets_ctx = []
        for sheet_data, sheet_analysis in zip(
            import_result.sheets, analysis_result.sheets
        ):
            cols_ctx = []
            for col_stat in sheet_analysis.column_stats:
                col_dict = col_stat.to_dict()
                cols_ctx.append(col_dict)

            # Preview rows
            preview = []
            for row in sheet_data.rows[: self.preview_rows]:
                preview.append(
                    [
                        html.escape(str(v)) if v is not None else ""
                        for v in row
                    ]
                )

            sheets_ctx.append(
                {
                    "sheet_name": sheet_analysis.sheet_name,
                    "row_count": sheet_analysis.row_count,
                    "col_count": sheet_analysis.col_count,
                    "type_summary": sheet_analysis.type_summary,
                    "duplicate_rows": sheet_analysis.duplicate_rows,
                    "completely_empty_rows": sheet_analysis.completely_empty_rows,
                    "columns": cols_ctx,
                    "headers": sheet_data.headers,
                    "preview_rows": preview,
                }
            )

        rendered = HTML_TEMPLATE.render(
            file_name=import_result.file_name,
            analysis_time=analysis_result.analysis_time,
            sheet_count=len(import_result.sheets),
            total_rows=import_result.total_rows,
            total_columns=import_result.total_columns,
            quality_score=quality_score,
            quality_color=quality_color,
            sheets=sheets_ctx,
            type_colors=TYPE_COLORS,
        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered)

        return output_path

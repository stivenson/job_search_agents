"""Generador de HTML para resultados de búsqueda de empleo."""

import json
from pathlib import Path
from typing import List, Dict
from jinja2 import Template
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import OUTPUT_DIR
from datetime import datetime


class HTMLGenerator:
    """Genera HTML interactivo con resultados de búsqueda."""
    
    def __init__(self):
        self.output_dir = OUTPUT_DIR
        self.template_path = Path(__file__).parent.parent / "templates" / "results_template.html"
    
    def generate(self, matched_jobs: List[Dict], summary: Dict, emails: List[str]) -> str:
        """Genera HTML con los resultados."""
        # Cargar template
        if self.template_path.exists():
            with open(self.template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
        else:
            # Template por defecto si no existe
            template_content = self._get_default_template()
        
        template = Template(template_content)
        
        # Preparar datos para el template
        data = {
            'jobs': matched_jobs,
            'summary': summary,
            'emails': emails,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_jobs': len(matched_jobs),
            'relevant_jobs': len([j for j in matched_jobs if j.get('is_relevant', False)]),
            'jobs_by_source': self._group_by_source(matched_jobs),
            'top_skills': summary.get('top_required_skills', [])
        }
        
        html = template.render(**data)
        return html
    
    def save(self, html: str, filename: str = None) -> Path:
        """Guarda el HTML en un archivo."""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"job_search_results_{timestamp}.html"
        
        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return output_path
    
    def _group_by_source(self, jobs: List[Dict]) -> Dict[str, int]:
        """Agrupa trabajos por fuente."""
        by_source = {}
        for job in jobs:
            source = job.get('source', 'unknown')
            by_source[source] = by_source.get(source, 0) + 1
        return by_source
    
    def _get_default_template(self) -> str:
        """Template HTML por defecto."""
        return """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resultados de Búsqueda de Empleo</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            padding: 20px;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 30px;
        }
        h1 {
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .summary {
            background: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        .summary-item {
            background: white;
            padding: 15px;
            border-radius: 5px;
        }
        .summary-item strong {
            display: block;
            color: #3498db;
            font-size: 24px;
        }
        .filters {
            margin-bottom: 20px;
            padding: 15px;
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .filters label {
            margin-right: 15px;
        }
        .filters select, .filters input {
            padding: 5px 10px;
            margin-right: 10px;
            border: 1px solid #ddd;
            border-radius: 3px;
        }
        .jobs-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        .jobs-table th {
            background: #34495e;
            color: white;
            padding: 12px;
            text-align: left;
        }
        .jobs-table td {
            padding: 12px;
            border-bottom: 1px solid #ddd;
        }
        .jobs-table tr:hover {
            background: #f8f9fa;
        }
        .match-score {
            font-weight: bold;
            padding: 5px 10px;
            border-radius: 3px;
            display: inline-block;
        }
        .score-high { background: #2ecc71; color: white; }
        .score-medium { background: #f39c12; color: white; }
        .score-low { background: #e74c3c; color: white; }
        .email-section {
            margin-top: 40px;
            padding: 20px;
            background: #e8f5e9;
            border-radius: 5px;
        }
        .email-list {
            margin-top: 15px;
        }
        .email-item {
            padding: 8px;
            background: white;
            margin: 5px 0;
            border-radius: 3px;
            display: inline-block;
            margin-right: 10px;
        }
        .email-item a {
            color: #27ae60;
            text-decoration: none;
        }
        .email-item a:hover {
            text-decoration: underline;
        }
        .job-link {
            color: #3498db;
            text-decoration: none;
        }
        .job-link:hover {
            text-decoration: underline;
        }
        .footer {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Resultados de Búsqueda de Empleo</h1>
        <p class="footer">Generado el: {{ generated_at }}</p>
        
        <div class="summary">
            <h2>Resumen Ejecutivo</h2>
            <div class="summary-grid">
                <div class="summary-item">
                    <strong>{{ total_jobs }}</strong>
                    <span>Total de trabajos</span>
                </div>
                <div class="summary-item">
                    <strong>{{ relevant_jobs }}</strong>
                    <span>Trabajos relevantes</span>
                </div>
                <div class="summary-item">
                    <strong>{{ summary.average_score|round(1) }}</strong>
                    <span>Score promedio</span>
                </div>
                <div class="summary-item">
                    <strong>{{ emails|length }}</strong>
                    <span>Emails encontrados</span>
                </div>
            </div>
            
            <h3 style="margin-top: 20px;">Distribución por Fuente</h3>
            <ul>
                {% for source, count in jobs_by_source.items() %}
                <li><strong>{{ source }}</strong>: {{ count }} trabajos</li>
                {% endfor %}
            </ul>
        </div>
        
        <div class="filters">
            <label>Filtrar por fuente:</label>
            <select id="sourceFilter" onchange="filterJobs()">
                <option value="">Todas</option>
                {% for source in jobs_by_source.keys() %}
                <option value="{{ source }}">{{ source }}</option>
                {% endfor %}
            </select>
            
            <label>Score mínimo:</label>
            <input type="number" id="scoreFilter" min="0" max="100" value="60" onchange="filterJobs()">
        </div>
        
        <table class="jobs-table" id="jobsTable">
            <thead>
                <tr>
                    <th>Título</th>
                    <th>Empresa</th>
                    <th>Ubicación</th>
                    <th>Score</th>
                    <th>Fuente</th>
                    <th>Email</th>
                    <th>Link</th>
                </tr>
            </thead>
            <tbody>
                {% for job in jobs %}
                <tr data-source="{{ job.source }}" data-score="{{ job.match_score|int }}">
                    <td><strong>{{ job.title }}</strong></td>
                    <td>{{ job.company }}</td>
                    <td>{{ job.location }}</td>
                    <td>
                        <span class="match-score {% if job.match_score >= 80 %}score-high{% elif job.match_score >= 60 %}score-medium{% else %}score-low{% endif %}">
                            {{ job.match_score|int }}%
                        </span>
                    </td>
                    <td>{{ job.source }}</td>
                    <td>
                        {% if job.application_email %}
                        <a href="mailto:{{ job.application_email }}">{{ job.application_email }}</a>
                        {% else %}
                        -
                        {% endif %}
                    </td>
                    <td>
                        {% if job.url %}
                        <a href="{{ job.url }}" target="_blank" class="job-link">Aplicar →</a>
                        {% else %}
                        -
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        {% if emails %}
        <div class="email-section">
            <h2>📧 Emails de Contacto Encontrados</h2>
            <p>Lista consolidada de emails donde puedes aplicar directamente:</p>
            <div class="email-list">
                {% for email in emails %}
                <span class="email-item">
                    <a href="mailto:{{ email }}">{{ email }}</a>
                </span>
                {% endfor %}
            </div>
        </div>
        {% endif %}
        
        <div class="footer">
            <p>Generado automáticamente por Job Search Agents</p>
        </div>
    </div>
    
    <script>
        function filterJobs() {
            const sourceFilter = document.getElementById('sourceFilter').value;
            const scoreFilter = parseInt(document.getElementById('scoreFilter').value) || 0;
            const rows = document.querySelectorAll('#jobsTable tbody tr');
            
            rows.forEach(row => {
                const source = row.getAttribute('data-source');
                const score = parseInt(row.getAttribute('data-score')) || 0;
                
                const matchSource = !sourceFilter || source === sourceFilter;
                const matchScore = score >= scoreFilter;
                
                row.style.display = (matchSource && matchScore) ? '' : 'none';
            });
        }
    </script>
</body>
</html>"""

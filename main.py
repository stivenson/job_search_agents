"""Punto de entrada principal para el sistema de búsqueda de empleo."""

import asyncio
import logging
import sys
from pathlib import Path

# Agregar directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import LOG_LEVEL, LOG_FILE
from utils.progress_logger import setup_logging, get_progress_logger

# Configurar logging mejorado con Rich
progress_logger = setup_logging(LOG_FILE)

# Configurar nivel de logging desde variables de entorno
log_level_map = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}
log_level = log_level_map.get(LOG_LEVEL.upper(), logging.INFO)
logging.getLogger().setLevel(log_level)

logger = logging.getLogger(__name__)

from agents.orchestrator import JobSearchOrchestrator
from utils.html_generator import HTMLGenerator
from config.settings import OUTPUT_DIR


async def main():
    """Función principal que ejecuta el workflow completo."""
    progress_logger = get_progress_logger()
    
    # Mostrar encabezado bonito
    progress_logger.print_header("Sistema de Búsqueda de Empleo con LangGraph", "🚀")
    
    try:
        # Inicializar orquestador
        progress_logger.print_info("Inicializando orquestador...")
        orchestrator = JobSearchOrchestrator()
        
        # Ejecutar workflow
        progress_logger.print_info("Ejecutando workflow de búsqueda...")
        results = await orchestrator.run()
        
        # Extraer resultados
        matched_jobs = results.get('matched_jobs', [])
        summary = results.get('summary', {})
        emails = results.get('emails', [])
        errors = results.get('errors', [])
        
        # Mostrar resumen en tabla bonita
        summary_data = {
            "Total de trabajos encontrados": len(matched_jobs),
            "Trabajos relevantes (score >= 60)": summary.get('relevant_jobs', 0),
            "Score promedio": f"{summary.get('average_score', 0):.2f}%",
            "Emails encontrados": len(emails),
        }
        progress_logger.print_summary_table(summary_data, "📊 Resumen de Resultados")
        
        if errors:
            progress_logger.print_warning(f"Errores encontrados: {len(errors)}")
            for error in errors:
                progress_logger.print_error(f"  {error}")
        
        # Generar HTML
        progress_logger.print_info("Generando reporte HTML...")
        html_generator = HTMLGenerator()
        html = html_generator.generate(matched_jobs, summary, emails)
        output_path = html_generator.save(html)
        
        progress_logger.print_success(f"Reporte HTML generado exitosamente!")
        progress_logger.print_info(f"Archivo guardado en: {output_path}")
        progress_logger.print_info("Abre el archivo en tu navegador para ver los resultados")
        
        # Mostrar top 5 trabajos en tabla
        if matched_jobs:
            progress_logger.print_jobs_table(matched_jobs, "⭐ Top 5 Trabajos Recomendados", max_rows=5)
        
        # Mostrar emails si hay
        if emails:
            progress_logger.print_emails_list(emails, "📧 Emails de Contacto Encontrados", max_items=10)
        
        progress_logger.print_header("Búsqueda completada exitosamente! 🎉", "✅")
        
        return results
        
    except Exception as e:
        progress_logger.print_error(f"Error crítico en el sistema: {e}")
        logger.error(f"Error crítico en el sistema: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # Ejecutar el workflow
    try:
        results = asyncio.run(main())
        sys.exit(0)
    except KeyboardInterrupt:
        progress_logger = get_progress_logger()
        progress_logger.print_warning("Búsqueda cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        progress_logger = get_progress_logger()
        progress_logger.print_error(f"Error fatal: {e}")
        logger.error(f"Error fatal: {e}", exc_info=True)
        sys.exit(1)

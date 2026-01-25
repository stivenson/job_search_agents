"""Módulo para logging mejorado con Rich - barras de progreso y colores."""

import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TaskID,
    TaskProgressColumn,
    MofNCompleteColumn,
)
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

# Console global para uso en todo el módulo
console = Console()


class ProgressLogger:
    """Logger mejorado con Rich para mostrar progreso visual y colores."""
    
    def __init__(self, log_file: Optional[str] = None):
        """
        Inicializa el ProgressLogger.
        
        Args:
            log_file: Ruta opcional al archivo de log
        """
        self.log_file = log_file
        self.progress: Optional[Progress] = None
        self.tasks: Dict[str, TaskID] = {}
        
        # Configurar logging con Rich
        self._setup_logging()
    
    def _setup_logging(self):
        """Configura el sistema de logging con Rich."""
        # Crear handler de Rich para consola
        rich_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            markup=True,
            rich_tracebacks=True,
            tracebacks_show_locals=False,
        )
        
        # Configurar formato
        rich_handler.setFormatter(
            logging.Formatter("%(message)s", datefmt="[%X]")
        )
        
        # Configurar logger raíz
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Limpiar handlers existentes
        root_logger.handlers.clear()
        
        # Agregar handler de Rich
        root_logger.addHandler(rich_handler)
        
        # Si hay archivo de log, agregar FileHandler también
        if self.log_file:
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            )
            root_logger.addHandler(file_handler)
    
    def start_progress(self, title: str = "Procesando...") -> Progress:
        """Inicia una barra de progreso.
        
        Args:
            title: Título de la barra de progreso
        
        Returns:
            Progress object para control de la barra
        """
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TextColumn("•"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            console=console,
            transient=False,
        )
        self.progress.start()
        return self.progress
    
    def stop_progress(self) -> None:
        """Detiene la barra de progreso."""
        if self.progress:
            self.progress.stop()
            self.progress = None
            self.tasks.clear()
    
    def add_task(self, description: str, total: int = 100) -> TaskID:
        """
        Agrega una tarea a la barra de progreso.
        
        Args:
            description: Descripción de la tarea
            total: Total de items a procesar
            
        Returns:
            TaskID de la tarea creada
        """
        if not self.progress:
            self.start_progress()
        
        task_id = self.progress.add_task(description, total=total)
        self.tasks[description] = task_id
        return task_id
    
    def update_task(self, task_id: TaskID, advance: int = 1, description: Optional[str] = None) -> None:
        """Actualiza una tarea en la barra de progreso.
        
        Args:
            task_id: ID de la tarea
            advance: Cantidad a avanzar
            description: Nueva descripción opcional
        """
        if self.progress:
            self.progress.update(task_id, advance=advance, description=description)
    
    def complete_task(self, task_id: TaskID) -> None:
        """Marca una tarea como completada.
        
        Args:
            task_id: ID de la tarea
        """
        if self.progress:
            self.progress.update(task_id, completed=self.progress.tasks[task_id].total)
    
    def print_header(self, title: str, emoji: str = "🚀"):
        """Imprime un encabezado bonito."""
        console.print()
        console.print(
            Panel(
                f"[bold cyan]{emoji} {title}[/bold cyan]",
                box=box.ROUNDED,
                border_style="cyan",
                padding=(1, 2),
            )
        )
        console.print()
    
    def print_success(self, message: str, emoji: str = "✅"):
        """Imprime un mensaje de éxito."""
        console.print(f"[bold green]{emoji} {message}[/bold green]")
    
    def print_error(self, message: str, emoji: str = "❌"):
        """Imprime un mensaje de error."""
        console.print(f"[bold red]{emoji} {message}[/bold red]")
    
    def print_warning(self, message: str, emoji: str = "⚠️"):
        """Imprime un mensaje de advertencia."""
        console.print(f"[bold yellow]{emoji} {message}[/bold yellow]")
    
    def print_info(self, message: str, emoji: str = "ℹ️"):
        """Imprime un mensaje informativo."""
        console.print(f"[bold blue]{emoji} {message}[/bold blue]")
    
    def print_summary_table(self, data: Dict[str, Any], title: str = "Resumen"):
        """
        Imprime una tabla de resumen.
        
        Args:
            data: Diccionario con los datos a mostrar
            title: Título de la tabla
        """
        table = Table(title=title, box=box.ROUNDED, show_header=True, header_style="bold magenta")
        table.add_column("Métrica", style="cyan", no_wrap=True)
        table.add_column("Valor", style="green", justify="right")
        
        for key, value in data.items():
            table.add_row(key, str(value))
        
        console.print()
        console.print(table)
        console.print()
    
    def print_jobs_table(self, jobs: List[Dict], title: str = "Trabajos Recomendados", max_rows: int = 5):
        """
        Imprime una tabla con trabajos.
        
        Args:
            jobs: Lista de trabajos
            title: Título de la tabla
            max_rows: Número máximo de filas a mostrar
        """
        if not jobs:
            return
        
        table = Table(title=title, box=box.ROUNDED, show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=3)
        table.add_column("Título", style="cyan", no_wrap=False)
        table.add_column("Empresa", style="yellow")
        table.add_column("Score", style="green", justify="right")
        table.add_column("Fuente", style="blue")
        
        for i, job in enumerate(jobs[:max_rows], 1):
            title_text = job.get('title', 'N/A')[:50] + ('...' if len(job.get('title', '')) > 50 else '')
            company = job.get('company', 'N/A')[:30] + ('...' if len(job.get('company', '')) > 30 else '')
            score = f"{job.get('match_score', 0):.1f}%"
            source = job.get('source', 'N/A')
            
            # Color del score según el valor
            if job.get('match_score', 0) >= 80:
                score_style = "[bold green]"
            elif job.get('match_score', 0) >= 60:
                score_style = "[yellow]"
            else:
                score_style = "[dim]"
            
            table.add_row(
                str(i),
                title_text,
                company,
                f"{score_style}{score}[/]",
                source
            )
        
        console.print()
        console.print(table)
        console.print()
    
    def print_emails_list(self, emails: List[str], title: str = "Emails de Contacto", max_items: int = 10):
        """
        Imprime una lista de emails.
        
        Args:
            emails: Lista de emails
            title: Título de la lista
            max_items: Número máximo de items a mostrar
        """
        if not emails:
            return
        
        console.print()
        console.print(f"[bold cyan]{title}[/bold cyan]")
        console.print()
        
        for email in emails[:max_items]:
            console.print(f"  [green]•[/green] {email}")
        
        if len(emails) > max_items:
            console.print(f"  [dim]... y {len(emails) - max_items} más (ver HTML completo)[/dim]")
        
        console.print()


# Instancia global del logger
_progress_logger: Optional[ProgressLogger] = None


def get_progress_logger(log_file: Optional[str] = None) -> ProgressLogger:
    """
    Obtiene o crea la instancia global del ProgressLogger.
    
    Args:
        log_file: Ruta opcional al archivo de log
        
    Returns:
        Instancia de ProgressLogger
    """
    global _progress_logger
    if _progress_logger is None:
        _progress_logger = ProgressLogger(log_file)
    return _progress_logger


def setup_logging(log_file: Optional[str] = None) -> ProgressLogger:
    """
    Configura el sistema de logging con Rich.
    
    Args:
        log_file: Ruta opcional al archivo de log
        
    Returns:
        Instancia de ProgressLogger configurada
    """
    return get_progress_logger(log_file)

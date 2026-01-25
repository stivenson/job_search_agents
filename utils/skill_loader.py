"""Skill loader para cargar y parsear archivos SKILL.md."""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)


class SkillLoader:
    """
    Cargador de skills desde archivos SKILL.md.
    
    Permite cargar prompts y configuración de agentes desde archivos
    SKILL.md con frontmatter YAML, siguiendo el estándar de agent-skills.
    """
    
    def __init__(self, skills_dir: Optional[Path] = None):
        """
        Inicializa el skill loader.
        
        Args:
            skills_dir: Directorio donde se encuentran los skills.
                       Si None, usa job_search_agents/skills/
        """
        if skills_dir is None:
            # Determinar directorio del proyecto
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent
            skills_dir = project_root / "skills"
        
        self.skills_dir = Path(skills_dir)
        self._cache: Dict[str, Dict] = {}
        
        if not self.skills_dir.exists():
            logger.warning(f"Directorio de skills no encontrado: {self.skills_dir}")
    
    def _parse_skill_file(self, skill_path: Path) -> Dict:
        """
        Parsea un archivo SKILL.md.
        
        Args:
            skill_path: Ruta al archivo SKILL.md
        
        Returns:
            Diccionario con metadata y contenido parseado
        """
        if not skill_path.exists():
            raise FileNotFoundError(f"Archivo skill no encontrado: {skill_path}")
        
        content = skill_path.read_text(encoding='utf-8')
        
        # Parsear frontmatter YAML
        frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(frontmatter_pattern, content, re.DOTALL)
        
        if not match:
            raise ValueError(f"Formato inválido en {skill_path}: no se encontró frontmatter YAML")
        
        yaml_content = match.group(1)
        markdown_content = match.group(2)
        
        # Parsear YAML
        try:
            metadata = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise ValueError(f"Error parseando YAML en {skill_path}: {e}")
        
        # Validar campos requeridos
        if 'name' not in metadata:
            raise ValueError(f"Campo 'name' requerido en {skill_path}")
        if 'description' not in metadata:
            raise ValueError(f"Campo 'description' requerido en {skill_path}")
        
        # Parsear contenido markdown
        sections = self._parse_markdown_sections(markdown_content)
        
        return {
            'metadata': metadata,
            'content': markdown_content,
            'sections': sections,
            'path': skill_path
        }
    
    def _parse_markdown_sections(self, markdown: str) -> Dict[str, str]:
        """
        Parsea secciones del contenido markdown.
        
        Args:
            markdown: Contenido markdown
        
        Returns:
            Diccionario con secciones encontradas
        """
        sections = {}
        
        # Buscar secciones ## System Message, ## Human Message Template, etc.
        section_pattern = r'##\s+([^\n]+)\n(.*?)(?=\n##\s+|\Z)'
        matches = re.finditer(section_pattern, markdown, re.DOTALL)
        
        for match in matches:
            section_name = match.group(1).strip().lower().replace(' ', '_')
            section_content = match.group(2).strip()
            sections[section_name] = section_content
        
        return sections
    
    def load_skill(self, skill_name: str, use_cache: bool = True) -> ChatPromptTemplate:
        """
        Carga un skill y retorna un ChatPromptTemplate.
        
        Args:
            skill_name: Nombre del skill (ej: "email-extractor")
            use_cache: Si usar caché de skills cargados
        
        Returns:
            ChatPromptTemplate listo para usar con LangChain
        """
        # Verificar caché
        if use_cache and skill_name in self._cache:
            skill_data = self._cache[skill_name]
        else:
            # Buscar archivo SKILL.md
            skill_path = self.skills_dir / skill_name / "SKILL.md"
            
            if not skill_path.exists():
                raise FileNotFoundError(
                    f"Skill '{skill_name}' no encontrado en {skill_path}. "
                    "Asegúrate de que el archivo SKILL.md existe."
                )
            
            # Parsear archivo
            skill_data = self._parse_skill_file(skill_path)
            
            # Guardar en caché
            if use_cache:
                self._cache[skill_name] = skill_data
        
        # Construir ChatPromptTemplate
        return self._build_prompt_template(skill_data)
    
    def _build_prompt_template(self, skill_data: Dict) -> ChatPromptTemplate:
        """
        Construye un ChatPromptTemplate desde los datos del skill.
        
        Args:
            skill_data: Datos parseados del skill
        
        Returns:
            ChatPromptTemplate
        """
        sections = skill_data['sections']
        messages = []
        
        # System message
        if 'system_message' in sections:
            messages.append(("system", sections['system_message']))
        
        # Human message
        if 'human_message_template' in sections:
            messages.append(("human", sections['human_message_template']))
        elif 'human_message' in sections:
            messages.append(("human", sections['human_message']))
        
        if not messages:
            raise ValueError(
                f"Skill '{skill_data['metadata']['name']}' no tiene mensajes válidos. "
                "Debe contener al menos '## System Message' y '## Human Message Template'"
            )
        
        return ChatPromptTemplate.from_messages(messages)
    
    def get_skill_metadata(self, skill_name: str) -> Dict:
        """
        Obtiene solo los metadatos de un skill sin cargarlo completamente.
        
        Args:
            skill_name: Nombre del skill
        
        Returns:
            Diccionario con metadatos
        """
        if skill_name in self._cache:
            return self._cache[skill_name]['metadata']
        
        skill_path = self.skills_dir / skill_name / "SKILL.md"
        skill_data = self._parse_skill_file(skill_path)
        return skill_data['metadata']
    
    def list_available_skills(self) -> List[Dict]:
        """
        Lista todos los skills disponibles en el directorio.
        
        Returns:
            Lista de diccionarios con información de cada skill
        """
        skills = []
        
        if not self.skills_dir.exists():
            logger.warning(f"Directorio de skills no existe: {self.skills_dir}")
            return skills
        
        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                try:
                    metadata = self.get_skill_metadata(skill_dir.name)
                    skills.append({
                        'name': skill_dir.name,
                        'description': metadata.get('description', ''),
                        'version': metadata.get('version', '1.0.0'),
                        'path': skill_file
                    })
                except Exception as e:
                    logger.warning(f"Error cargando skill {skill_dir.name}: {e}")
        
        return skills
    
    def validate_skill(self, skill_name: str) -> Tuple[bool, Optional[str]]:
        """
        Valida que un skill esté correctamente formateado.
        
        Args:
            skill_name: Nombre del skill
        
        Returns:
            Tupla (es_válido, mensaje_error)
        """
        try:
            skill_path = self.skills_dir / skill_name / "SKILL.md"
            
            if not skill_path.exists():
                return False, f"Archivo no encontrado: {skill_path}"
            
            skill_data = self._parse_skill_file(skill_path)
            
            # Validar que tenga las secciones necesarias
            sections = skill_data['sections']
            if 'system_message' not in sections:
                return False, "Falta sección '## System Message'"
            
            if 'human_message_template' not in sections and 'human_message' not in sections:
                return False, "Falta sección '## Human Message Template' o '## Human Message'"
            
            # Intentar construir el template
            self._build_prompt_template(skill_data)
            
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    def clear_cache(self):
        """Limpia el caché de skills."""
        self._cache.clear()
        logger.debug("Caché de skills limpiado")

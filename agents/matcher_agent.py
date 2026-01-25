"""Agente para matchear trabajos con el perfil del usuario usando embeddings."""

import logging
from typing import List, Dict, Optional
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
import json
import yaml
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import DATA_DIR, LLM_PROVIDER, LLM_MODEL, OPENAI_API_KEY, ANTHROPIC_API_KEY, MIN_MATCH_SCORE

logger = logging.getLogger(__name__)


class MatcherAgent:
    """Agente que calcula el match entre trabajos y perfil del usuario."""
    
    def __init__(self, profile_path: Optional[Path] = None):
        self.profile_path = profile_path or (DATA_DIR / "profile.json")
        self.profile = self._load_profile()
        self.min_score = MIN_MATCH_SCORE
        
        # Cargar configuración de preferencias de idioma
        self.language_prefs = self._load_language_preferences()
        
        # Inicializar embeddings (requiere OpenAI para embeddings)
        if OPENAI_API_KEY:
            self.embeddings = OpenAIEmbeddings()
        else:
            logger.warning("No hay OpenAI API key, usando matching basado en keywords")
            self.embeddings = None
        
        # Inicializar LLM para análisis semántico
        if LLM_PROVIDER == "anthropic" and ANTHROPIC_API_KEY:
            self.llm = ChatAnthropic(
                model=LLM_MODEL if "claude" in LLM_MODEL.lower() else "claude-3-5-sonnet-20241022",
                temperature=0
            )
        elif OPENAI_API_KEY:
            self.llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
        else:
            self.llm = None
    
    def _load_language_preferences(self) -> Dict:
        """Carga preferencias de idioma desde job_sources.yaml."""
        config_path = Path(__file__).parent.parent / "config" / "job_sources.yaml"
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                return config.get('language_preferences', {})
            except Exception as e:
                logger.warning(f"Error cargando preferencias de idioma: {e}")
                return {}
        return {}
    
    def _load_profile(self) -> Dict:
        """Carga el perfil del usuario."""
        if not self.profile_path.exists():
            logger.warning(f"Perfil no encontrado en {self.profile_path}, usando perfil vacío")
            return {}
        
        with open(self.profile_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _extract_skills_from_profile(self) -> List[str]:
        """Extrae lista de skills del perfil."""
        skills = []
        
        # Skills explícitas - manejar tanto diccionario como lista
        skills_data = self.profile.get('skills', {})
        if isinstance(skills_data, dict):
            # Si es un diccionario, iterar sobre categorías
            for category, items in skills_data.items():
                if isinstance(items, list):
                    for item in items:
                        # Extraer tecnologías del texto
                        if isinstance(item, str):
                            techs = self._extract_tech_keywords(item)
                            skills.extend(techs)
                            # También agregar el item directamente si es un string
                            skills.append(item)
                elif isinstance(items, str):
                    # Si el item es un string directo
                    techs = self._extract_tech_keywords(items)
                    skills.extend(techs)
                    skills.append(items)
        elif isinstance(skills_data, list):
            # Si es una lista directa, procesar cada elemento
            for item in skills_data:
                if isinstance(item, str):
                    # Agregar el string directamente como skill
                    skills.append(item)
                    # También extraer tecnologías del texto por si contiene más info
                    techs = self._extract_tech_keywords(item)
                    skills.extend(techs)
                elif isinstance(item, dict):
                    # Si el item es un diccionario, extraer tecnologías
                    techs = self._extract_tech_keywords(str(item))
                    skills.extend(techs)
        
        # Skills de experiencia
        for exp in self.profile.get('experience', []):
            if isinstance(exp, dict):
                skills.extend(exp.get('technologies', []))
            elif isinstance(exp, str):
                # Si experience es una lista de strings, extraer tecnologías
                techs = self._extract_tech_keywords(exp)
                skills.extend(techs)
        
        # Skills de proyectos
        for proj in self.profile.get('projects', []):
            if isinstance(proj, dict):
                skills.extend(proj.get('technologies', []))
        
        return list(set(skills))
    
    def _extract_tech_keywords(self, text: str) -> List[str]:
        """Extrae keywords tecnológicos de un texto."""
        tech_keywords = [
            'Python', 'Django', 'Flask', 'FastAPI', 'Pandas', 'NumPy',
            'TypeScript', 'JavaScript', 'Node.js', 'React', 'Java', 'Spring Boot',
            'AWS', 'GCP', 'ECS', 'Lambda', 'S3', 'DynamoDB', 'CloudFormation',
            'Docker', 'Kubernetes', 'K8s', 'GKE',
            'n8n', 'Jupyter', 'LLM', 'MLOps', 'LLMOps', 'AI', 'Machine Learning',
            'MySQL', 'PostgreSQL', 'MongoDB', 'Redshift',
            'Git', 'GitHub', 'CI/CD', 'Jenkins'
        ]
        
        found = []
        text_lower = text.lower()
        for tech in tech_keywords:
            if tech.lower() in text_lower:
                found.append(tech)
        
        return found
    
    def _calculate_language_score(self, job_text: str, location: str = "") -> Dict:
        """
        Calcula score basado en preferencias de idioma.
        
        - Penaliza trabajos que requieran inglés fluido/nativo
        - Bonifica trabajos en español o regiones LATAM
        - Bonifica trabajos que acepten inglés intermedio
        
        Returns: Dict con score (0-15) y detalles
        """
        score = 7.5  # Score neutral (mitad de 15 puntos)
        details = []
        
        # Combinar texto del trabajo y ubicación para análisis
        full_text = f"{job_text} {location}".lower()
        
        # Obtener keywords de las preferencias
        fluent_required = self.language_prefs.get('fluent_english_required', [])
        acceptable_english = self.language_prefs.get('acceptable_english', [])
        preferred_languages = self.language_prefs.get('preferred_languages', [])
        preferred_regions = self.language_prefs.get('preferred_regions', [])
        
        # 1. Penalizar si requiere inglés fluido (-7.5 puntos)
        requires_fluent = False
        for kw in fluent_required:
            if kw.lower() in full_text:
                requires_fluent = True
                details.append(f"Requiere inglés fluido: '{kw}'")
                break
        
        if requires_fluent:
            score -= 7.5
        
        # 2. Bonus si acepta inglés intermedio (+3 puntos)
        accepts_intermediate = False
        for kw in acceptable_english:
            if kw.lower() in full_text:
                accepts_intermediate = True
                details.append(f"Acepta inglés intermedio: '{kw}'")
                break
        
        if accepts_intermediate:
            score += 3
        
        # 3. Bonus si es en español o menciona español (+5 puntos)
        is_spanish = False
        for kw in preferred_languages:
            if kw.lower() in full_text:
                is_spanish = True
                details.append(f"Trabajo en español: '{kw}'")
                break
        
        if is_spanish:
            score += 5
        
        # 4. Bonus si es región LATAM/España (+2.5 puntos)
        is_latam = False
        for kw in preferred_regions:
            if kw.lower() in full_text:
                is_latam = True
                details.append(f"Región preferida: '{kw}'")
                break
        
        if is_latam:
            score += 2.5
        
        # 5. Bonus si NO se menciona inglés explícitamente (+3 puntos)
        no_english_mentioned = False
        if not requires_fluent and not accepts_intermediate:
            # Verificar que tampoco haya menciones genéricas de inglés
            english_keywords = ['english', 'inglés', 'anglais', 'englisch']
            has_any_english_mention = any(kw in full_text for kw in english_keywords)
            
            if not has_any_english_mention:
                no_english_mentioned = True
                score += 3
                details.append("No menciona requisito de inglés explícitamente")
        
        # Normalizar score entre 0 y 15
        final_score = max(0, min(15, score))
        
        return {
            'score': final_score,
            'requires_fluent_english': requires_fluent,
            'accepts_intermediate': accepts_intermediate,
            'is_spanish': is_spanish,
            'is_latam_region': is_latam,
            'no_english_mentioned': no_english_mentioned,
            'details': details
        }
    
    def calculate_match_score(self, job: Dict) -> float:
        """
        Calcula score de match (0-100) entre un trabajo y el perfil.
        
        Distribución de puntos (total 100):
        - Skills match: 35 puntos
        - Tipo de trabajo: 15 puntos
        - Ubicación: 15 puntos
        - Nivel experiencia: 10 puntos
        - Keywords relevantes: 10 puntos
        - Idioma/Región: 15 puntos (NUEVO)
        """
        score = 0.0
        factors = {}
        
        # Extraer texto del trabajo
        job_text = f"{job.get('title', '')} {job.get('description', '')} {job.get('summary', '')}".lower()
        location = job.get('location', '').lower()
        
        # 1. Match de skills (35 puntos)
        user_skills = [s.lower() for s in self._extract_skills_from_profile()]
        
        matched_skills = []
        for skill in user_skills:
            if skill in job_text:
                matched_skills.append(skill)
        
        skill_score = min(35, (len(matched_skills) / max(len(user_skills), 1)) * 35)
        score += skill_score
        factors['skills_match'] = round(skill_score, 1)
        
        # 2. Tipo de trabajo (15 puntos)
        if any(term in job_text for term in ['part-time', 'part time', 'parttime', 'contract', 'freelance']):
            type_score = 15
        elif 'full-time' in job_text or 'fulltime' in job_text:
            type_score = 4  # Menos preferido pero aceptable
        else:
            type_score = 8  # Neutral
        
        score += type_score
        factors['type_match'] = type_score
        
        # 3. Ubicación (15 puntos)
        if 'remote' in location or 'anywhere' in location or 'work from home' in location:
            location_score = 15
        elif 'occasional travel' in job_text or 'travel occasionally' in job_text:
            location_score = 12
        else:
            location_score = 0
        
        score += location_score
        factors['location_match'] = location_score
        
        # 4. Nivel de experiencia (10 puntos)
        if any(term in job_text for term in ['senior', 'lead', 'principal', 'expert']):
            level_score = 10
        elif 'mid' in job_text or 'intermediate' in job_text:
            level_score = 5
        else:
            level_score = 3
        
        score += level_score
        factors['level_match'] = level_score
        
        # 5. Keywords relevantes (10 puntos)
        relevant_keywords = ['ai', 'machine learning', 'llm', 'llmops', 'mlops', 'python', 'aws', 'gcp']
        keyword_matches = sum(1 for kw in relevant_keywords if kw in job_text)
        keyword_score = min(10, (keyword_matches / len(relevant_keywords)) * 10)
        
        score += keyword_score
        factors['keywords_match'] = round(keyword_score, 1)
        
        # 6. Idioma y Región (15 puntos) - NUEVO
        language_result = self._calculate_language_score(job_text, location)
        language_score = language_result['score']
        
        score += language_score
        factors['language_match'] = round(language_score, 1)
        
        # Guardar información adicional de idioma en el job
        job['language_info'] = {
            'requires_fluent_english': language_result['requires_fluent_english'],
            'accepts_intermediate': language_result['accepts_intermediate'],
            'is_spanish': language_result['is_spanish'],
            'is_latam_region': language_result['is_latam_region'],
            'no_english_mentioned': language_result['no_english_mentioned'],
            'details': language_result['details']
        }
        
        # Guardar factores en el job
        job['match_factors'] = factors
        job['matched_skills'] = matched_skills
        
        return min(100, max(0, score))
    
    def match_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Matchea una lista de trabajos con el perfil."""
        # Recargar perfil si estaba vacío
        if not self.profile:
            self.profile = self._load_profile()
        
        matched_jobs = []
        
        for job in jobs:
            score = self.calculate_match_score(job)
            job['match_score'] = score
            job['is_relevant'] = score >= self.min_score
            
            matched_jobs.append(job)
        
        # Ordenar primero por prioridad de región (1=hispanos, 2=ingleses), luego por score descendente
        matched_jobs.sort(key=lambda x: (
            x.get('region_priority', 999),  # Prioridad de región (menor es mejor, hispanos primero)
            -x.get('match_score', 0)  # Score descendente (negativo para orden descendente)
        ))
        
        return matched_jobs
    
    def get_match_summary(self, jobs: List[Dict]) -> Dict:
        """Genera resumen de matches."""
        total = len(jobs)
        relevant = sum(1 for j in jobs if j.get('is_relevant', False))
        avg_score = sum(j.get('match_score', 0) for j in jobs) / total if total > 0 else 0
        
        # Top skills requeridas
        all_required_skills = []
        for job in jobs[:20]:  # Top 20
            job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
            for skill in self._extract_skills_from_profile():
                if skill.lower() in job_text:
                    all_required_skills.append(skill)
        
        from collections import Counter
        top_skills = [skill for skill, count in Counter(all_required_skills).most_common(10)]
        
        return {
            'total_jobs': total,
            'relevant_jobs': relevant,
            'average_score': round(avg_score, 2),
            'top_required_skills': top_skills
        }

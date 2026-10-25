"""Agente para matchear trabajos con el perfil del usuario usando embeddings."""

import logging
from typing import List, Dict, Optional
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import DATA_DIR, MIN_MATCH_SCORE
from config.config_loader import load_job_sources_config

logger = logging.getLogger(__name__)


class MatcherAgent:
    """Agente que calcula el match entre trabajos y perfil del usuario."""
    
    def __init__(self, profile_path: Optional[Path] = None):
        self.profile_path = profile_path or (DATA_DIR / "profile.json")
        self.profile = self._load_profile()
        self.min_score = MIN_MATCH_SCORE
        
        # Cargar configuración de preferencias de idioma
        self.language_prefs = self._load_language_preferences()
        
        # Cargar configuración de matching
        self.matching_config = self._load_matching_config()
        
        # Inicializar valores por defecto si no hay configuración
        self.scoring_weights = self._get_scoring_weights()
        self.employment_type_terms = self._get_employment_type_terms()
        self.employment_type_scores = self._get_employment_type_scores()
        self.location_terms = self._get_location_terms()
        self.location_scores = self._get_location_scores()
        self.locality_terms = self._get_locality_terms()
        self.experience_level_terms = self._get_experience_level_terms()
        self.experience_level_scores = self._get_experience_level_scores()
        self.relevant_keyword_groups = self._get_relevant_keyword_groups()

        # This matcher currently uses deterministic keyword scoring; avoid
        # constructing unused OpenAI clients when another provider is selected.
        self.embeddings = None
        self.llm = None
    
    def _load_language_preferences(self) -> Dict:
        """Carga preferencias de idioma desde job_sources.yaml."""
        return load_job_sources_config().get('language_preferences', {})
    
    def _load_matching_config(self) -> Dict:
        """Carga configuración de matching desde job_sources.yaml."""
        return load_job_sources_config().get('matching', {})
    
    def _get_scoring_weights(self) -> Dict[str, int]:
        """Obtiene pesos de scoring con valores por defecto."""
        weights = self.matching_config.get('scoring_weights', {})
        return {
            'skills_match': weights.get('skills_match', 35),
            'employment_type': weights.get('employment_type', 15),
            'location': weights.get('location', 15),
            'experience_level': weights.get('experience_level', 10),
            'relevant_keywords': weights.get('relevant_keywords', 10),
            'language_region': weights.get('language_region', 15)
        }
    
    def _get_employment_type_terms(self) -> Dict[str, List[str]]:
        """Obtiene términos de tipo de empleo con valores por defecto."""
        terms = self.matching_config.get('employment_type_terms', {})
        return {
            'full_time': terms.get('full_time', ['full-time', 'fulltime', 'full time', 'permanent']),
            'part_time': terms.get('part_time', ['part-time', 'part time', 'parttime']),
            'contract': terms.get('contract', ['contract', 'contractor', 'contracting']),
            'freelance': terms.get('freelance', ['freelance', 'freelancer', 'freelancing'])
        }
    
    def _get_employment_type_scores(self) -> Dict[str, int]:
        """Obtiene scores de tipo de empleo con valores por defecto."""
        scores = self.matching_config.get('employment_type_scores', {})
        return {
            'full_time': scores.get('full_time', 15),
            'part_time': scores.get('part_time', 4),
            'contract': scores.get('contract', 4),
            'freelance': scores.get('freelance', 4),
            'neutral': scores.get('neutral', 8)
        }
    
    def _get_location_terms(self) -> Dict[str, List[str]]:
        """Obtiene términos de ubicación con valores por defecto."""
        terms = self.matching_config.get('location_terms', {})
        return {
            'remote': terms.get('remote', ['remote', 'anywhere', 'work from home', 'wfh', 'distributed']),
            'occasional_travel': terms.get('occasional_travel', ['occasional travel', 'travel occasionally', 'some travel'])
        }
    
    def _get_location_scores(self) -> Dict[str, int]:
        """Obtiene scores de ubicación con valores por defecto."""
        scores = self.matching_config.get('location_scores', {})
        return {
            'remote': scores.get('remote', 15),
            'occasional_travel': scores.get('occasional_travel', 12),
            'other': scores.get('other', 0)
        }
    
    def _get_locality_terms(self) -> List[str]:
        """Términos locales configurados, sin asumir una ciudad concreta."""
        terms = self.matching_config.get('locality_terms', [])
        return [str(term).casefold() for term in terms if str(term).strip()] if isinstance(terms, list) else []

    def _get_experience_level_terms(self) -> Dict[str, List[str]]:
        """Obtiene términos de nivel de experiencia con valores por defecto."""
        terms = self.matching_config.get('experience_level_terms', {})
        return {
            'senior': terms.get('senior', ['senior', 'lead', 'principal', 'expert', 'staff']),
            'mid': terms.get('mid', ['mid', 'intermediate', 'mid-level']),
            'junior': terms.get('junior', ['junior', 'entry', 'associate'])
        }
    
    def _get_experience_level_scores(self) -> Dict[str, int]:
        """Obtiene scores de nivel de experiencia con valores por defecto."""
        scores = self.matching_config.get('experience_level_scores', {})
        return {
            'senior': scores.get('senior', 10),
            'mid': scores.get('mid', 5),
            'junior': scores.get('junior', 3)
        }
    
    def _get_relevant_keyword_groups(self) -> List[List[str]]:
        """Obtiene grupos configurables de términos para scoring profesional."""
        configured = self.matching_config.get('relevant_keyword_groups', {})
        if isinstance(configured, dict):
            groups = [
                [str(term).casefold() for term in terms if str(term).strip()]
                for terms in configured.values()
                if isinstance(terms, list)
            ]
            groups = [group for group in groups if group]
            if groups:
                return groups

        # Compatibilidad con la configuración anterior de keywords planos.
        legacy_keywords = self.matching_config.get('relevant_keywords', [])
        return [[str(term).casefold()] for term in legacy_keywords if str(term).strip()]
    
    def _load_profile(self) -> Dict:
        """Carga el perfil del usuario."""
        if not self.profile_path.exists():
            logger.debug(f"Perfil aún no parseado en {self.profile_path}; se actualizará desde el CV")
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

        # En CVs PDF el texto de experiencia puede estar disponible sin separar
        # cada empleo; recuperar de allí las tecnologías explícitas.
        experience_text = self.profile.get('experience_text', '')
        if experience_text:
            skills.extend(self._extract_tech_keywords(experience_text))
        
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
    
    def _calculate_employment_type_score(self, job_text: str, max_score: int) -> int:
        """Calcula score de tipo de empleo usando términos configurados."""
        # Verificar full-time
        for term in self.employment_type_terms['full_time']:
            if term in job_text:
                return self.employment_type_scores['full_time']
        
        # Verificar otros tipos
        for emp_type in ['part_time', 'contract', 'freelance']:
            for term in self.employment_type_terms[emp_type]:
                if term in job_text:
                    return self.employment_type_scores[emp_type]
        
        # Neutral si no se encuentra nada
        return self.employment_type_scores['neutral']
    
    def _calculate_location_score(self, location: str, job_text: str, max_score: int) -> int:
        """Calcula score de ubicación usando términos configurados."""
        combined_text = f"{location} {job_text}".casefold()
        hybrid = any(term in combined_text for term in ('híbrido', 'hibrido', 'hybrid', 'presencial y remoto'))

        # Verificar remote
        for term in self.location_terms['remote']:
            if term in combined_text:
                if hybrid:
                    return self.location_scores['occasional_travel']
                return self.location_scores['remote']
        
        # Verificar occasional travel
        for term in self.location_terms['occasional_travel']:
            if term in job_text:
                return self.location_scores['occasional_travel']
        
        # Dar el puntaje local completo solo si se confirma la región objetivo.
        if any(term in location.casefold() for term in self.locality_terms):
            return self.location_scores['other']
        return int(max_score * 0.35)
    
    def _calculate_experience_level_score(self, job_text: str, max_score: int) -> int:
        """Calcula score de nivel de experiencia usando términos configurados."""
        # Verificar senior/lead
        for term in self.experience_level_terms['senior']:
            if term in job_text:
                return self.experience_level_scores['senior']
        
        # Verificar mid-level
        for term in self.experience_level_terms['mid']:
            if term in job_text:
                return self.experience_level_scores['mid']
        
        # Verificar junior
        for term in self.experience_level_terms['junior']:
            if term in job_text:
                return self.experience_level_scores['junior']
        
        # Si no se encuentra, dar un score neutro (30% del máximo)
        return int(max_score * 0.3)
    
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
        
        # 1. Match de skills (usar peso configurado)
        weight_skills = self.scoring_weights['skills_match']
        user_skills = sorted({s.strip().casefold() for s in self._extract_skills_from_profile() if len(s.strip()) >= 3})
        
        matched_skills = []
        for skill in user_skills:
            if skill in job_text:
                matched_skills.append(skill)
        
        # The CV contains many extracted aliases; divide points across a small
        # number of independent matches instead of diluting them across every term.
        skill_score = min(weight_skills, (len(matched_skills) / 3) * weight_skills)
        score += skill_score
        factors['skills_match'] = round(skill_score, 1)
        
        # 2. Tipo de trabajo (usar términos y scores configurados)
        weight_type = self.scoring_weights['employment_type']
        type_score = self._calculate_employment_type_score(job_text, weight_type)
        score += type_score
        factors['type_match'] = type_score
        
        # 3. Ubicación (usar términos y scores configurados)
        weight_location = self.scoring_weights['location']
        location_score = self._calculate_location_score(location, job_text, weight_location)
        score += location_score
        factors['location_match'] = location_score
        
        # 4. Nivel de experiencia (usar términos y scores configurados)
        weight_level = self.scoring_weights['experience_level']
        level_score = self._calculate_experience_level_score(job_text, weight_level)
        score += level_score
        factors['level_match'] = level_score
        
        # 5. Keywords relevantes (usar keywords configurados/inferidos)
        weight_keywords = self.scoring_weights['relevant_keywords']
        keyword_groups = self.relevant_keyword_groups
        keyword_matches = sum(1 for group in keyword_groups if any(term in job_text for term in group))
        keyword_score = min(weight_keywords, (keyword_matches / min(len(keyword_groups), 3)) * weight_keywords) if keyword_groups else 0
        
        score += keyword_score
        factors['keywords_match'] = round(keyword_score, 1)
        
        # 6. Idioma y Región (usar peso configurado)
        weight_language = self.scoring_weights['language_region']
        language_result = self._calculate_language_score(job_text, location)
        # Escalar el score de idioma al peso configurado (actualmente es 0-15)
        language_score = (language_result['score'] / 15.0) * weight_language
        
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
    
    def _get_employment_type_priority(self, job: Dict) -> int:
        """Retorna 0 para full-time, 1 para otros tipos."""
        job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
        if 'full-time' in job_text or 'fulltime' in job_text:
            return 0
        return 1
    
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
        
        # Ordenar por: región (1=hispanos), tipo de trabajo (full-time primero), score descendente
        matched_jobs.sort(key=lambda x: (
            x.get('region_priority', 999),  # Prioridad de región (menor es mejor, hispanos primero)
            self._get_employment_type_priority(x),  # Full-time = 0, otros = 1
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

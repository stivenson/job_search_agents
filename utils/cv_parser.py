"""Parser para extraer información estructurada de CVs en Markdown o PDF."""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional
import sys
from pathlib import Path

# Agregar directorio padre al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import CV_PATH, DATA_DIR


class CVParser:
    """Extrae información estructurada del CV."""
    
    def __init__(self, cv_path: Optional[Path] = None):
        self.cv_path = cv_path or CV_PATH
        self.data_dir = DATA_DIR
        
    def parse(self) -> Dict:
        """Parsea el CV y retorna un diccionario estructurado."""
        if not self.cv_path.exists():
            raise FileNotFoundError(f"CV no encontrado en: {self.cv_path}")

        if self.cv_path.suffix.lower() == ".pdf":
            from pypdf import PdfReader

            reader = PdfReader(str(self.cv_path))
            content = "\n".join(page.extract_text() or "" for page in reader.pages)
            if not content.strip():
                raise ValueError(f"No se pudo extraer texto del CV PDF: {self.cv_path}")
            content = self._normalize_pdf_text(content)
        else:
            with open(self.cv_path, 'r', encoding='utf-8') as f:
                content = f.read()
        
        profile = {
            'personal_info': self._extract_personal_info(content),
            'summary': self._extract_summary(content),
            'experience': self._extract_experience(content),
            'experience_text': self._extract_section_text(content, 'Work Experience'),
            'skills': self._extract_skills(content),
            'education': self._extract_education(content),
            'projects': self._extract_projects(content),
            'certifications': self._extract_certifications(content)
        }
        
        # Guardar perfil en JSON
        profile_path = self.data_dir / "profile.json"
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        
        return profile

    def _normalize_pdf_text(self, content: str) -> str:
        """Normaliza encabezados y viñetas para reutilizar los extractores Markdown."""
        section_names = (
            'Professional Summary', 'Work Experience', 'Skills',
            'Education', 'Projects', 'Certifications'
        )
        normalized_lines = []
        for line in content.replace('\x0c', '\n').replace('\u2022', '- ').splitlines():
            stripped = line.strip()
            if not stripped:
                normalized_lines.append('')
                continue

            heading = next(
                (name for name in section_names if stripped.rstrip(':').casefold() == name.casefold()),
                None
            )
            normalized_lines.append(f'## {heading}' if heading else stripped)

        return '\n'.join(normalized_lines)

    def _extract_section_text(self, content: str, heading: str) -> str:
        """Devuelve el texto de una sección hasta el siguiente encabezado principal."""
        match = re.search(
            rf'^## {re.escape(heading)}\s*$\n(.+?)(?=^## |\Z)',
            content,
            re.MULTILINE | re.DOTALL | re.IGNORECASE
        )
        return match.group(1).strip() if match else ''
    
    def _extract_personal_info(self, content: str) -> Dict:
        """Extrae información personal."""
        info = {}
        
        # Email
        email_match = re.search(r'\*\*Email:\*\*\s*([^\n]+)', content)
        if email_match:
            info['email'] = email_match.group(1).strip()
        
        # Teléfono
        phone_match = re.search(r'(?:Celular|WhatsApp).*?(\+?57\d+)', content)
        if phone_match:
            info['phone'] = phone_match.group(1).strip()
        
        # GitHub
        github_match = re.search(r'(?:Github|GitHub).*?(https?://[^\s\)]+)', content, re.IGNORECASE)
        if github_match:
            info['github'] = github_match.group(1).strip()
        
        # Portfolio
        portfolio_match = re.search(r'(?:Portafolio|Portfolio).*?(https?://[^\s\)]+)', content, re.IGNORECASE)
        if portfolio_match:
            info['portfolio'] = portfolio_match.group(1).strip()
        
        # Nombre
        name_match = re.search(r'^##\s+(.+)$', content, re.MULTILINE)
        if name_match:
            info['name'] = name_match.group(1).strip()
        
        return info
    
    def _extract_summary(self, content: str) -> str:
        """Extrae el resumen profesional."""
        summary_match = re.search(
            r'## Professional Summary\s+(.+?)(?=\n---|\n##)',
            content,
            re.DOTALL
        )
        if summary_match:
            summary = summary_match.group(1).strip()
            # Limpiar markdown bold
            summary = re.sub(r'\*\*(.+?)\*\*', r'\1', summary)
            return summary
        return ""
    
    def _extract_experience(self, content: str) -> List[Dict]:
        """Extrae experiencia laboral."""
        experiences = []
        
        # Buscar sección de experiencia
        exp_section_match = re.search(
            r'## Work Experience\s+(.+?)(?=\n---|\n##)',
            content,
            re.DOTALL
        )
        if not exp_section_match:
            return experiences
        
        exp_section = exp_section_match.group(1)
        
        # Patrón para cada trabajo
        job_pattern = r'### (.+?)\n\*\*(.+?)\*\*\s*\|\s*(.+?)\n\n(.+?)(?=\n### |\n---|\Z)'
        
        for match in re.finditer(job_pattern, exp_section, re.DOTALL):
            company = match.group(1).strip()
            title = match.group(2).strip()
            period = match.group(3).strip()
            description = match.group(4).strip()
            
            # Extraer bullet points
            bullets = re.findall(r'^- (.+)$', description, re.MULTILINE)
            
            # Extraer tecnologías mencionadas
            techs = self._extract_technologies(description)
            
            experiences.append({
                'company': company,
                'title': title,
                'period': period,
                'description': description,
                'bullets': bullets,
                'technologies': techs
            })

        # PDF extraction often flattens headings and bold markup. Recover entries
        # from period lines such as "Marzo 2021 - Julio 2025" as a fallback.
        if not experiences:
            lines = [line.strip() for line in exp_section.splitlines()]
            period_re = re.compile(
                r"^(?:(?:ene(?:ro)?|feb(?:rero)?|mar(?:zo)?|abr(?:il)?|may(?:o)?|jun(?:io)?|"
                r"jul(?:io)?|ago(?:sto)?|sep(?:tiembre)?|oct(?:ubre)?|nov(?:iembre)?|dic(?:iembre)?|"
                r"jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
                r"aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?|actualidad|present)"
                r"\s+)?\d{4}\s*[-–—]\s*(?:(?:[\wáéíóú]+)\s+)?(?:\d{4}|actualidad|present)$",
                re.IGNORECASE,
            )
            period_indexes = [i for i, line in enumerate(lines) if period_re.match(line)]
            for pos, period_index in enumerate(period_indexes):
                before = [line for line in lines[max(0, period_index - 2):period_index] if line]
                if not before:
                    continue
                title = before[-1]
                company = before[-2] if len(before) > 1 else ""
                next_period = period_indexes[pos + 1] if pos + 1 < len(period_indexes) else len(lines)
                # The next role's company/title appear immediately before its date.
                description_end = max(period_index + 1, next_period - 2) if pos + 1 < len(period_indexes) else next_period
                description = "\n".join(lines[period_index + 1:description_end]).strip()
                if not description and pos + 1 < len(period_indexes):
                    description = "\n".join(lines[period_index + 1:next_period]).strip()
                experiences.append({
                    "company": company,
                    "title": title,
                    "period": lines[period_index],
                    "description": description,
                    "bullets": [re.sub(r"^[-*•\s]+", "", line) for line in description.splitlines() if line.strip()],
                    "technologies": self._extract_technologies(description),
                })
        
        return experiences
    
    def _extract_skills(self, content: str) -> Dict[str, List[str]]:
        """Extrae habilidades organizadas por categoría."""
        skills = {}
        
        # Buscar sección de skills
        skills_section_match = re.search(
            r'## Skills\s+(.+?)(?=\n---|\n##)',
            content,
            re.DOTALL
        )
        if not skills_section_match:
            return skills
        
        skills_section = skills_section_match.group(1)
        
        # Extraer por categorías
        category_pattern = r'### (.+?)\n((?:- .+\n?)+)'
        
        for match in re.finditer(category_pattern, skills_section, re.MULTILINE):
            category = match.group(1).strip()
            items_text = match.group(2)
            
            # Extraer items de la lista
            items = re.findall(r'^- (.+)$', items_text, re.MULTILINE)
            
            # Limpiar y extraer tecnologías
            cleaned_items = []
            for item in items:
                # Remover markdown bold
                item = re.sub(r'\*\*(.+?)\*\*', r'\1', item)
                cleaned_items.append(item)
            
            skills[category] = cleaned_items

        # Los PDFs suelen perder los subtítulos y el formato de listas al extraer texto.
        if not skills:
            items = [
                re.sub(r'^[-*•\s]+', '', line).strip()
                for line in skills_section.splitlines()
                if line.strip() and not line.lstrip().startswith('#')
            ]
            if items:
                skills['Skills'] = items
        
        return skills
    
    def _extract_education(self, content: str) -> List[Dict]:
        """Extrae educación."""
        education = []
        
        edu_section_match = re.search(
            r'## Education\s+(.+?)(?=\n---|\n##)',
            content,
            re.DOTALL
        )
        if not edu_section_match:
            return education
        
        edu_section = edu_section_match.group(1)
        
        # Patrón para cada educación
        edu_pattern = r'### (.+?)\n\*\*(.+?)\*\*\s*\|\s*(.+?)(?:\n- (.+))?(?=\n### |\n---|\Z)'
        
        for match in re.finditer(edu_pattern, edu_section, re.DOTALL):
            institution = match.group(1).strip()
            degree = match.group(2).strip()
            period = match.group(3).strip()
            details = match.group(4).strip() if match.group(4) else ""
            
            education.append({
                'institution': institution,
                'degree': degree,
                'period': period,
                'details': details
            })
        
        return education
    
    def _extract_projects(self, content: str) -> List[Dict]:
        """Extrae proyectos."""
        projects = []
        
        proj_section_match = re.search(
            r'## Projects\s+(.+?)(?=\n---|\n##)',
            content,
            re.DOTALL
        )
        if not proj_section_match:
            return projects
        
        proj_section = proj_section_match.group(1)
        
        # Patrón para cada proyecto
        proj_pattern = r'### (.+?)\n\*\*(.+?)\*\*\s*\|\s*(.+?)\n\n(.+?)(?=\n### |\n---|\Z)'
        
        for match in re.finditer(proj_pattern, proj_section, re.DOTALL):
            name = match.group(1).strip()
            context = match.group(2).strip()
            period = match.group(3).strip()
            description = match.group(4).strip()
            
            techs = self._extract_technologies(description)
            
            projects.append({
                'name': name,
                'context': context,
                'period': period,
                'description': description,
                'technologies': techs
            })
        
        return projects
    
    def _extract_certifications(self, content: str) -> List[Dict]:
        """Extrae certificaciones."""
        certifications = []
        
        cert_section_match = re.search(
            r'## Certifications\s+(.+?)(?=\n---|\n##)',
            content,
            re.DOTALL
        )
        if not cert_section_match:
            return certifications
        
        cert_section = cert_section_match.group(1)
        
        # Buscar listas numeradas
        cert_pattern = r'^\d+\.\s+\*\*(.+?)\*\*\s*-\s*(.+)$'
        
        for match in re.finditer(cert_pattern, cert_section, re.MULTILINE):
            name = match.group(1).strip()
            details = match.group(2).strip()
            
            certifications.append({
                'name': name,
                'details': details
            })
        
        return certifications
    
    def _extract_technologies(self, text: str) -> List[str]:
        """Extrae tecnologías mencionadas en un texto."""
        # Tecnologías comunes a buscar
        tech_keywords = [
            'Python', 'Django', 'Flask', 'FastAPI', 'Pandas', 'NumPy',
            'TypeScript', 'JavaScript', 'Node.js', 'React', 'Java', 'Spring Boot',
            'AWS', 'GCP', 'ECS', 'Lambda', 'S3', 'DynamoDB', 'CloudFormation',
            'Docker', 'Kubernetes', 'K8s', 'GKE',
            'n8n', 'Jupyter', 'LLM', 'MLOps', 'LLMOps',
            'MySQL', 'PostgreSQL', 'MongoDB', 'Redshift',
            'Git', 'GitHub', 'CI/CD', 'Jenkins'
        ]
        
        found_techs = []
        text_lower = text.lower()
        
        for tech in tech_keywords:
            if tech.lower() in text_lower:
                found_techs.append(tech)
        
        return found_techs
    
    def get_skills_list(self, profile: Dict) -> List[str]:
        """Obtiene una lista plana de todas las habilidades."""
        skills_list = []
        
        # Manejar skills como diccionario o lista
        skills_data = profile.get('skills', {})
        if isinstance(skills_data, dict):
            # Si es un diccionario, iterar sobre categorías
            for category, items in skills_data.items():
                if isinstance(items, list):
                    for item in items:
                        # Extraer tecnologías del item
                        techs = self._extract_technologies(item)
                        skills_list.extend(techs)
                elif isinstance(items, str):
                    # Si el item es un string directo
                    techs = self._extract_technologies(items)
                    skills_list.extend(techs)
        elif isinstance(skills_data, list):
            # Si es una lista directa, procesar cada elemento
            for item in skills_data:
                if isinstance(item, str):
                    # Agregar el string directamente como skill
                    skills_list.append(item)
                    # También extraer tecnologías del texto por si contiene más info
                    techs = self._extract_technologies(item)
                    skills_list.extend(techs)
                elif isinstance(item, dict):
                    # Si el item es un diccionario, extraer tecnologías
                    techs = self._extract_technologies(str(item))
                    skills_list.extend(techs)
        
        # Agregar tecnologías de experiencia
        for exp in profile.get('experience', []):
            if isinstance(exp, dict):
                skills_list.extend(exp.get('technologies', []))
            elif isinstance(exp, str):
                # Si experience es una lista de strings, extraer tecnologías
                techs = self._extract_technologies(exp)
                skills_list.extend(techs)
        
        # Agregar tecnologías de proyectos
        for proj in profile.get('projects', []):
            if isinstance(proj, dict):
                skills_list.extend(proj.get('technologies', []))
        
        # Remover duplicados y ordenar
        return sorted(list(set(skills_list)))


if __name__ == "__main__":
    parser = CVParser()
    profile = parser.parse()
    print(f"Perfil extraído y guardado en: {DATA_DIR / 'profile.json'}")
    print(f"Total de experiencias: {len(profile['experience'])}")
    print(f"Total de habilidades: {sum(len(v) for v in profile['skills'].values())}")

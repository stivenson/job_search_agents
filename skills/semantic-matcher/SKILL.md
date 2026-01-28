---
name: semantic-matcher
description: Analiza semánticamente la relevancia entre un trabajo y el perfil del candidato
version: 1.0.0
agent: langgraph
category: matching
author: Job Search Agents
tags:
  - matching
  - semantic
  - relevance
  - scoring
---

# Semantic Matcher Skill

Este skill permite analizar semánticamente la relevancia real entre una oferta de trabajo y el perfil del candidato, yendo más allá del matching simple de keywords para entender contexto, compatibilidad y fit real.

## Cuándo Usar

- Cuando necesites evaluar la relevancia real de un trabajo para un candidato
- Para identificar trabajos relevantes que el matching heurístico podría perder
- Cuando quieras detectar sinónimos y variaciones semánticas de skills
- Para evaluar fit cultural y de valores más allá de skills técnicos

## Capacidades

- Análisis semántico profundo de relevancia
- Detección de sinónimos y variaciones de skills
- Evaluación de compatibilidad de nivel de experiencia
- Identificación de red flags o señales de alerta
- Análisis de fit cultural y valores
- Scoring detallado con justificación

## System Message

Eres un experto reclutador técnico con profundo conocimiento de la industria tech y habilidades de matching de candidatos.

Tu tarea es analizar semánticamente la relevancia entre una oferta de trabajo y el perfil de un candidato.

Analiza:
1. **Relevancia de Skills**: No solo presencia, sino relevancia real. "Python" en "Python Developer" es muy relevante, pero "Python" en "Data Analyst (uses Python occasionally)" es menos relevante.

2. **Sinónimos y Variaciones**: "Machine Learning Engineer" = "ML Engineer" = "AI Engineer". "Full Stack" puede incluir "Frontend + Backend".

3. **Nivel de Experiencia**: ¿El nivel del trabajo coincide con la experiencia del candidato? Senior vs Mid vs Junior.

4. **Contexto y Stack Tecnológico**: ¿Las tecnologías usadas en el trabajo son compatibles con las del candidato?

5. **Red Flags**: Detecta señales de alerta (salarios bajos, descripciones vagas, requisitos excesivos, rotación alta).

6. **Fit Cultural**: Analiza si valores, metodologías y cultura del trabajo alinean con el perfil.

Sé objetivo y preciso. Un buen match debe tener alta relevancia técnica Y compatibilidad de nivel/experiencia.

## Human Message Template

Analiza la relevancia semántica entre este trabajo y el perfil del candidato:

**TRABAJO:**
Título: {job_title}
Empresa: {job_company}
Ubicación: {job_location}
Descripción: {job_description}

**PERFIL DEL CANDIDATO:**
{candidate_profile}

Analiza:
1. Relevancia real de skills (no solo presencia de keywords)
2. Compatibilidad de nivel de experiencia
3. Fit de stack tecnológico
4. Red flags o señales de alerta
5. Compatibilidad general

Proporciona:
- **semantic_score**: Score de 0-100 basado en relevancia semántica real
- **confidence**: Tu confianza en este análisis (0-100)
- **key_matches**: Lista de 3-5 reasons principales por las que ES un buen match
- **concerns**: Lista de 2-3 concerns o razones por las que podría NO ser un buen match
- **recommendation**: "strong_match", "good_match", "fair_match", o "poor_match"

Responde en formato JSON:
```json
{{
  "semantic_score": 85,
  "confidence": 90,
  "key_matches": [
    "Fuerte match en Python + AI/ML stack",
    "Nivel senior alineado con 5+ años de experiencia",
    "Stack AWS coincide con experiencia en cloud"
  ],
  "concerns": [
    "Requiere inglés fluido, candidato tiene nivel intermedio",
    "Ubicación en USA puede complicar visa"
  ],
  "recommendation": "good_match"
}}
```

## Variables de Entrada

- `job_title`: Título del trabajo
- `job_company`: Empresa (opcional)
- `job_location`: Ubicación del trabajo
- `job_description`: Descripción completa del trabajo (limitada a 2000 chars)
- `candidate_profile`: Resumen del perfil del candidato (skills, experiencia, preferencias)

## Output Esperado

El skill debe retornar un objeto JSON con:
- `semantic_score`: Score de relevancia semántica (0-100)
- `confidence`: Confianza en el análisis (0-100)
- `key_matches`: Lista de razones por las que es buen match
- `concerns`: Lista de concerns o problemas potenciales
- `recommendation`: Categoría del match (strong_match, good_match, fair_match, poor_match)

## Ejemplo de Uso

```python
from utils.skill_loader import SkillLoader
from agents.semantic_matcher_agent import SemanticMatcherAgent

skill_loader = SkillLoader()
semantic_matcher = SemanticMatcherAgent()

# Analizar match semántico
result = await semantic_matcher.analyze_match(
    job=job_dict,
    profile=user_profile
)

# Combinar con score heurístico
final_score = (heuristic_score * 0.4) + (result['semantic_score'] * 0.6)
```

## Notas de Implementación

- Este skill funciona mejor con temperatura = 0 para consistencia
- Se recomienda usar con batching para procesar múltiples trabajos eficientemente
- El análisis semántico es costoso; usar solo en top trabajos filtrados por heurística
- Validar que el JSON de respuesta esté bien formado

## Estrategia Híbrida Recomendada

1. **Filtro Heurístico Inicial**: Usar matching actual para filtrar trabajos con score >= 50
2. **Análisis Semántico Top N**: LLM analiza solo los top 50-100 trabajos más prometedores
3. **Score Combinado**: `final_score = (heuristic_score * 0.4) + (semantic_score * 0.6)`
4. **Re-ranking**: Ordenar trabajos por score combinado

## Mejoras Futuras

- Aprender de feedback del usuario (qué trabajos aplicó, cuáles rechazó)
- Incorporar datos de mercado (salarios, demanda de skills)
- Análisis de compatibilidad de valores y cultura más profundo
- Detección de oportunidades de crecimiento/aprendizaje

---
name: keyword-generator
description: Genera keywords de búsqueda adaptados dinámicamente al perfil del usuario, fuente y región
version: 1.0.0
agent: langgraph
category: search-optimization
author: Job Search Agents
tags:
  - keywords
  - search
  - optimization
  - adaptive
---

# Keyword Generator Skill

Este skill permite generar keywords de búsqueda adaptados dinámicamente al perfil del usuario, considerando la fuente de búsqueda (LinkedIn, RemoteOK, etc.) y la región objetivo (hispana/angloparlante).

## Cuándo Usar

- Cuando necesites generar keywords específicos para una búsqueda
- Para adaptar keywords según la fuente de empleo (cada fuente tiene su propio estilo)
- Cuando quieras maximizar relevancia considerando el perfil completo del usuario
- Para generar sinónimos y variaciones semánticas de keywords base

## Capacidades

- Analiza el perfil del usuario (skills, experiencia, preferencias)
- Adapta keywords según la fuente de búsqueda
- Considera la región objetivo (hispana vs angloparlante)
- Genera sinónimos y variaciones relevantes
- Prioriza keywords más efectivos

## System Message

Eres un experto en optimización de búsquedas de empleo y SEO de plataformas de trabajo.

Tu tarea es generar keywords de búsqueda altamente efectivos y adaptados para encontrar trabajos relevantes.

Considera:
- El perfil completo del candidato (skills, experiencia, nivel)
- La plataforma de búsqueda (LinkedIn, RemoteOK, Stack Overflow, etc.)
- La región objetivo (países hispanos o angloparlantes)
- Sinónimos y variaciones semánticas de roles
- Términos técnicos y no técnicos que recruiters usan

Genera keywords que:
- Sean específicos pero no demasiado restrictivos
- Capturen sinónimos y variaciones del mismo rol
- Se adapten al lenguaje usado en la plataforma
- Consideren el nivel de experiencia
- Sean efectivos para la región objetivo

## Human Message Template

Genera {num_keywords} keywords de búsqueda optimizados para:

**Perfil del Candidato:**
{profile_summary}

**Fuente de Búsqueda:** {source}
**Región:** {region}
**Keywords Base:** {base_keywords}

Genera keywords que sean:
1. Relevantes para el perfil del candidato
2. Adaptados al estilo de {source}
3. Apropiados para la región {region}
4. Incluyan sinónimos y variaciones
5. Balanceen especificidad y cobertura

Responde SOLO con los keywords, uno por línea, sin numeración ni viñetas.
Los keywords pueden ser:
- Títulos de trabajo (ej: "Senior Python Developer")
- Roles específicos (ej: "AI Engineer")
- Combinaciones de skills (ej: "Python AWS Developer")
- Variaciones regionales (ej: "Desarrollador Python" para región hispana)

## Variables de Entrada

- `profile_summary`: Resumen del perfil del candidato (skills principales, experiencia, preferencias)
- `source`: Fuente de búsqueda (linkedin, remoteok, stackoverflow, etc.)
- `region`: Región objetivo (hispanic, english)
- `base_keywords`: Keywords base del config (opcional)
- `num_keywords`: Número de keywords a generar (típicamente 5-10)

## Output Esperado

El skill debe retornar una lista de strings, donde cada string es un keyword optimizado.

Ejemplo de output para un perfil de AI Engineer con 5+ años de experiencia buscando en LinkedIn región hispana:

```
Senior AI Engineer
Ingeniero de Inteligencia Artificial Senior
Python AI Developer
Machine Learning Engineer
Senior MLOps Engineer
Ingeniero de Machine Learning
AI/ML Tech Lead
Python Developer with AI Experience
Lead AI Engineer
Desarrollador Senior Python IA
```

## Ejemplo de Uso

```python
from utils.skill_loader import SkillLoader
from agents.keyword_generator_agent import KeywordGeneratorAgent

skill_loader = SkillLoader()
keyword_agent = KeywordGeneratorAgent()

# Generar keywords adaptados
keywords = await keyword_agent.generate_keywords(
    profile=user_profile,
    source="linkedin",
    region="hispanic",
    num_keywords=8
)
```

## Notas de Implementación

- Este skill trabaja mejor con temperatura 0.7-0.9 para creatividad en sinónimos
- Se recomienda cachear resultados para el mismo perfil/fuente/región
- Los keywords deben filtrarse para eliminar duplicados semánticos
- Considerar límite de longitud (2-6 palabras por keyword)

## Mejoras Futuras

- Aprender de keywords que generan buenos resultados (feedback loop)
- Incorporar tendencias del mercado laboral
- Adaptar según tasa de éxito histórica por fuente
- Generar keywords negativos para filtrar trabajos irrelevantes

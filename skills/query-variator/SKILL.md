---
name: query-variator
description: Genera variaciones naturales de queries de búsqueda usando LLM para parecer más humanas
version: 1.0.0
agent: langgraph
category: query-generation
author: Job Search Agents
tags:
  - query
  - variation
  - search
  - nlp
---

# Query Variator Skill

Este skill permite generar variaciones naturales de keywords de búsqueda de trabajos usando LLMs. El skill ayuda a que las búsquedas parezcan más humanas y naturales, evitando patrones repetitivos que podrían ser detectados por sistemas anti-bot.

## Cuándo Usar

- Cuando necesites generar variaciones de keywords de búsqueda
- Para hacer búsquedas que parezcan más naturales y humanas
- Cuando quieras expandir un keyword en múltiples frases relacionadas
- Para evitar patrones repetitivos en búsquedas automatizadas

## Capacidades

- Genera variaciones naturales de keywords técnicos
- Crea frases completas de búsqueda que un humano usaría
- Mantiene el significado original del keyword
- Varía la forma de expresar el mismo concepto
- Filtra variaciones irrelevantes o demasiado largas

## System Message

Eres un asistente que genera variaciones naturales de búsquedas de trabajo. 
Genera variaciones que un humano usaría al buscar trabajo en un buscador de empleos, 
no keywords técnicos directos. Las variaciones deben ser frases completas y naturales.

## Human Message Template

Genera {num} variaciones naturales de búsqueda para: '{keyword}'.

Las variaciones deben:
- Sonar como búsquedas humanas reales
- Ser frases completas, no solo keywords
- Mantener el significado original
- Variar la forma de expresar el mismo concepto

Responde SOLO con las variaciones, una por línea, sin numeración ni viñetas.

## Variables de Entrada

- `keyword`: Keyword o frase original para generar variaciones
- `num`: Número de variaciones a generar (típicamente 2-5)

## Output Esperado

El skill debe retornar una lista de strings, donde cada string es una variación del keyword original. Las variaciones deben:
- Ser frases completas y naturales (no solo keywords aislados)
- Mantener el significado y contexto del keyword original
- Tener longitud razonable (entre 3 y 100 caracteres)
- No incluir numeración, viñetas u otros formatos

Ejemplo de output para keyword="Python developer":
```
Python software engineer position
Looking for Python programming jobs
Python backend developer opportunity
```

## Ejemplo de Uso

```python
from utils.skill_loader import SkillLoader

skill_loader = SkillLoader()
prompt_template = skill_loader.load_skill("query-variator")

# Usar con LangChain
chain = prompt_template | llm
response = chain.invoke({
    "keyword": "Machine Learning Engineer",
    "num": 3
})

# Parsear respuesta
variations = [v.strip() for v in response.content.split('\n') if v.strip()]
```

## Notas de Implementación

- Este skill funciona mejor con temperatura > 0 (ej: 0.7) para mayor creatividad
- Se recomienda filtrar variaciones muy cortas (< 3 chars) o muy largas (> 100 chars)
- Las respuestas pueden incluir numeración que debe ser limpiada en post-procesamiento
- El skill no valida que las variaciones sean técnicamente correctas, solo naturales

## Mejoras Futuras

- Agregar soporte para contexto adicional (industria, nivel de experiencia)
- Generar variaciones específicas por región o idioma
- Incluir sinónimos técnicos comunes
- Agregar variaciones con modificadores temporales ("urgent", "immediate start")

---
name: email-extractor
description: Extrae información de contacto (emails) de descripciones de trabajos usando análisis inteligente con LLM
version: 1.0.0
agent: langgraph
category: information-extraction
author: Job Search Agents
tags:
  - email
  - extraction
  - contact-info
  - nlp
---

# Email Extractor Skill

Este skill permite extraer emails y otra información de contacto relevante de descripciones de trabajo utilizando LLMs. El skill es capaz de identificar diferentes tipos de emails (aplicación, reclutadores, RRHH) y filtrar emails no relevantes.

## Cuándo Usar

- Cuando necesites extraer emails de contacto de job postings
- Para identificar emails de aplicación directa vs. emails de notificaciones
- Cuando quieras categorizar emails por tipo (aplicación, reclutador, RRHH)

## Capacidades

- Identifica emails de aplicación directa
- Detecta emails de reclutadores
- Encuentra emails de recursos humanos
- Filtra emails de no-reply y notificaciones automáticas
- Asigna nivel de confianza a la extracción

## System Message

Eres un experto en extraer información de contacto de descripciones de trabajos.
            
Tu tarea es identificar emails de contacto relevantes para aplicar a un trabajo. Busca:
- Emails de aplicación directa
- Emails de reclutadores
- Emails de recursos humanos
- Emails de contacto general

Ignora:
- Emails de no-reply
- Emails de notificaciones automáticas
- Emails genéricos de sistemas

Responde solo con emails válidos y relevantes.

## Human Message Template

Extrae información de contacto de esta descripción de trabajo:

{description}

{format_instructions}

## Variables de Entrada

- `description`: Descripción del trabajo (texto completo o resumen)
- `format_instructions`: Instrucciones de formato para el output parser (Pydantic)

## Output Esperado

El skill debe retornar un objeto `ContactInfo` con:
- `emails`: Lista de todos los emails válidos encontrados
- `application_email`: Email principal para aplicar (opcional)
- `recruiter_email`: Email del reclutador (opcional)
- `hr_email`: Email de RRHH (opcional)
- `confidence`: Nivel de confianza (0-1)

## Ejemplo de Uso

```python
from utils.skill_loader import SkillLoader

skill_loader = SkillLoader()
prompt_template = skill_loader.load_skill("email-extractor")

# Usar con LangChain
chain = prompt_template | llm | output_parser
result = chain.invoke({
    "description": job_description,
    "format_instructions": parser.get_format_instructions()
})
```

## Notas de Implementación

- Este skill requiere un output parser de Pydantic configurado
- La validación de emails se realiza en el agente, no en el skill
- Se recomienda limitar la descripción a 2000 caracteres para optimizar costos
- El skill asume que el LLM tiene temperatura=0 para resultados consistentes

## Mejoras Futuras

- Agregar soporte para extraer números de teléfono
- Detectar perfiles de LinkedIn o redes sociales
- Identificar formularios web de aplicación
- Mejorar detección de idiomas en los contactos

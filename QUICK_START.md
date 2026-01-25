# Guía de Inicio Rápido

## Pasos para ejecutar el sistema

### 1. Instalar dependencias
```bash
cd job_search_agents
pip install -r requirements.txt
playwright install chromium
```

### 2. Configurar variables de entorno
Crea un archivo `.env` en el directorio `job_search_agents`:

```env
# Requerido: Elige un proveedor de LLM
OPENAI_API_KEY=sk-tu-api-key-aqui
# o
ANTHROPIC_API_KEY=sk-tu-api-key-aqui

# Configuración básica
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
```

### 3. Ejecutar
```bash
python main.py
```

### 4. Ver resultados
El sistema generará un archivo HTML en `job_search_agents/results/` con todos los trabajos encontrados.

## Estructura de archivos importantes

- `main.py` - Punto de entrada
- `config/settings.py` - Configuración del sistema
- `config/job_sources.yaml` - Keywords y fuentes de búsqueda
- `CVs_Principales/CV_Dev_Senior_AI_Improvement.md` - CV fuente (debe existir)

## Personalización rápida

### Cambiar keywords de búsqueda
Edita `config/job_sources.yaml`:
```yaml
keywords:
  - "AI Engineer"
  - "Python Senior"
  # Agrega más...
```

### Ajustar score mínimo
En `.env`:
```env
MIN_MATCH_SCORE=70  # Solo trabajos con score >= 70
```

### Habilitar/deshabilitar fuentes
En `config/job_sources.yaml`:
```yaml
job_sources:
  linkedin:
    enabled: true  # o false
```

## Troubleshooting

**Error: "CV no encontrado"**
- Verifica que `CVs_Principales/CV_Dev_Senior_AI_Improvement.md` exista en el directorio padre

**Error: "API key not found"**
- Verifica que tu `.env` tenga `OPENAI_API_KEY` o `ANTHROPIC_API_KEY`

**Error: "Playwright browser not found"**
```bash
playwright install chromium
```

**LinkedIn/Indeed bloqueando requests**
- Aumenta `SCRAPING_DELAY` en `.env` (ej: `SCRAPING_DELAY=5.0`)

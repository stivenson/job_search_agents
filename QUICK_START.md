# Guía de Inicio Rápido

## Pasos para ejecutar el sistema

### 1. Instalar dependencias
```bash
cd job_search_agents
pip install -r requirements.txt
playwright install chromium
```

### 2. Configurar variables de entorno y preferencias locales
Copia `env.example` a `.env` y configura una credencial válida para el proveedor
de LLM elegido. `.env` está excluido de Git.

```env
LLM_PROVIDER=huggingface
HF_TOKEN=tu_token_real
```

Copia `config/local_search.example.yaml` a `config/local_search.yaml` para
personalizar keywords, ubicación y fuentes. El override local está excluido de
Git. Guarda tu CV en `cv/resume.md` (también excluido) o configura `CV_PATH`.

### 3. Ejecutar
```bash
python main.py
```

### 4. Ver resultados
El sistema generará un archivo HTML en `results/` (relativo a la raíz del proyecto) con los trabajos encontrados. Puedes cambiar la ruta con `OUTPUT_DIR` en `.env`.

## Estructura de archivos importantes

- `main.py` - Punto de entrada
- `config/settings.py` - Configuración del sistema
- `config/job_sources.yaml` - Valores públicos predeterminados
- `config/local_search.example.yaml` - Ejemplo de preferencias locales
- `cv/resume.md` - CV fuente (debe existir, configurable via `CV_PATH` en `.env`)

## Personalización rápida

### Cambiar keywords de búsqueda
Edita `config/local_search.yaml`:
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
En `config/local_search.yaml`:
```yaml
job_sources:
  linkedin:
    enabled: true  # o false
```

## Troubleshooting

**Error: "CV no encontrado"**
- Verifica que tu CV exista en la ruta configurada (por defecto `cv/resume.md` dentro del proyecto)

**Error: "API key not found"**
- Verifica que tu `.env` tenga una credencial para el proveedor LLM seleccionado

**Error: "Playwright browser not found"**
```bash
playwright install chromium
```

**LinkedIn/Indeed bloqueando requests**
- Aumenta `SCRAPING_DELAY` en `.env` (ej: `SCRAPING_DELAY=5.0`)

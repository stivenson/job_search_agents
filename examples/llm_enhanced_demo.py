"""
Demo de las nuevas características LLM-Enhanced.

Este script demuestra cómo usar los nuevos agentes de keywords adaptativos
y matching semántico de forma independiente.
"""

import asyncio
import sys
from pathlib import Path

# Agregar directorio padre al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.keyword_generator_agent import KeywordGeneratorAgent
from agents.semantic_matcher_agent import SemanticMatcherAgent


async def demo_keyword_generator():
    """Demo de generación de keywords adaptativos."""
    print("\n" + "="*80)
    print("DEMO: Generación de Keywords Adaptativos")
    print("="*80)
    
    # Perfil de ejemplo
    sample_profile = {
        'skills': {
            'AI/ML': ['Python', 'TensorFlow', 'LLM', 'Machine Learning'],
            'Cloud': ['AWS', 'Docker', 'Kubernetes'],
            'Backend': ['Django', 'FastAPI', 'PostgreSQL']
        },
        'experience': [
            {
                'role': 'Senior AI Engineer',
                'company': 'TechCorp',
                'technologies': ['Python', 'AWS', 'LLM', 'FastAPI']
            },
            {
                'role': 'ML Engineer',
                'company': 'DataCorp',
                'technologies': ['Python', 'TensorFlow', 'GCP']
            }
        ]
    }
    
    # Keywords base del config
    base_keywords = ["AI Engineer", "Python Developer", "MLOps Engineer"]
    
    # Crear agente
    agent = KeywordGeneratorAgent()
    
    # Demo 1: LinkedIn región hispana
    print("\n📍 LinkedIn - Región Hispana:")
    print("-" * 80)
    keywords_linkedin_es = await agent.generate_keywords(
        profile=sample_profile,
        source="linkedin",
        region="hispanic",
        base_keywords=base_keywords,
        num_keywords=6
    )
    for i, kw in enumerate(keywords_linkedin_es, 1):
        print(f"  {i}. {kw}")
    
    # Demo 2: RemoteOK región angloparlante
    print("\n📍 RemoteOK - Región Angloparlante:")
    print("-" * 80)
    keywords_remote_en = await agent.generate_keywords(
        profile=sample_profile,
        source="remoteok",
        region="english",
        base_keywords=base_keywords,
        num_keywords=6
    )
    for i, kw in enumerate(keywords_remote_en, 1):
        print(f"  {i}. {kw}")
    
    # Demo 3: Stack Overflow
    print("\n📍 Stack Overflow:")
    print("-" * 80)
    keywords_so = await agent.generate_keywords(
        profile=sample_profile,
        source="stackoverflow",
        region="english",
        base_keywords=base_keywords,
        num_keywords=6
    )
    for i, kw in enumerate(keywords_so, 1):
        print(f"  {i}. {kw}")
    
    print("\n✅ Demo completado - Keywords adaptativos generados para 3 fuentes\n")


async def demo_semantic_matching():
    """Demo de matching semántico."""
    print("\n" + "="*80)
    print("DEMO: Matching Semántico Inteligente")
    print("="*80)
    
    # Perfil de ejemplo
    sample_profile = {
        'skills': {
            'AI/ML': ['Python', 'TensorFlow', 'LLM', 'Machine Learning'],
            'Cloud': ['AWS', 'Docker'],
        },
        'experience': [
            {
                'role': 'Senior AI Engineer',
                'company': 'TechCorp',
                'technologies': ['Python', 'AWS', 'LLM']
            }
        ]
    }
    
    # Trabajos de ejemplo
    jobs = [
        {
            'title': 'Senior AI/ML Engineer',
            'company': 'AI Startup',
            'location': 'Remote',
            'description': '''
            We are seeking a Senior AI/ML Engineer with 5+ years of experience in Python,
            TensorFlow, and LLM development. Strong AWS experience required.
            You will lead our AI team and build cutting-edge ML solutions.
            Fluent English required.
            '''
        },
        {
            'title': 'Python Developer',
            'company': 'General Tech Co',
            'location': 'New York',
            'description': '''
            Looking for a Python developer for web development.
            Django and Flask experience needed. Basic ML knowledge is a plus.
            Entry-level position.
            '''
        },
        {
            'title': 'Ingeniero de IA Senior',
            'company': 'TechLatam',
            'location': 'Colombia',
            'description': '''
            Buscamos Ingeniero de IA Senior con experiencia en Python, Machine Learning y LLMs.
            Trabajarás en proyectos innovadores de IA generativa.
            Inglés intermedio suficiente. Remoto desde LATAM.
            '''
        }
    ]
    
    # Crear agente
    agent = SemanticMatcherAgent()
    
    print("\nAnalizando 3 trabajos semánticamente...")
    print("-" * 80)
    
    # Analizar cada trabajo
    for i, job in enumerate(jobs, 1):
        print(f"\n🔍 Trabajo {i}: {job['title']} @ {job['company']}")
        print(f"   Ubicación: {job['location']}")
        
        result = await agent.analyze_match(job, sample_profile)
        
        print(f"\n   📊 Score Semántico: {result['semantic_score']}/100")
        print(f"   🎯 Confianza: {result['confidence']}/100")
        print(f"   ✅ Recomendación: {result['recommendation']}")
        
        if result['key_matches']:
            print(f"\n   ✅ Matches Clave:")
            for match in result['key_matches'][:3]:
                print(f"      • {match}")
        
        if result['concerns']:
            print(f"\n   ⚠️  Concerns:")
            for concern in result['concerns'][:3]:
                print(f"      • {concern}")
        
        print()
    
    print("="*80)
    print("✅ Demo completado - Análisis semántico de 3 trabajos")
    print("="*80)


async def demo_hybrid_approach():
    """Demo del enfoque híbrido: heurístico + semántico."""
    print("\n" + "="*80)
    print("DEMO: Enfoque Híbrido (Heurístico + Semántico)")
    print("="*80)
    
    # Simular scores
    jobs_with_scores = [
        {"title": "Senior AI Engineer", "heuristic_score": 85, "semantic_score": 92},
        {"title": "Python Developer", "heuristic_score": 70, "semantic_score": 65},
        {"title": "ML Engineer", "heuristic_score": 60, "semantic_score": 88},
        {"title": "Data Analyst", "heuristic_score": 45, "semantic_score": 0},  # No analizado
    ]
    
    agent = SemanticMatcherAgent()
    
    print("\nCombinando scores (40% heurístico + 60% semántico):")
    print("-" * 80)
    
    for job in jobs_with_scores:
        combined = agent.combine_scores(
            job['heuristic_score'],
            job['semantic_score'],
            heuristic_weight=0.4,
            semantic_weight=0.6
        )
        
        print(f"\n{job['title']}:")
        print(f"  Heurístico: {job['heuristic_score']}/100 (40%)")
        print(f"  Semántico:  {job['semantic_score']}/100 (60%)")
        print(f"  COMBINADO:  {combined:.1f}/100")
    
    print("\n✅ Demo completado - Scores combinados calculados\n")


async def main():
    """Ejecuta todos los demos."""
    print("\n" + "="*80)
    print("🚀 DEMO: LLM-Enhanced Search Features")
    print("="*80)
    print("\nEste demo muestra las nuevas características basadas en LLM.")
    print("NOTA: Requiere configurar API keys en .env")
    print("="*80)
    
    try:
        # Demo 1: Keywords adaptativos
        await demo_keyword_generator()
        
        # Demo 2: Matching semántico
        await demo_semantic_matching()
        
        # Demo 3: Enfoque híbrido
        await demo_hybrid_approach()
        
        print("\n" + "="*80)
        print("✅ TODOS LOS DEMOS COMPLETADOS")
        print("="*80)
        print("\n💡 Para usar en producción:")
        print("   1. Configurar .env con tus API keys")
        print("   2. Habilitar USE_ADAPTIVE_KEYWORDS=true")
        print("   3. Habilitar USE_SEMANTIC_MATCHING=true")
        print("   4. Ejecutar: python main.py")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error en demo: {e}")
        print("Verifica que:")
        print("  - Tienes API keys configuradas en .env")
        print("  - El modelo LLM está disponible")
        print("  - Los skills están en skills/")


if __name__ == "__main__":
    asyncio.run(main())

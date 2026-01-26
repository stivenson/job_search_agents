"""Script de validación para verificar que los skills se cargan correctamente."""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from utils.skill_loader import SkillLoader


def validate_email_extractor_skill():
    """Valida el skill email-extractor."""
    print("\n=== Validando skill email-extractor ===")
    try:
        skill_loader = SkillLoader()
        
        # Validar skill
        is_valid, error = skill_loader.validate_skill("email-extractor")
        
        if is_valid:
            print("✓ Skill email-extractor es válido")
            
            # Intentar cargar
            prompt = skill_loader.load_skill("email-extractor")
            print(f"✓ Skill cargado correctamente: {type(prompt)}")
            
            # Verificar variables
            messages = prompt.messages
            print(f"✓ Tiene {len(messages)} mensajes (system y human)")
            
            # Verificar que las variables están en el template
            human_msg = str(messages[1].prompt.template) if len(messages) > 1 else ""
            if "{description}" in human_msg and "{format_instructions}" in human_msg:
                print("✓ Variables {description} y {format_instructions} encontradas")
            else:
                print("✗ Variables esperadas no encontradas en el template")
                return False
            
            return True
        else:
            print(f"✗ Skill email-extractor inválido: {error}")
            return False
            
    except Exception as e:
        print(f"✗ Error validando email-extractor: {e}")
        return False


def validate_query_variator_skill():
    """Valida el skill query-variator."""
    print("\n=== Validando skill query-variator ===")
    try:
        skill_loader = SkillLoader()
        
        # Validar skill
        is_valid, error = skill_loader.validate_skill("query-variator")
        
        if is_valid:
            print("✓ Skill query-variator es válido")
            
            # Intentar cargar
            prompt = skill_loader.load_skill("query-variator")
            print(f"✓ Skill cargado correctamente: {type(prompt)}")
            
            # Verificar variables
            messages = prompt.messages
            print(f"✓ Tiene {len(messages)} mensajes (system y human)")
            
            # Verificar que las variables están en el template
            human_msg = str(messages[1].prompt.template) if len(messages) > 1 else ""
            if "{keyword}" in human_msg and "{num}" in human_msg:
                print("✓ Variables {keyword} y {num} encontradas")
            else:
                print("✗ Variables esperadas no encontradas en el template")
                return False
            
            return True
        else:
            print(f"✗ Skill query-variator inválido: {error}")
            return False
            
    except Exception as e:
        print(f"✗ Error validando query-variator: {e}")
        return False


def list_all_skills():
    """Lista todos los skills disponibles."""
    print("\n=== Listando todos los skills disponibles ===")
    try:
        skill_loader = SkillLoader()
        skills = skill_loader.list_available_skills()
        
        if skills:
            print(f"✓ Se encontraron {len(skills)} skills:")
            for skill in skills:
                print(f"  - {skill['name']}: {skill['description']}")
            return True
        else:
            print("✗ No se encontraron skills")
            return False
            
    except Exception as e:
        print(f"✗ Error listando skills: {e}")
        return False


def main():
    """Ejecuta todas las validaciones."""
    print("=" * 60)
    print("VALIDACIÓN DE SKILLS")
    print("=" * 60)
    
    results = []
    
    # Listar skills
    results.append(list_all_skills())
    
    # Validar email-extractor
    results.append(validate_email_extractor_skill())
    
    # Validar query-variator
    results.append(validate_query_variator_skill())
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Validaciones exitosas: {passed}/{total}")
    
    if passed == total:
        print("✓ Todos los skills están correctamente implementados")
        return 0
    else:
        print("✗ Algunas validaciones fallaron")
        return 1


if __name__ == "__main__":
    sys.exit(main())

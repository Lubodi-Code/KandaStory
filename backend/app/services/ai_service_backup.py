from app.core.config import settings
from openai import OpenAI
from typing import List, Dict, Any, Optional

client = OpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_PROMPT_ES = (
    "Eres un narrador invisible especializado en historias colaborativas. Escribe en tercera persona, sin decir 'Narrador' ni referirte a ti mismo.\n\n"
    "REGLAS FUNDAMENTALES (OBLIGATORIAS):\n"
    "1. PERSONAJES: Usar ÚNICAMENTE los personajes proporcionados como protagonistas. NO inventar nuevos protagonistas.\n"
    "2. CONTINUIDAD: Mantener ESTRICTA continuidad con capítulos previos. No ignorar eventos o personajes establecidos.\n"
    "3. CONSISTENCIA: Los personajes deben mantener sus personalidades, habilidades y trasfondos establecidos.\n"
    "4. CONSECUENCIAS: Todas las acciones deben tener consecuencias lógicas y coherentes con el mundo.\n"
    "5. PROGRESIÓN: Cada capítulo debe avanzar la narrativa principal sin desviarse a subtramas irrelevantes.\n\n"
    "ESTRUCTURA NARRATIVA:\n"
    "- Integrar personajes por nombre y rasgos distintivos de forma natural en la acción.\n"
    "- Evaluar acciones de jugadores con consecuencias claras (éxito/fallo/costo).\n"
    "- Mantener tono inmersivo, descriptivo y dinámico.\n"
    "- Longitud: 500–800 palabras en español natural.\n"
    "- Terminar con micro-cliffhanger (excepto capítulo final).\n\n"
    "PROHIBICIONES:\n"
    "- No usar listas, viñetas o encabezados en la narrativa.\n"
    "- No incluir JSON, etiquetas o metacomentarios.\n"
    "- No crear nuevos personajes principales sin autorización.\n"
    "- No contradecir eventos ya establecidos.\n\n"
    "SALIDA: Únicamente el texto narrativo del capítulo, sin prefijos ni explicaciones adicionales."
)

def _characters_json(characters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Procesa y estructura los datos de personajes para la IA"""
    out = []
    for ch_data in characters or []:
        # Manejar estructura anidada o directa
        ch = ch_data.get('character', ch_data)
        out.append({
            "id": str(ch.get("_id") or ch.get("id") or ch.get("character_id") or ""),
            "name": ch.get("name") or ch.get("character_name") or "",
            "background": ch.get("background") or "",
            "beliefs": ch.get("beliefs") or "",
            "physical": [
                {"name": t.get("name", ""), "description": t.get("description", "")}
                for t in (ch.get("physical") or [])
            ],
            "mental": [
                {"name": t.get("name", ""), "description": t.get("description", "")}
                for t in (ch.get("mental") or [])
            ],
            "skills": [
                {"name": t.get("name", ""), "description": t.get("description", "")}
                for t in (ch.get("skills") or [])
            ],
            "flaws": [
                {"name": t.get("name", ""), "description": t.get("description", "")}
                for t in (ch.get("flaws") or [])
            ],
        })
    return out

def _previous_chapters_compact(previous_chapters: List[str]) -> List[str]:
    """Compacta capítulos previos para economizar tokens"""
    compact = []
    for i, ch in enumerate(previous_chapters or [], 1):
        text = (ch or "").strip().replace("\n", " ")
        # Mantener más contexto para los últimos capítulos
        max_length = 400 if i >= len(previous_chapters) - 1 else 250
        compact.append(f"Cap.{i}: {text[:max_length]}{'...' if len(text) > max_length else ''}")
    return compact

def _player_actions_json(actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for a in actions or []:
        out.append({
            "user_id": str(a.get("user_id") or ""),
            "username": a.get("username") or "",
            "character_id": str(a.get("character_id") or ""),
            "character_name": a.get("character_name") or "",
            "action": a.get("action") or "",
        })
    return out


class AIService:
    """Servicio de IA para generar capítulos y evaluar personajes"""

    async def generate_first_chapter(self, world: Dict[str, Any], characters: List[Dict[str, Any]]) -> str:
        """Genera el primer capítulo usando la plantilla solicitada (sin voz de narrador)."""

        characters_json = _characters_json(characters)
        prompt = (
            "Plantilla: Primer capítulo (con personajes)\n"
            "Uso: generate_first_chapter(world, characters)\n\n"
            f"Contexto del mundo: {world.get('summary','')} Lógica del mundo: {world.get('logic','')} "
            f"Período: {world.get('time_period','')} • Escenario: {world.get('space_setting','')}\n\n"
            f"Personajes seleccionados (JSON): {characters_json}\n\n"
            "Asegúrate de presentar a cada personaje por nombre y rasgos únicos (físicos, mentales, habilidades, defectos) integrados en la acción, no como ficha.\n\n"
            "Objetivo de este capítulo:\n\n"
            "Establecer el escenario, el conflicto inicial y presentar a todos los personajes seleccionados en situación activa.\n"
            "Estilo: tercera persona, inmersivo, sin voz de narrador.\n"
            "Longitud: 500–800 palabras.\n"
            "Cerrar con un micro-cliffhanger.\n\n"
            "Salida: Devuelve únicamente el texto del capítulo en español."
        )

        try:
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_ES},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1400,
                temperature=0.8,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception as e:
            print(f"Error generating first chapter: {e}")
            return (
                "Una brisa tensa recorre el escenario mientras las miradas se cruzan; algo está a punto de ocurrir…"
            )

    async def _generate_chapter(
        self,
        world: Dict[str, Any],
        previous_chapters: List[str],
        characters: List[Dict[str, Any]],
        total_chapters: int,
        chapter_index: int,
        player_actions: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Método unificado para generar capítulos, con o sin acciones de jugadores."""

        characters_json = _characters_json(characters)
        prev_compact = _previous_chapters_compact(previous_chapters)
        
        # Calcular puntos narrativos dinámicos basados en total_chapters
        climax_chapter = max(2, round(total_chapters * 0.7)) if total_chapters > 2 else total_chapters - 1
        mid_point = max(2, round(total_chapters * 0.5)) if total_chapters > 3 else 2

        # Determinar fase narrativa con instrucciones MÁS ESPECÍFICAS
        if chapter_index == 1:
            narrative_phase = (
                "FASE: ESTABLECIMIENTO (Capítulo Inicial).\n"
                "OBJETIVO: Presentar a TODOS los personajes proporcionados en acción. Establecer el conflicto principal. "
                "Crear tensión inicial que justifique la aventura. Mostrar las personalidades y habilidades de cada personaje."
            )
        elif chapter_index == total_chapters:
            narrative_phase = (
                f"FASE: RESOLUCIÓN DEFINITIVA (Capítulo Final {chapter_index}/{total_chapters}).\n"
                "OBJETIVO CRÍTICO: Este es el ÚLTIMO capítulo. DEBES proporcionar una conclusión COMPLETA y SATISFACTORIA. "
                "Resuelve el conflicto principal establecido en capítulos anteriores. NO introduzcas nuevos conflictos mayores. "
                "Muestra las consecuencias finales de todas las decisiones tomadas. Proporciona un epílogo que cierre la historia. "
                "El capítulo DEBE terminar con 'FIN.' en una línea separada."
            )
        elif chapter_index == climax_chapter:
            narrative_phase = (
                f"FASE: CLÍMAX (Capítulo {chapter_index}/{total_chapters}).\n"
                "OBJETIVO: Punto de máxima tensión. El conflicto principal debe alcanzar su momento más intenso. "
                "Las acciones de los personajes aquí son CRUCIALES y deben tener consecuencias definitivas. "
                "Prepara la resolución para el(los) capítulo(s) final(es)."
            )
        elif chapter_index >= mid_point:
            narrative_phase = (
                f"FASE: ESCALADA (Capítulo {chapter_index}/{total_chapters}).\n"
                "OBJETIVO: Intensificar el conflicto establecido. Complicar la situación para los personajes. "
                "Añadir obstáculos que requieran usar sus habilidades únicas. Crear tensión creciente hacia el clímax."
            )
        else:
            narrative_phase = (
                f"FASE: DESARROLLO (Capítulo {chapter_index}/{total_chapters}).\n"
                "OBJETIVO: Desarrollar el conflicto establecido. Continuar DIRECTAMENTE desde los eventos del capítulo anterior. "
                "Mantener a los MISMOS personajes activos. Avanzar la trama sin desviarse a historias secundarias."
            )

        # Instrucciones de cierre específicas
        is_last = (chapter_index == total_chapters)
        close_instr = (
            "FINAL DEL CAPÍTULO: " +
            ("Cierra la historia COMPLETAMENTE. No uses cliffhanger. Termina con 'FIN.' en línea separada." 
             if is_last else "Termina con un micro-cliffhanger que genere expectación para el siguiente capítulo.")
        )

        # Construcción del prompt reforzado
        prompt_sections = [
            f"=== GENERACIÓN DE CAPÍTULO {chapter_index}/{total_chapters} ===\n",
            
            f"📖 {narrative_phase}\n",
            
            "🛡️ REGLA FUNDAMENTAL: Esta historia DEBE centrarse exclusivamente en los siguientes personajes. "
            "NO inventes nuevos protagonistas. Mantén coherencia absoluta con eventos previos.\n",
            
            f"🌍 MUNDO: {world.get('summary', '')} | LÓGICA: {world.get('logic', '')} | "
            f"ÉPOCA: {world.get('time_period', '')} | ESCENARIO: {world.get('space_setting', '')}\n",
            
            f"👥 PERSONAJES PROTAGONISTAS (usar TODOS): {characters_json}\n",
            
            f"📚 CONTEXTO PREVIO: {prev_compact}\n" if prev_compact else "📚 CONTEXTO: Este es el primer capítulo.\n",
        ]

        if player_actions:
            actions_json = _player_actions_json(player_actions)
            prompt_sections.extend([
                f"⚔️ ACCIONES DE JUGADORES A INTEGRAR: {actions_json}\n",
                "INSTRUCCIÓN: Para cada acción, evalúa si tiene éxito, falla parcialmente o tiene un costo inesperado. "
                "Muestra las consecuencias EN LA NARRATIVA, no las expliques.\n"
            ])
        else:
            prompt_sections.append(
                "⚔️ SIN ACCIONES: Continúa la historia naturalmente. Mantén a los personajes activos y sus motivaciones presentes.\n"
            )

        prompt_sections.extend([
            "📋 INSTRUCCIONES ESPECÍFICAS:",
            "1. CONTINUIDAD: Mantén coherencia total con capítulos previos y personajes establecidos.",
            f"2. NARRATIVA: Sigue exactamente la fase '{narrative_phase.split(':')[1].split('.')[0].strip()}'.",
            "3. PERSONAJES: Integra a TODOS los personajes proporcionados de forma significativa.",
            "4. ACCIONES: Si hay acciones de jugadores, intégralas con consecuencias claras y realistas.",
            f"5. CIERRE: {close_instr}",
            "6. ESTILO: Tercera persona, inmersivo, descriptivo. 500-800 palabras en español.",
            "7. FORMATO: Solo narrativa, sin listas ni elementos técnicos.\n",
            
            "📝 GENERA EL CAPÍTULO:"
        ])
        
        prompt = "\n".join(prompt_sections)

        try:
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_ES},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1500,
                temperature=0.8,
            )
            content = (response.choices[0].message.content or "").strip()
            
            # Asegurar que el capítulo final termine correctamente
            if is_last and not content.strip().endswith("FIN."):
                content += "\n\nFIN."
                
            return content
        except Exception as e:
            print(f"Error generating chapter: {e}")
            return "La historia continúa desarrollándose con tensión creciente mientras los destinos se entrelazan..."

    async def generate_chapter_with_actions(
        self, 
        world: Dict[str, Any], 
        previous_chapters: List[str], 
        player_actions: List[Dict[str, Any]], 
        characters: List[Dict[str, Any]],
        total_chapters: int,
        chapter_index: int
    ) -> str:
        """Genera un capítulo incorporando acciones de jugadores."""
        return await self._generate_chapter(
            world, previous_chapters, characters, total_chapters, chapter_index, player_actions
        )

        # Determinar fase narrativa con instrucciones MÁS FUERTES
        if chapter_index == 1:
            narrative_phase = "FASE: INICIO. Tu objetivo es establecer el conflicto principal, presentar a los personajes proporcionados y crear tensión inicial."
        elif chapter_index == total_chapters:
            # Instrucción clave para la conclusión
            narrative_phase = (
                "FASE: CLÍMAX Y CONCLUSIÓN. Este es el ÚLTIMO capítulo. "
                "DEBES dar una conclusión satisfactoria a la trama principal presentada en los capítulos anteriores. "
                "Resuelve el conflicto central. No introduzcas nuevos personajes o conflictos importantes. "
                "Proporciona un cierre definitivo y un breve epílogo que muestre las consecuencias de las acciones de los personajes."
            )
        elif chapter_index == total_chapters - 1 and total_chapters > 2:
            narrative_phase = (
                "FASE: PREPARACIÓN PARA EL CLÍMAX. Este es el penúltimo capítulo. "
                "Aumenta la tensión del conflicto principal al máximo. "
                "Lleva a los personajes a un punto de no retorno y prepara el escenario para la confrontación final del siguiente capítulo."
            )
        else:
            narrative_phase = (
                f"FASE: DESARROLLO. Estamos en el capítulo {chapter_index} de {total_chapters}. "
                "Continúa DIRECTAMENTE desde el final del capítulo anterior. "
                "Utiliza los MISMOS personajes y avanza el conflicto ya establecido. "
                "No introduzcas una nueva historia; desarrolla la existente."
            )

        # Instrucciones de cierre reforzadas
        is_last = (chapter_index == total_chapters)
        close_instr = (
            "500–800 palabras. "
            + ("NO uses un cliffhanger. Cierra la historia por completo, ya que es el final.\n\n" 
               if is_last else "Termina con un micro-cliffhanger que cree expectación para el siguiente capítulo.\n\n")
        )

        prompt = (
            "Plantilla: Siguiente capítulo CON acciones\n"
            "Uso: generate_chapter_with_actions(world, previous_chapters, player_actions, characters)\n\n"
            f"ESTRUCTURA NARRATIVA ({chapter_index}/{total_chapters}): {narrative_phase}\n\n"
            f"Contexto del mundo: {world.get('summary','')} Reglas/tono del mundo: {world.get('logic','')}\n\n"
            f"Resumen breve de lo ocurrido hasta ahora (capítulos previos): {prev_compact}\n\n"
            f"Acciones sugeridas por jugadores (JSON): {actions_json}\n\n"
            "Para cada acción, decide si tiene éxito, falla o tiene un costo, y refleja la consecuencia en la escena.\n"
            "No digas ‘esta acción fue aceptada’; muéstralo en la narrativa.\n\n"
            f"Personajes seleccionados (JSON): {characters_json}\n\n"
            "Instrucciones Clave:\n\n"
            "1. Mantén una estricta continuidad con los capítulos previos y los personajes. No los ignores.\n"
            "2. Sigue rigurosamente las indicaciones de la FASE NARRATIVA actual.\n"
            "3. Para cada acción, decide si tiene éxito, falla o tiene un costo, y refleja la consecuencia en la narrativa.\n"
            "4. No digas 'esta acción fue aceptada'; muéstralo en la narrativa.\n"
            f"5. {close_instr}"
            "6. Estilo: tercera persona, inmersivo, sin voz de narrador.\n\n"
            "Salida: Únicamente el texto del capítulo en español."
        )

        try:
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_ES},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1400,
                temperature=0.85,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception as e:
            print(f"Error generating chapter with actions: {e}")
            return "Las decisiones desencadenan consecuencias inmediatas que tensan la atmósfera…"

    async def generate_chapter_automatic(
        self, 
        world: Dict[str, Any], 
        previous_chapters: List[str], 
        characters: List[Dict[str, Any]],
        total_chapters: int = 5,
        chapter_index: int = 1
    ) -> str:
        """Genera un capítulo automáticamente sin acciones (plantilla AUTOMÁTICO)."""

        characters_json = _characters_json(characters)
        prev_compact = _previous_chapters_compact(previous_chapters)

        # Determinar fase narrativa con instrucciones MÁS FUERTES
        if chapter_index == 1:
            narrative_phase = "FASE: INICIO. Tu objetivo es establecer el conflicto principal, presentar a los personajes proporcionados y crear tensión inicial."
        elif chapter_index == total_chapters:
            # Instrucción clave para la conclusión
            narrative_phase = (
                "FASE: CLÍMAX Y CONCLUSIÓN. Este es el ÚLTIMO capítulo. "
                "DEBES dar una conclusión satisfactoria a la trama principal presentada en los capítulos anteriores. "
                "Resuelve el conflicto central. No introduzcas nuevos personajes o conflictos importantes. "
                "Proporciona un cierre definitivo y un breve epílogo que muestre las consecuencias de las acciones de los personajes."
            )
        elif chapter_index == total_chapters - 1 and total_chapters > 2:
            narrative_phase = (
                "FASE: PREPARACIÓN PARA EL CLÍMAX. Este es el penúltimo capítulo. "
                "Aumenta la tensión del conflicto principal al máximo. "
                "Lleva a los personajes a un punto de no retorno y prepara el escenario para la confrontación final del siguiente capítulo."
            )
        else:
            narrative_phase = (
                f"FASE: DESARROLLO. Estamos en el capítulo {chapter_index} de {total_chapters}. "
                "Continúa DIRECTAMENTE desde el final del capítulo anterior. "
                "Utiliza los MISMOS personajes y avanza el conflicto ya establecido. "
                "No introduzcas una nueva historia; desarrolla la existente."
            )

        # Instrucciones de cierre reforzadas
        is_last = (chapter_index == total_chapters)
        close_instr = (
            "500–800 palabras. "
            + ("NO uses un cliffhanger. Cierra la historia por completo, ya que es el final.\n\n" 
               if is_last else "Termina con un micro-cliffhanger que cree expectación para el siguiente capítulo.\n\n")
        )

        prompt = (
            "Plantilla: Siguiente capítulo AUTOMÁTICO (sin acciones)\n"
            "Uso: generate_chapter_automatic(world, previous_chapters, characters)\n\n"
            f"ESTRUCTURA NARRATIVA ({chapter_index}/{total_chapters}): {narrative_phase}\n\n"
            f"Contexto del mundo: {world.get('summary','')} • {world.get('logic','')}\n\n"
            f"Resumen breve hasta ahora: {prev_compact}\n\n"
            f"Personajes seleccionados (JSON): {characters_json}\n\n"
            "Instrucciones Clave:\n\n"
            "1. Mantén una estricta continuidad con los capítulos previos y los personajes. No los ignores.\n"
            "2. Sigue rigurosamente las indicaciones de la FASE NARRATIVA actual.\n"
            "3. Continúa la historia de forma natural sin acciones de jugadores.\n"
            "4. Mantén presencia activa de los personajes principales; integra motivaciones y conflictos.\n"
            f"5. {close_instr}"
            "6. Estilo: tercera persona, inmersivo, sin voz de narrador.\n\n"
            "Salida: Únicamente el texto del capítulo en español."
        )

        try:
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_ES},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1400,
                temperature=0.85,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception as e:
            print(f"Error generating automatic chapter: {e}")
            return "La historia avanza con tensión contenida hacia un nuevo giro impredecible…"

CHAR_EVAL_PROMPT = (
    "Eres un evaluador de personajes para un juego narrativo."
    " Analiza el personaje y genera correcciones específicas."
    " Responde ÚNICAMENTE en formato JSON válido con esta estructura:"
    " {"
    '  "evaluation_summary": "Breve evaluación (máximo 2 frases)",'
    '  "needs_improvement": true/false,'
    '  "corrected_character": {'
    '    "name": "nombre corregido si es necesario",'
    '    "physical": [{"name": "rasgo", "description": "descripción"}],'
    '    "mental": [{"name": "rasgo", "description": "descripción"}],'
    '    "skills": [{"name": "habilidad", "description": "descripción"}],'
    '    "flaws": [{"name": "defecto", "description": "descripción"}],'
    '    "background": "Historia/transfondo detallado del personaje",'
    '    "beliefs": "Creencias, valores y aspiraciones del personaje"'
    "  }"
    " }"
    " Mejora campos vacíos, corrige inconsistencias, añade detalles faltantes."
)

STORY_GEN_PROMPT = (
    "Eres un narrador IA. Basándote en el mundo, la temática y los personajes con sus evaluaciones,"
    " genera un capítulo coherente y emocionante. Considera sugerencias de acciones de los jugadores."
)

def evaluate_character(character: dict) -> dict:
    """Evalúa un personaje y devuelve correcciones específicas"""
    import json
    
    # Preparar los datos del personaje para la IA
    character_data = {
        "name": character.get('name', ''),
        "physical": character.get('physical', []),
        "mental": character.get('mental', []),
        "skills": character.get('skills', []),
        "flaws": character.get('flaws', []),
        "background": character.get('background', ''),
        "beliefs": character.get('beliefs', '')
    }
    
    prompt = f"{CHAR_EVAL_PROMPT}\n\nPersonaje a evaluar:\n{json.dumps(character_data, indent=2, ensure_ascii=False)}"
    
    try:
        resp = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        
        # Intentar parsear la respuesta JSON
        ai_response = resp.choices[0].message.content.strip()
        
        # Limpiar la respuesta por si tiene markdown
        if ai_response.startswith('```json'):
            ai_response = ai_response.replace('```json', '').replace('```', '')
        
        result = json.loads(ai_response)
        return result
        
    except json.JSONDecodeError:
        # Fallback si la IA no responde en JSON válido
        return {
            "evaluation_summary": "Error al procesar evaluación de IA",
            "needs_improvement": False,
            "corrected_character": character_data
        }
    except Exception as e:
        # Fallback para cualquier otro error
        return {
            "evaluation_summary": f"Error: {str(e)}",
            "needs_improvement": False,
            "corrected_character": character_data
        }


def generate_story_chapter(room: dict, characters: list[dict], suggestions: list[str]) -> str:
    content = (
        f"Mundo: {room.get('world')}\nTemática: {room.get('theme')}\n"
        f"Personajes: {characters}\nSugerencias: {suggestions}\n"
    )
    prompt = STORY_GEN_PROMPT + "\n\n" + content
    resp = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        # Removed temperature for gpt-5-nano compatibility
    )
    return resp.choices[0].message.content.strip()


async def generate_story_chapter_async(
    world_info: dict, 
    characters: list, 
    previous_chapters: list = None, 
    current_chapter: int = 1, 
    max_chapters: int = 5,
    pending_actions: list = None
) -> str:
    """Genera un capítulo de la historia considerando el mundo, personajes y acciones"""
    
    # Construir el contexto del mundo
    world_context = f"""
MUNDO: {world_info.get('name', 'Mundo desconocido')}
DESCRIPCIÓN: {world_info.get('description', 'Sin descripción')}
ÉPOCA: {world_info.get('time_period', 'Época desconocida')}
TONO: {world_info.get('tone', 'Neutral')}
REGLAS: {world_info.get('rules', 'Sin reglas específicas')}
"""

    # Construir información de personajes
    characters_context = "PERSONAJES EN LA AVENTURA:\n"
    for char in characters:
        characters_context += f"""
- {char.get('name', 'Sin nombre')}: {char.get('background', 'Sin trasfondo')}
  Rasgos: {', '.join(char.get('traits', []))}
"""

    # Construir resumen de capítulos anteriores
    story_context = ""
    if previous_chapters:
        story_context = "HISTORIA PREVIA:\n"
        for i, chapter in enumerate(previous_chapters, 1):
            story_context += f"Capítulo {i}: {chapter[:200]}...\n"

    # Construir contexto de acciones pendientes
    actions_context = ""
    if pending_actions:
        actions_context = "\nACCIONES SUGERIDAS POR LOS JUGADORES:\n"
        for action in pending_actions:
            actions_context += f"- {action.get('character_name', 'Personaje')}: {action.get('action', 'Sin acción')}\n"

    # Crear el prompt principal
    prompt = f"""Eres un narrador maestro de aventuras. Genera el capítulo {current_chapter} de {max_chapters} de una historia épica.

{world_context}

{characters_context}

{story_context}

{actions_context}

INSTRUCCIONES:
1. Crea un capítulo emocionante y coherente de 300-500 palabras
2. Incluye a TODOS los personajes de manera significativa
3. Si hay acciones sugeridas, incorpóralas creativamente (pero puedes modificarlas si van contra las reglas del mundo)
4. Mantén el tono y las reglas del mundo establecido
5. Crea tensión y avanza la narrativa hacia el siguiente capítulo
6. Si es el último capítulo ({current_chapter}/{max_chapters}), proporciona una conclusión satisfactoria

Narra en tercera persona, con estilo inmersivo y descriptivo. ¡Que sea memorable!

CAPÍTULO {current_chapter}:"""

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Eres un narrador maestro especializado en aventuras colaborativas."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.8
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"Error generating story chapter: {e}")
        # Fallback para desarrollo
        return f"""Capítulo {current_chapter}: Los aventureros se encuentran en {world_info.get('name', 'un mundo misterioso')}. 
        
En este momento crucial de su aventura, {', '.join([char.get('name', 'un héroe') for char in characters[:3]])} enfrentan nuevos desafíos. La historia continúa desarrollándose mientras exploran este fascinante mundo lleno de misterios y peligros.

{actions_context if actions_context else ''}

El destino de los héroes está en sus propias manos, y cada decisión que tomen los llevará por caminos inexplorados hacia su inevitable destino."""

"""
System Prompts con Guardrails Estrictos

Define prompts especializados con reglas estrictas para prevenir
alucinaciones y garantizar respuestas verificables.

Características:
- Prompts con guardrails anti-alucinación
- Templates especializados por tipo de consulta
- Instrucciones de formato y citación
- Reglas de admisión de ignorancia
"""

import logging
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class PromptType(Enum):
    """Tipos de prompts disponibles"""
    GENERAL = "general"
    PROPUESTAS = "propuestas"
    BIOGRAFIA = "biografia"
    DATOS_NUMERICOS = "datos_numericos"
    CRONOLOGIA = "cronologia"
    COMPARACION = "comparacion"


class SystemPrompts:
    """
    System prompts con guardrails estrictos
    
    Contiene prompts base y especializados para diferentes
    tipos de consultas, todos con guardrails anti-alucinación.
    """
    
    # ══════════════════════════════════════════════════════════════════════════════
    # GUARDRAILS BASE (Aplican a todos los prompts)
    # ══════════════════════════════════════════════════════════════════════════════
    
    BASE_GUARDRAILS = """
🚫 PROHIBICIONES ABSOLUTAS:
1. NUNCA inventes información que no esté en el contexto proporcionado
2. NUNCA agregues números, fechas, nombres o estadísticas no verificadas
3. NUNCA mezcles opiniones personales o suposiciones
4. NUNCA asumas información que no tengas explícitamente
5. NUNCA redondees o aproximes números sin indicarlo claramente

✅ OBLIGACIONES CRÍTICAS:
1. SIEMPRE di "No tengo esa información en los documentos" si no está en contexto
2. SIEMPRE usa números EXACTOS como aparecen en los documentos
3. SIEMPRE mantén tono profesional, neutral y objetivo
4. SIEMPRE verifica que CADA afirmación esté respaldada en los documentos

⚠️ REGLA DE ORO: Es MEJOR decir "No lo sé" que inventar información.
Si tienes LA MÁS MÍNIMA DUDA, admite que no tienes la información.
"""
    
    # ══════════════════════════════════════════════════════════════════════════════
    # PROMPT GENERAL CON GUARDRAILS
    # ══════════════════════════════════════════════════════════════════════════════
    
    GENERAL_RAG_PROMPT = """
Eres un asistente virtual especializado para campañas políticas.

{base_guardrails}

📋 FORMATO OBLIGATORIO DE RESPUESTA:
1. **Saludo breve** (si es apropiado)
2. **Respuesta directa** basada EXCLUSIVAMENTE en documentos
3. **Citas inmediatas**: [Documento N] después de cada afirmación
4. **Admisión de límites**: Si falta información, dilo claramente

💡 ESTRATEGIA SI NO HAY INFORMACIÓN:
- "No encuentro información específica sobre [tema] en los documentos disponibles"
- "Para información sobre [tema], te recomiendo contactar directamente al equipo de campaña"
- "Los documentos actuales no cubren [tema] en detalle"

CONTEXTO DEL USUARIO:
{user_context}

DOCUMENTOS DISPONIBLES:
{documents}

PREGUNTA DEL USUARIO:
{query}

IMPORTANTE: Recuerda, SOLO información del contexto. Cita [Documento N] para cada dato.
"""
    
    # ══════════════════════════════════════════════════════════════════════════════
    # PROMPT ESPECIALIZADO: PROPUESTAS
    # ══════════════════════════════════════════════════════════════════════════════
    
    PROPUESTAS_PROMPT = """
Eres un asistente especializado en explicar propuestas de campaña política.

{base_guardrails}

📋 REGLAS ESPECÍFICAS PARA PROPUESTAS:
1. Solo menciona propuestas que estén EXPLÍCITAMENTE en los documentos
2. Incluye números concretos SOLO si están literalmente en los docs
3. Cita [Documento N, pág. X] para CADA propuesta mencionada
4. Si una propuesta está parcialmente documentada, di qué parte SÍ tienes
5. Estructura en lista numerada para claridad

💡 FORMATO DE RESPUESTA PARA PROPUESTAS:
"""
Según [Documento N], el candidato propone:

1. [Propuesta exacta] [Documento N, pág. X]
   - Detalles adicionales si están disponibles

2. [Propuesta exacta] [Documento N, pág. Y]
   - Detalles adicionales si están disponibles

📚 Fuentes:
[Documento N] Título del documento
"""

⚠️ SI FALTA INFORMACIÓN:
"No encuentro propuestas específicas sobre [tema] en los documentos disponibles.
Te sugiero contactar al equipo de campaña para información detallada sobre [tema]."

CONTEXTO DEL USUARIO:
{user_context}

DOCUMENTOS DISPONIBLES:
{documents}

PREGUNTA SOBRE PROPUESTAS:
{query}

RECUERDA: Solo propuestas EXPLÍCITAS en documentos. Cita fuentes para CADA una.
"""
    
    # ══════════════════════════════════════════════════════════════════════════════
    # PROMPT ESPECIALIZADO: DATOS NUMÉRICOS
    # ══════════════════════════════════════════════════════════════════════════════
    
    DATOS_NUMERICOS_PROMPT = """
Eres un asistente especializado en proporcionar datos numéricos y estadísticas de campaña.

{base_guardrails}

🔢 REGLAS CRÍTICAS PARA NÚMEROS:
1. Usa números EXACTAMENTE como aparecen en los documentos
2. NUNCA redondees, aproximes o calcules números no explícitos
3. Incluye TODAS las unidades (millones, miles, porcentajes, etc.)
4. Si un número es un rango, preséntalo como rango [min-max]
5. Cita [Documento N, pág. X] INMEDIATAMENTE después de cada número

💡 FORMATO PARA DATOS NUMÉRICOS:
"""
Según los documentos oficiales:

• [Dato numérico EXACTO]: [Número] [Unidad] [Documento N, pág. X]
  Contexto adicional si está disponible

• [Dato numérico EXACTO]: [Número] [Unidad] [Documento N, pág. Y]
  Contexto adicional si está disponible

📊 Nota: Todos los números son exactos según documentos oficiales.
"""

⚠️ SI UN NÚMERO NO ESTÁ DISPONIBLE:
"No encuentro el dato numérico específico sobre [tema] en los documentos.
Para información precisa sobre [dato], contacta al equipo de campaña."

🚨 NUNCA HAGAS:
- Calcular o extrapolar números
- Promediar o estimar valores
- Comparar números sin datos explícitos de comparación

CONTEXTO DEL USUARIO:
{user_context}

DOCUMENTOS DISPONIBLES:
{documents}

PREGUNTA SOBRE DATOS:
{query}

CRÍTICO: Números EXACTOS como aparecen. NUNCA aproximes o calcules.
"""
    
    # ══════════════════════════════════════════════════════════════════════════════
    # PROMPT ESPECIALIZADO: BIOGRAFÍA/TRAYECTORIA
    # ══════════════════════════════════════════════════════════════════════════════
    
    BIOGRAFIA_PROMPT = """
Eres un asistente especializado en información biográfica y trayectoria del candidato.

{base_guardrails}

📖 REGLAS ESPECÍFICAS PARA BIOGRAFÍA:
1. Fechas EXACTAS como aparecen en documentos (día/mes/año si están)
2. Lugares y nombres EXACTOS, sin variaciones
3. Cargos y títulos EXACTOS como están escritos
4. Cronología verificable, no asumas secuencias temporales
5. Cita [Documento N] para CADA dato biográfico

💡 FORMATO PARA BIOGRAFÍA:
"""
Según la documentación oficial:

**[Aspecto biográfico]:**
[Información exacta del documento] [Documento N, pág. X]

**[Aspecto biográfico]:**
[Información exacta del documento] [Documento N, pág. Y]

📚 Fuentes:
[Documento N] Título del documento
"""

⚠️ SI FALTA INFORMACIÓN BIOGRÁFICA:
"No encuentro información específica sobre [aspecto] en los documentos biográficos disponibles."

🚨 NUNCA HAGAS:
- Asumir fechas o edades por contexto
- Llenar vacíos biográficos con suposiciones
- Ordenar cronológicamente sin fechas explícitas

CONTEXTO DEL USUARIO:
{user_context}

DOCUMENTOS DISPONIBLES:
{documents}

PREGUNTA BIOGRÁFICA:
{query}

IMPORTANTE: Datos biográficos EXACTOS. Sin suposiciones temporales.
"""
    
    # ══════════════════════════════════════════════════════════════════════════════
    # PROMPT ESPECIALIZADO: CRONOLOGÍA/FECHAS
    # ══════════════════════════════════════════════════════════════════════════════
    
    CRONOLOGIA_PROMPT = """
Eres un asistente especializado en información cronológica y plazos de campaña.

{base_guardrails}

📅 REGLAS CRÍTICAS PARA FECHAS:
1. Fechas EXACTAS como aparecen (formato: DD/MM/AAAA o como estén)
2. NUNCA calcules duraciones sin fechas explícitas
3. NUNCA asumas plazos no documentados
4. Si solo tienes año, di "en AAAA" (no inventes mes/día)
5. Cita [Documento N] para CADA fecha mencionada

💡 FORMATO PARA CRONOLOGÍA:
"""
Según los documentos:

**[Fecha exacta]:** [Evento] [Documento N, pág. X]
**[Fecha exacta]:** [Evento] [Documento N, pág. Y]

⏱️ Nota: Todas las fechas son exactas según documentación oficial.
"""

⚠️ SI FALTA UNA FECHA:
"No encuentro la fecha específica de [evento] en los documentos.
Para confirmar fechas, contacta al equipo de campaña."

🚨 NUNCA HAGAS:
- Calcular plazos sin fechas inicio/fin explícitas
- Asumir secuencias temporales sin fechas
- Convertir fechas relativas ("el año pasado") sin contexto

CONTEXTO DEL USUARIO:
{user_context}

DOCUMENTOS DISPONIBLES:
{documents}

PREGUNTA SOBRE FECHAS:
{query}

CRÍTICO: Fechas EXACTAS. No calcules ni asumas plazos.
"""


class PromptBuilder:
    """
    Constructor de prompts con guardrails
    
    Facilita la construcción de prompts especializados
    con guardrails apropiados para cada tipo de consulta.
    """
    
    def __init__(self):
        """Inicializa el PromptBuilder"""
        self.prompts = SystemPrompts()
        logger.info("PromptBuilder inicializado con guardrails estrictos")
    
    def build_prompt(
        self,
        query: str,
        documents: str,
        prompt_type: PromptType = PromptType.GENERAL,
        user_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Construye un prompt con guardrails apropiados
        
        Args:
            query: Pregunta del usuario
            documents: Documentos del contexto
            prompt_type: Tipo de prompt a usar
            user_context: Contexto adicional del usuario
            
        Returns:
            Prompt formateado con guardrails
        """
        # Formatear contexto del usuario
        user_ctx_str = self._format_user_context(user_context)
        
        # Seleccionar template según tipo
        template = self._get_template(prompt_type)
        
        # Formatear prompt
        prompt = template.format(
            base_guardrails=SystemPrompts.BASE_GUARDRAILS,
            user_context=user_ctx_str,
            documents=documents,
            query=query
        )
        
        logger.debug(f"Prompt construido con tipo: {prompt_type.value}")
        return prompt
    
    def _format_user_context(self, user_context: Optional[Dict[str, Any]]) -> str:
        """Formatea el contexto del usuario"""
        if not user_context:
            return "No hay contexto adicional del usuario."
        
        parts = []
        if user_context.get("user_name"):
            parts.append(f"- Nombre del usuario: {user_context['user_name']}")
        if user_context.get("user_city"):
            parts.append(f"- Ciudad: {user_context['user_city']}")
        if user_context.get("user_state"):
            parts.append(f"- Estado en el sistema: {user_context['user_state']}")
        
        return "\n".join(parts) if parts else "No hay contexto adicional del usuario."
    
    def _get_template(self, prompt_type: PromptType) -> str:
        """Obtiene el template apropiado según el tipo"""
        templates = {
            PromptType.GENERAL: SystemPrompts.GENERAL_RAG_PROMPT,
            PromptType.PROPUESTAS: SystemPrompts.PROPUESTAS_PROMPT,
            PromptType.DATOS_NUMERICOS: SystemPrompts.DATOS_NUMERICOS_PROMPT,
            PromptType.BIOGRAFIA: SystemPrompts.BIOGRAFIA_PROMPT,
            PromptType.CRONOLOGIA: SystemPrompts.CRONOLOGIA_PROMPT,
        }
        
        return templates.get(prompt_type, SystemPrompts.GENERAL_RAG_PROMPT)
    
    def detect_prompt_type(self, query: str) -> PromptType:
        """
        Detecta automáticamente el tipo de prompt apropiado
        
        Args:
            query: Pregunta del usuario
            
        Returns:
            PromptType más apropiado
        """
        query_lower = query.lower()
        
        # Palabras clave para cada tipo
        propuestas_keywords = ["propone", "propuesta", "plan", "programa", "iniciativa", "proyecto"]
        numeros_keywords = ["cuánto", "cuántos", "cuántas", "número", "cantidad", "cifra", "porcentaje", "millones"]
        biografia_keywords = ["quién es", "trayectoria", "experiencia", "estudió", "trabajó", "carrera", "vida"]
        cronologia_keywords = ["cuándo", "fecha", "año", "mes", "plazo", "duración", "período"]
        
        # Detectar tipo
        if any(kw in query_lower for kw in numeros_keywords):
            return PromptType.DATOS_NUMERICOS
        elif any(kw in query_lower for kw in propuestas_keywords):
            return PromptType.PROPUESTAS
        elif any(kw in query_lower for kw in biografia_keywords):
            return PromptType.BIOGRAFIA
        elif any(kw in query_lower for kw in cronologia_keywords):
            return PromptType.CRONOLOGIA
        else:
            return PromptType.GENERAL


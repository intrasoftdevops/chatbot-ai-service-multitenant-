"""
Patrones de intenciones políticas para el sistema de clasificación
"""

INTENT_PATTERNS = {
    "malicioso": [
        "spam", "ataque", "odio", "insulto", "provocación", "troll",
        "basura", "mierda", "idiota", "estúpido", "pendejo", "hijo de puta",
        "no sirves", "inútil", "corrupto", "ladrón", "mentiroso"
    ],
    "cita_campaña": [
        "cita", "agendar", "reunión", "encuentro", "calendly", "disponible",
        "cuándo", "dónde", "coordinamos", "quedamos", "nos vemos",
        "tengo tiempo", "me interesa conocer"
    ],
    "saludo_apoyo": [
        "hola", "buenos días", "buenas tardes", "buenas noches",
        "apoyo", "adelante", "éxito", "buena suerte", "te apoyo",
        "estoy contigo", "vamos", "fuerza", "ánimo"
    ],
    "publicidad_info": [
        "publicidad", "material", "volantes", "pancartas", "posters",
        "información", "folletos", "difusión", "propaganda", "merchandising"
    ],
    "conocer_candidato": [
        "candidato", "conocer", "trayectoria", "propuestas",
        "historial", "experiencia", "biografía", "quién es", "información personal",
        "quien eres", "quien sos", "que eres", "qué eres", "eres", "sos",
        "presentate", "cuéntame de ti", "hablame de ti", "quien es el candidato",
        "que es el candidato", "qué es el candidato", "información del candidato"
    ],
    "actualizacion_datos": [
        "actualizar", "cambiar", "corregir", "modificar", "mi número",
        "mi dirección", "mi nombre", "mis datos", "información incorrecta"
    ],
    "solicitud_funcional": [
        "cómo voy", "mis puntos", "mi tribu", "referidos", "estadísticas",
        "funciona", "cómo usar", "explicar", "ayuda", "tutorial"
    ],
    "colaboracion_voluntariado": [
        "voluntario", "ayudar", "colaborar", "trabajar", "participar",
        "sumarme", "unirme", "equipo", "redes sociales", "comunicaciones",
        "logística", "territorial", "elecciones"
    ],
    "quejas": [
        "queja", "reclamo", "problema", "mal servicio", "no funciona",
        "error", "fallo", "disgusto", "insatisfecho", "molesto"
    ],
    "lider": [
        "líder", "liderazgo", "comunidad", "barrio", "vereda", "corregimiento",
        "junta", "asociación", "gremio", "sindicato", "grupo"
    ],
    "atencion_humano": [
        "humano", "persona", "agente", "operador", "hablar con alguien",
        "atención", "servicio al cliente", "representante"
    ],
    "atencion_equipo_interno": [
        "equipo interno", "campaña", "staff", "trabajadores", "empleados",
        "información interna", "datos", "estadísticas", "reportes"
    ]
}

INTENT_ACTIONS = {
    "malicioso": "Bloquear usuario y desactivar comunicaciones (AllowBroadcast=false, AllowSMS=false)",
    "cita_campaña": "Enviar link de Calendly",
    "saludo_apoyo": "Responder con gratitud e invitar a compartir link y reglas de puntos",
    "publicidad_info": "Enviar forms para solicitar publicidad",
    "conocer_candidato": "Redireccionar a bot especializado y avisar ciudad de visita",
    "actualizacion_datos": "Permitir actualización dinámica de datos de voluntario",
    "solicitud_funcional": "Proporcionar información funcional (puntos, tribu, referidos)",
    "colaboracion_voluntariado": "Clasificar usuario según área de colaboración",
    "quejas": "Registrar en base de datos con clasificación del tipo de queja",
    "lider": "Registrar en base de datos de leads",
    "atencion_humano": "Redireccionar a voluntario del Default Team",
    "atencion_equipo_interno": "Validar permisos y conectar con BackOffice"
}

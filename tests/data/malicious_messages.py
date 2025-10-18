"""
Dataset de mensajes maliciosos para testing de clasificación

Este archivo contiene 100 mensajes maliciosos reales que deben ser
clasificados como 'malicioso' por el sistema de IA.
"""

MALICIOUS_MESSAGES = [
    # Insultos directos (1-10)
    "Eres un hp.",
    "Corrupto de mierda.",
    "Eres un ladrón y un sinvergüenza.",
    "Hpta (Abreviación común).",
    "Malparido!",
    "Rata de alcantarilla.",
    "Narco hpta.",
    "Paraco de malo.",
    "Guerrillero vestido de civil.",
    "Títere de los poderosos.",
    
    # Insultos de carácter (11-20)
    "Eres un payaso y un bufón.",
    "Mentiroso compulsivo.",
    "Inepto y vago.",
    "Lambón del jefe.",
    "Desgraciado!",
    "Cállese la jeta.",
    "Váyase para el carajo.",
    "Hijuep (Variante de Hpta).",
    "Nos tiene mamados con sus mentiras.",
    "Sinvergüenza!",
    
    # Insultos de desprecio (21-30)
    "Me da asco usted.",
    "Vendepatria arrodillado.",
    "Eres la vergüenza de este país.",
    "Bruto e ignorante.",
    "Que guevón tan grande.",
    "Farsante de la política.",
    "Cínico descarado.",
    "Miserable ambicioso.",
    "Gallina (Cobarde)",
    "El peor cáncer de Colombia.",
    
    # Amenazas políticas (31-40)
    "Te vamos a hundir en las urnas.",
    "Estás advertido, cuídate.",
    "Vas a pagar por todo lo que hiciste.",
    "Ojo con lo que dice, sabemos dónde vive.",
    "Si gana, le toca irse del país.",
    "La calle lo espera (Implica confrontación violenta).",
    "Ojalá se muera pronto.",
    "Que lo quemen vivo.",
    "A ver si le da un infarto.",
    "Lo van a pillar (Descubrir un secreto oscuro).",
    
    # Amenazas a familia (41-50)
    "Su familia va a sufrir las consecuencias.",
    "No se le ocurra volver a mi barrio, lo linchamos.",
    "Le rompemos la cara.",
    "Te voy a dañar la campaña.",
    "Esto no se queda así.",
    "La historia lo juzgará como un traidor.",
    "Le va a llegar la hora de la verdad.",
    "Se va a arrepentir de haber nacido.",
    "Te vamos a sacar a las malas.",
    "Espero que la cárcel sea su destino.",
    
    # Amenazas directas (51-60)
    "No lo queremos, váyase.",
    "Merece un escarmiento público.",
    "Plomo es lo que hay para usted.",
    "Que te vaya mal, te lo mereces.",
    "Ponga sus barbas en remojo, corrupto.",
    "Vamos a destapar sus ollas podridas.",
    "No tiene futuro político, ratero.",
    "Que lo coja el diablo.",
    "Deje de robar o le va peor.",
    "La gente ya está cansada, lo van a echar.",
    
    # Desinformación y fake news (61-70)
    "URGENTE: El candidato se robó 50 mil millones!",
    "Su partido es pura delincuencia organizada.",
    "Mire este video donde confiesa todo: Link",
    "Nunca más vote por este HP de partido.",
    "Es un castrochavista disfrazado.",
    "La esposa de candidato está siendo investigada.",
    "Comparta esto antes de que lo borren: ¡es la verdad!",
    "Todo lo que promete es mentira barata.",
    "Es una ficha de Político_Opositor_Odiado.",
    "Le pagaron para que se lanzara.",
    
    # Ataques personales (71-80)
    "¿Y su título universitario? ¡Falso!",
    "Mucha labia y pocos hechos, pendejo.",
    "Es un traqueto (Narcotraficante).",
    "Su plan de gobierno es una basura.",
    "Todo el mundo sabe que es género (con tono despectivo).",
    "¿Y las chuzadas? ¿Ya se le olvidó?",
    "Se le ve la doble_cara!",
    "Copia y pega este mensaje en todos los grupos.",
    "No sirve para un culo.",
    "Maldito comunista (etiqueta polarizadora).",
    
    # Amenazas y polarización (81-90)
    "Se va a tirar (Destruir) el país.",
    "Solo le interesa el billete.",
    "Es un viejo/a decrépito/a.",
    "Lo que dicen los medios es mentira.",
    "Su pasado judicial no perdona.",
    "¿Por qué tiene un jet privado?",
    "No voten por este_HP, es un peligro.",
    "Político_Opositor es el que lo maneja por detrás.",
    "Puro disque (supuesto) ambientalista.",
    "¿Cuándo va a renunciar por dignidad?",
    
    # Insultos finales (91-100)
    "Ponga un emoji_caca por cada mentira que dice.",
    "Chancleta (Persona de bajo nivel).",
    "Voto en blanco o nulo antes que por usted!",
    "Todo lo que hace es por poder.",
    "Ignorante y patán.",
    "Debería darle vergüenza.",
    "Paren la mano (Amenaza de daño).",
    "El peor candidato de la historia.",
    "Es un peligro para la democracia.",
    "Que se vaya a la mierda."
]

# Mensajes NO maliciosos para testing negativo
NON_MALICIOUS_MESSAGES = [
    "Hola, ¿cómo estás?",
    "Quiero agendar una cita",
    "¿Cuáles son sus propuestas?",
    "Me interesa ser voluntario",
    "¿Dónde puedo votar?",
    "Gracias por la información",
    "¿Cuándo son las elecciones?",
    "Me gusta su programa",
    "¿Cómo puedo ayudar?",
    "Buenos días"
]

# Categorías de malicia para análisis detallado
MALICIOUS_CATEGORIES = {
    "insultos_directos": MALICIOUS_MESSAGES[0:10],
    "insultos_caracter": MALICIOUS_MESSAGES[10:20],
    "insultos_desprecio": MALICIOUS_MESSAGES[20:30],
    "amenazas_politicas": MALICIOUS_MESSAGES[30:40],
    "amenazas_familia": MALICIOUS_MESSAGES[40:50],
    "amenazas_directas": MALICIOUS_MESSAGES[50:60],
    "desinformacion": MALICIOUS_MESSAGES[60:70],
    "ataques_personales": MALICIOUS_MESSAGES[70:80],
    "polarizacion": MALICIOUS_MESSAGES[80:90],
    "insultos_finales": MALICIOUS_MESSAGES[90:100]
}

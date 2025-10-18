"""
Controlador para normalización de ciudades
=========================================

Maneja la normalización de ciudades usando fuentes externas y IA
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any
import aiohttp
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["city-normalization"])

@router.post("/normalize-city")
async def normalize_city(request: Dict[str, Any]):
    """
    Normaliza una ciudad y detecta su departamento/estado y país usando IA y fuentes externas REALES
    """
    try:
        city_input = request.get("city", "").strip()
        if not city_input:
            raise HTTPException(status_code=400, detail="City parameter is required")
        
        logger.info(f"🌍 Normalizando ciudad: '{city_input}'")
        
        # Estrategia híbrida: IA + fuentes externas + validación cruzada
        normalized_result = await normalize_city_hybrid_approach(city_input)
        
        result = {
            "city": normalized_result["city"],
            "state": normalized_result.get("state"),
            "country": normalized_result.get("country", "Colombia"),
            "confidence": normalized_result.get("confidence", 0.8),
            "source": normalized_result.get("source", "hybrid")
        }
        
        # Si necesita aclaración, incluir la pregunta y opciones
        if normalized_result.get("source") == "clarification_needed":
            result["clarification_question"] = normalized_result.get("clarification_question")
            result["options"] = normalized_result.get("options")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error normalizando ciudad: {e}")
        raise HTTPException(status_code=500, detail=f"Error normalizando ciudad: {str(e)}")

@router.post("/resolve-city-ambiguity")
async def resolve_city_ambiguity(request: Dict[str, Any]):
    """
    Resuelve la ambigüedad de ciudad cuando el usuario selecciona una opción
    """
    try:
        city_input = request.get("city", "").strip()
        selected_option = request.get("selected_option", 0)
        options = request.get("options", [])
        
        if not city_input or not options or selected_option < 1 or selected_option > len(options):
            raise HTTPException(status_code=400, detail="Parámetros inválidos")
        
        # Obtener la opción seleccionada
        selected_city = options[selected_option - 1]
        
        return {
            "city": selected_city.get("city", city_input),
            "state": selected_city.get("state"),
            "country": selected_city.get("country"),
            "confidence": 0.9,  # Alta confianza porque el usuario la confirmó
            "source": "user_confirmed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolviendo ambigüedad de ciudad: {e}")
        raise HTTPException(status_code=500, detail=f"Error resolviendo ambigüedad: {str(e)}")

@router.post("/interpret-city-selection")
async def interpret_city_selection(request: Dict[str, Any]):
    """
    Interpreta la selección de ciudad del usuario en lenguaje natural
    """
    try:
        user_response = request.get("user_response", "").strip()
        options = request.get("options", [])
        city_input = request.get("city", "").strip()
        
        if not user_response or not options or not city_input:
            raise HTTPException(status_code=400, detail="Parámetros requeridos: user_response, options, city")
        
        logger.info(f"🤖 Interpretando selección natural: '{user_response}' para ciudad '{city_input}'")
        
        # Usar IA para interpretar la respuesta del usuario
        selected_option = await interpret_natural_selection(user_response, options, city_input)
        
        if selected_option is None:
            return {
                "success": False,
                "message": "No pude entender tu respuesta. Por favor, responde con el número de la opción (1, 2, 3) o menciona el país o región específica.",
                "suggestions": [f"{i+1}. {opt.get('full_location', '')}" for i, opt in enumerate(options)]
            }
        
        return {
            "success": True,
            "selected_option": selected_option,
            "city": options[selected_option-1].get("city"),
            "state": options[selected_option-1].get("state"),
            "country": options[selected_option-1].get("country"),
            "confidence": 0.9
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error interpretando selección de ciudad: {e}")
        raise HTTPException(status_code=500, detail=f"Error interpretando selección: {str(e)}")

async def normalize_city_hybrid_approach(city_input: str) -> Dict[str, Any]:
    """
    Enfoque híbrido: usa IA para determinar estrategia de búsqueda, luego consulta fuentes externas
    """
    try:
        # 0. PRIMERO: Verificar sobrenombres/apodos conocidos (más rápido y confiable)
        nickname_result = check_city_nicknames(city_input)
        if nickname_result:
            logger.info(f"🏷️ Sobrenombre detectado: '{city_input}' -> {nickname_result}")
            return {
                "city": nickname_result["city"],
                "state": nickname_result["state"],
                "country": nickname_result["country"],
                "confidence": 0.95,  # Alta confianza para sobrenombres conocidos
                "source": "nickname"
            }
        
        # 1. Usar IA para determinar si la ciudad es probablemente de Colombia
        country_hint = await determine_country_hint_with_ai(city_input)
        logger.info(f"🤖 IA sugiere buscar primero en: {country_hint}")
        
        # 2. Consultar fuentes externas con estrategia inteligente
        external_tasks = [
            query_nominatim_geocoding(city_input, country_hint),
            query_geonames_api(city_input, country_hint),
            query_google_geocoding(city_input, country_hint)  # Si está disponible
        ]
        
        external_results = await asyncio.gather(*external_tasks, return_exceptions=True)
        
        # 3. Procesar resultados de Nominatim (puede devolver múltiples)
        valid_results = []
        for result in external_results:
            if isinstance(result, list):
                # Nominatim devolvió múltiples resultados - usar filtro más permisivo para ambigüedad
                if country_hint == "ambiguous":
                    valid_results.extend([r for r in result if r.get("confidence", 0) > 0.1])
                else:
                    valid_results.extend([r for r in result if r.get("confidence", 0) > 0.5])
            elif isinstance(result, dict):
                if country_hint == "ambiguous" and result.get("confidence", 0) > 0.1:
                    valid_results.append(result)
                elif result.get("confidence", 0) > 0.5:
                    valid_results.append(result)
        
        # 3.5. Eliminar duplicados basándose en ciudad, estado y país
        unique_results = []
        seen_locations = set()
        for result in valid_results:
            city = result.get("city", "").strip()
            state = result.get("state", "")
            country = result.get("country", "")
            location_key = f"{city}|{state}|{country}"
            
            if location_key not in seen_locations:
                seen_locations.add(location_key)
                unique_results.append(result)
        
        # 4. Verificar si hay ambigüedad en los resultados únicos
        logger.info(f"🔍 Verificando ambigüedad: {len(unique_results)} resultados únicos")
        for i, result in enumerate(unique_results):
            logger.info(f"   Resultado {i+1}: {result.get('city')}, {result.get('state')}, {result.get('country')}")
        
        if len(unique_results) > 1 and has_ambiguous_cities(unique_results):
            logger.info(f"🔍 Ambiguidad detectada para '{city_input}'")
            # Usar IA para generar pregunta de aclaración
            clarification_question = await generate_clarification_question(city_input, unique_results)
            return {
                "city": city_input,
                "state": None,
                "country": None,
                "confidence": 0.0,
                "source": "clarification_needed",
                "clarification_question": clarification_question,
                "options": extract_city_options(unique_results)
            }
        
        # 5. Usar IA para análisis y validación cruzada
        ai_analysis = await analyze_external_results_with_ai(city_input, unique_results)
        
        # 6. Seleccionar el mejor resultado basado en confianza y consenso
        best_result = select_best_result(ai_analysis, unique_results)
        
        return best_result
        
    except Exception as e:
        logger.error(f"Error en enfoque híbrido: {e}")
        # Fallback: solo IA
        return await normalize_city_with_ai_only(city_input)

async def determine_country_hint_with_ai(city_input: str) -> str:
    """
    Usa IA para determinar si una ciudad es probablemente de Colombia o de otro país
    """
    try:
        # Primero verificar patrones comunes que indican ambigüedad
        city_lower = city_input.lower().strip()
        
        # Ciudades conocidas que existen en múltiples países
        ambiguous_cities = [
            "madrid", "paris", "london", "berlin", "rome", "milan", "barcelona", 
            "valencia", "sevilla", "zaragoza", "málaga", "murcia", "palma",
            "córdoba", "valladolid", "vigo", "gijón", "lhospitalet", "vitoria",
            "granada", "elche", "oviedo", "santa cruz", "badalona", "cartagena",
            "terrassa", "jerez", "sabadell", "móstoles", "alcalá", "pamplona",
            "león", "castellón", "almería", "burgos", "salamanca", "huelva",
            "albacete", "logroño", "badajoz", "san sebastián", "lérida", "cáceres",
            "santander", "pontevedra", "girona", "lugo", "ourense", "ceuta",
            "melilla", "palencia", "ávila", "segovia", "soria", "guadalajara",
            "cuenca", "toledo", "ciudad real", "jaén", "cádiz", "huesca",
            "teruel", "zamora", "león", "pontevedra", "ourense", "lugo"
        ]
        
        # Si es una ciudad ambigua sin contexto de país, marcar como ambigua
        city_name = extract_city_name_from_input(city_input).lower().strip()
        if city_name in ambiguous_cities:
            # Verificar si hay contexto de país
            has_country_context = any(word in city_lower for word in [
                "en españa", "en colombia", "en méxico", "en argentina", 
                "en chile", "en perú", "en venezuela", "españa", "colombia",
                "méxico", "mexico", "argentina", "chile", "perú", "peru", "venezuela"
            ])
            
            if not has_country_context:
                logger.info(f"🔍 Ciudad ambigua detectada: '{city_name}' sin contexto de país")
                return "ambiguous"
        
        # Importar el servicio de IA
        from chatbot_ai_service.services.ai_service import AIService
        ai_service = AIService()
        
        # Crear prompt para determinar el país
        prompt = f"""
        Analiza el siguiente texto y determina si menciona un país específico:
        
        Texto: "{city_input}"
        
        Busca indicadores de país como:
        - "en [país]" (ej: "en españa", "en colombia", "en méxico")
        - "de [país]" (ej: "de españa", "de colombia")
        - Nombres de países directamente (ej: "españa", "colombia", "méxico")
        - Referencias geográficas (ej: "europa", "américa latina")
        
        IMPORTANTE: Si el texto contiene "en [ciudad]" sin especificar país (ej: "en madrid", "en paris"), 
        responde "ambiguous" porque puede referirse a múltiples países.
        
        Responde SOLO con el nombre del país detectado en minúsculas, "ambiguous" si hay ambigüedad, o "colombia" si no detectas ningún país específico.
        
        Ejemplos:
        - "en españa, en madrid" -> "españa"
        - "en madrid" -> "ambiguous" (puede ser España o Colombia)
        - "madrid" -> "ambiguous" (puede ser España o Colombia)
        - "bogotá" -> "colombia"
        - "en méxico, ciudad de méxico" -> "méxico"
        - "europa" -> "ambiguous"
        """
        
        # Usar el servicio de IA para determinar el país
        response = await ai_service.generate_response(prompt, "system")
        
        if response and response.strip().lower() in ["españa", "spain", "colombia", "méxico", "mexico", "argentina", "chile", "perú", "peru", "venezuela", "ambiguous"]:
            country = response.strip().lower()
            logger.info(f"🤖 IA detectó país: {country} para '{city_input}'")
            return country
        else:
            logger.warn(f"🤖 IA no pudo determinar país claramente: '{response}' para '{city_input}'")
            # No asumir Colombia por defecto, marcar como ambiguo para buscar en todos los países
            return "ambiguous"
        
    except Exception as e:
        logger.error(f"Error determinando país con IA: {e}")
        return "ambiguous"  # Marcar como ambiguo para buscar en todos los países

def extract_city_name_from_input(city_input: str) -> str:
    """
    Extrae el nombre de la ciudad específica del input del usuario
    """
    try:
        # Casos especiales para frases como "en españa, en madrid"
        if "," in city_input:
            parts = [part.strip() for part in city_input.split(",")]
            # Buscar la parte que parece ser una ciudad específica
            for part in reversed(parts):
                clean_part = part.lower().strip()
                # Si la parte contiene "en" seguido de una ciudad específica
                if clean_part.startswith("en "):
                    city_name = clean_part[3:].strip()  # Remover "en "
                    # Verificar que no sea un país
                    if city_name not in ["españa", "spain", "colombia", "méxico", "mexico", "argentina", "chile", "perú", "peru", "venezuela"]:
                        return city_name.title()
                # Si no contiene palabras de país, es probablemente la ciudad
                elif not any(word in clean_part for word in ["en", "de", "del", "la", "el", "españa", "spain", "colombia", "méxico", "mexico"]):
                    return part.strip()
        
        # Si no hay comas, buscar patrones como "en [país], en [ciudad]"
        if "en " in city_input.lower():
            # Dividir por "en" y tomar la última parte
            parts = city_input.lower().split("en ")
            if len(parts) > 1:
                last_part = parts[-1].strip()
                # Si la última parte no contiene palabras de país, es probablemente la ciudad
                if not any(word in last_part for word in ["españa", "spain", "colombia", "méxico", "mexico"]):
                    return last_part.title()
        
        # Si no hay comas, devolver el input completo
        return city_input.strip()
        
    except Exception as e:
        logger.error(f"Error extrayendo nombre de ciudad: {e}")
        return city_input.strip()

async def query_nominatim_geocoding(city_input: str, country_hint: str = "colombia") -> List[Dict[str, Any]]:
    """
    Consulta la API de Nominatim (OpenStreetMap) para obtener información geográfica
    Usa la sugerencia de país de la IA para priorizar la búsqueda
    """
    try:
        url = "https://nominatim.openstreetmap.org/search"
        headers = {
            "User-Agent": "PoliticalReferralsBot/1.0 (contact@example.com)"
        }
        
        # Mapear países a códigos de país
        country_codes = {
            "españa": "es",
            "spain": "es", 
            "colombia": "co",
            "méxico": "mx",
            "mexico": "mx",
            "argentina": "ar",
            "chile": "cl",
            "perú": "pe",
            "peru": "pe",
            "venezuela": "ve",
            "ambiguous": None
        }
        
        # Estrategia de búsqueda basada en la sugerencia de la IA
        search_strategies = []
        
        if country_hint == "ambiguous":
            # Si hay ambigüedad, buscar en todos los países sin filtros
            logger.info(f"🔍 Ambiguidad detectada para '{city_input}', buscando en todos los países")
            
            # Extraer la ciudad específica del input
            city_name = extract_city_name_from_input(city_input)
            logger.info(f"🔍 Ciudad extraída: '{city_name}' de input: '{city_input}'")
            
            # Buscar sin filtros de país para obtener todas las opciones
            search_strategies.append({
                "q": city_name,
                "priority": "ambiguous_all",
                "limit": 10
            })
            
            # También buscar con el input completo
            search_strategies.append({
                "q": city_input,
                "priority": "ambiguous_complete",
                "limit": 5
            })
            
        elif country_hint in country_codes and country_codes[country_hint]:
            # Extraer la ciudad específica del input para búsquedas más precisas
            city_name = extract_city_name_from_input(city_input)
            logger.info(f"🔍 Ciudad extraída: '{city_name}' de input: '{city_input}'")
            
            # Priorizar el país sugerido por la IA con la ciudad específica
            search_strategies.append({
                "q": f"{city_name}, {country_hint.title()}",
                "countrycodes": country_codes[country_hint],
                "priority": f"{country_hint}_first",
                "limit": 5
            })
            
            # También buscar con el input completo por si contiene información adicional
            search_strategies.append({
                "q": f"{city_input}, {country_hint.title()}",
                "countrycodes": country_codes[country_hint],
                "priority": f"{country_hint}_complete",
                "limit": 3
            })
            
            # Siempre incluir Colombia como segunda opción si no es el país sugerido
            if country_hint != "colombia":
                search_strategies.append({
                    "q": f"{city_input}, Colombia",
                    "countrycodes": "co",
                    "priority": "colombia_second",
                    "limit": 3
                })
            
            # Buscar en otros países si no hay resultados específicos
            search_strategies.append({
                "q": city_input,
                "countrycodes": "us,mx,ar,es,ve,pe,ec,bo,py,uy,cl,cr,pa,gt,hn,sv,ni,cu,do,pr,br",
                "priority": "other_countries",
                "limit": 3
            })
        
        all_results = []
        
        async with aiohttp.ClientSession() as session:
            for strategy in search_strategies:
                params = {
                    "q": strategy["q"],
                    "format": "json",
                    "limit": strategy["limit"],
                    "addressdetails": 1
                }
                
                # Solo agregar countrycodes si está definido
                if "countrycodes" in strategy and strategy["countrycodes"]:
                    params["countrycodes"] = strategy["countrycodes"]
                
                try:
                    async with session.get(url, params=params, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if data and len(data) > 0:
                                # Analizar todos los resultados y agregarlos a la lista
                                results = analyze_nominatim_results_multiple(data, strategy["priority"], city_input)
                                all_results.extend(results)
                                logger.info(f"🌍 Nominatim ({strategy['priority']}) encontró {len(results)} resultados")
                
                except Exception as e:
                    logger.error(f"Error en estrategia {strategy['priority']}: {e}")
                    continue
        
        # Si encontramos múltiples resultados, devolverlos todos para detección de ambigüedad
        if len(all_results) > 1:
            return all_results
        elif len(all_results) == 1:
            return all_results[0]
        else:
            return {"confidence": 0.0}
        
    except Exception as e:
        logger.error(f"Error consultando Nominatim: {e}")
        return {"confidence": 0.0}

def analyze_nominatim_results_multiple(data: List[Dict[str, Any]], search_priority: str, city_input: str = "") -> List[Dict[str, Any]]:
    """
    Analiza múltiples resultados de Nominatim y devuelve una lista de resultados válidos
    """
    try:
        results = []
        
        for result in data:
            address = result.get("address", {})
            
            # Extraer información
            city = (address.get("city") or 
                   address.get("town") or 
                   address.get("village") or 
                   address.get("hamlet") or
                   address.get("suburb"))
            
            state = (address.get("state") or 
                    address.get("province") or 
                    address.get("region") or
                    address.get("county"))
            
            country = address.get("country")
            
            if not city:
                continue
            
            # Mapear región a departamento si es Colombia
            if country == "Colombia" and state:
                state = map_colombian_region_to_department(state)
            
            # Calcular score basado en relevancia
            score = 0
            
            # Importancia del lugar (0-1)
            importance = result.get("importance", 0)
            score += importance * 0.4
            
            # Preferencia por Colombia si estamos en búsqueda específica
            if search_priority == "colombia_first" and country == "Colombia":
                score += 0.3
            elif search_priority == "other_countries" and country != "Colombia":
                score += 0.3
            
            # Preferencia por lugares con estado/departamento definido
            if state:
                score += 0.2
            
            # Preferencia por ciudades sobre pueblos
            if any(term in address for term in ["city", "town"]):
                score += 0.1
            
            # Solo agregar si tiene suficiente confianza (reducido para permitir más opciones)
            logger.info(f"   📊 Score para {city}, {state}, {country}: {score:.3f}")
            
            # Filtrar solo ciudades que coincidan con el nombre buscado
            # Extraer la ciudad del input original
            extracted_city = extract_city_name_from_input(city_input).lower().strip()
            city_matches = city.lower().strip() == extracted_city
            
            # También verificar coincidencia directa si el input es simple
            if not city_matches and len(city_input.split()) == 1:
                city_matches = city.lower().strip() == city_input.lower().strip()
            
            if score > 0.1 and city_matches:
                city_result = {
                    "city": city,
                    "state": state,
                    "country": country or "Colombia",
                    "confidence": min(score, 0.9),
                    "source": "nominatim"
                }
                results.append(city_result)
                logger.info(f"   ✅ Agregado: {city}, {state}, {country}")
            else:
                if not city_matches:
                    logger.info(f"   ❌ Rechazado por nombre no coincidente: {city}, {state}, {country}")
                else:
                    logger.info(f"   ❌ Rechazado por score bajo: {city}, {state}, {country}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error analizando múltiples resultados Nominatim: {e}")
        return []

def map_colombian_region_to_department(state: str) -> str:
    """
    Mapea regiones administrativas colombianas a departamentos
    """
    if not state:
        return state
    
    state_lower = state.lower().strip()
    
    # Mapeo de regiones administrativas a departamentos
    region_mapping = {
        # Región Administrativa y de Planificación (RAP) Central
        "rap (especial) central": "Cundinamarca",
        "rap central": "Cundinamarca",
        "región central": "Cundinamarca",
        "central": "Cundinamarca",
        
        # RAP Caribe
        "rap (especial) caribe": "Atlántico",
        "rap caribe": "Atlántico",
        "región caribe": "Atlántico",
        "caribe": "Atlántico",
        
        # RAP Pacífico
        "rap (especial) pacífico": "Valle del Cauca",
        "rap pacífico": "Valle del Cauca",
        "región pacífico": "Valle del Cauca",
        "pacífico": "Valle del Cauca",
        
        # RAP Eje Cafetero
        "rap (especial) eje cafetero": "Risaralda",
        "rap eje cafetero": "Risaralda",
        "región eje cafetero": "Risaralda",
        "eje cafetero": "Risaralda",
        
        # RAP Orinoquía
        "rap (especial) orinoquía": "Meta",
        "rap orinoquía": "Meta",
        "región orinoquía": "Meta",
        "orinoquía": "Meta",
        
        # RAP Amazonía
        "rap (especial) amazonía": "Caquetá",
        "rap amazonía": "Caquetá",
        "región amazonía": "Caquetá",
        "amazonía": "Caquetá",
        
        # Casos específicos conocidos
        "cundinamarca": "Cundinamarca",
        "antioquia": "Antioquia",
        "valle del cauca": "Valle del Cauca",
        "atlántico": "Atlántico",
        "bolívar": "Bolívar",
        "santander": "Santander",
        "norte de santander": "Norte de Santander",
        "tolima": "Tolima",
        "risaralda": "Risaralda",
        "magdalena": "Magdalena",
        "cesar": "Cesar",
        "córdoba": "Córdoba",
        "huila": "Huila",
        "meta": "Meta",
        "boyacá": "Boyacá",
        "caquetá": "Caquetá",
        "cauca": "Cauca",
        "chocó": "Chocó",
        "la guajira": "La Guajira",
        "san andrés y providencia": "San Andrés y Providencia"
    }
    
    # Buscar coincidencia exacta
    if state_lower in region_mapping:
        mapped_department = region_mapping[state_lower]
        logger.info(f"🗺️ Mapeando región '{state}' -> departamento '{mapped_department}'")
        return mapped_department
    
    # Buscar coincidencia parcial
    for region, department in region_mapping.items():
        if region in state_lower or state_lower in region:
            logger.info(f"🗺️ Mapeando región (parcial) '{state}' -> departamento '{department}'")
            return department
    
    # Si no se encuentra mapeo, devolver el estado original
    return state

async def query_geonames_api(city_input: str, country_hint: str = "colombia") -> Dict[str, Any]:
    """
    Consulta la API de GeoNames para obtener información geográfica
    """
    try:
        url = "http://api.geonames.org/searchJSON"
        
        params = {
            "q": city_input,
            "maxRows": 3,
            "username": "demo",  # Usar demo para pruebas
            "country": "CO",  # Buscar primero en Colombia
            "featureClass": "P",  # Solo lugares poblados
            "orderby": "population"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    geonames = data.get("geonames", [])
                    
                    if geonames:
                        result = geonames[0]  # Tomar el más poblado
                        
                        return {
                            "city": result.get("name", ""),
                            "state": result.get("adminName1", ""),
                            "country": result.get("countryName", "Colombia"),
                            "confidence": 0.7 if result.get("population", 0) > 1000 else 0.5,
                            "source": "geonames"
                        }
        
        return {"confidence": 0.0}
        
    except Exception as e:
        logger.error(f"Error consultando GeoNames: {e}")
        return {"confidence": 0.0}

async def query_google_geocoding(city_input: str, country_hint: str = "colombia") -> Dict[str, Any]:
    """
    Consulta la API de Google Geocoding (si está disponible)
    """
    try:
        # Por ahora retornar sin resultados ya que requiere API key
        # En el futuro se puede implementar si se tiene acceso
        return {"confidence": 0.0}
        
    except Exception as e:
        logger.error(f"Error consultando Google Geocoding: {e}")
        return {"confidence": 0.0}

def has_ambiguous_cities(results: List[Dict[str, Any]]) -> bool:
    """
    Verifica si hay ciudades ambiguas (mismo nombre, diferentes ubicaciones)
    """
    if len(results) < 2:
        return False
    
    # Crear un conjunto de ubicaciones únicas
    unique_locations = set()
    for result in results:
        city = result.get("city", "").strip()
        state = result.get("state", "")
        country = result.get("country", "")
        location_key = f"{city}|{state}|{country}"
        unique_locations.add(location_key)
    
    # Si hay más de una ubicación única, hay ambigüedad
    logger.info(f"🔍 Ubicaciones únicas encontradas: {len(unique_locations)}")
    for location in unique_locations:
        logger.info(f"   📍 {location}")
    
    return len(unique_locations) > 1

def extract_city_options(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extrae las opciones de ciudades para mostrar al usuario
    """
    options = []
    for i, result in enumerate(results, 1):
        city = result.get("city", "")
        state = result.get("state", "")
        country = result.get("country", "")
        
        option = {
            "id": i,
            "city": city,
            "state": state,
            "country": country,
            "full_location": f"{city}, {state}, {country}" if state and country else city
        }
        options.append(option)
    
    return options

async def generate_clarification_question(city_input: str, results: List[Dict[str, Any]]) -> str:
    """
    Genera una pregunta de aclaración usando IA cuando hay ciudades ambiguas
    """
    try:
        # Construir lista de opciones para la IA
        options_text = ""
        for i, result in enumerate(results, 1):
            city = result.get("city", "")
            state = result.get("state", "")
            country = result.get("country", "")
            options_text += f"{i}. {city}, {state}, {country}\n"
        
        # Generar pregunta simple por ahora (sin IA)
        question = f"Encontré varias ciudades llamadas {city_input}. ¿Podrías confirmar cuál es la correcta?\n\n{options_text}\nPor favor responde con el número de la opción que corresponde a tu ubicación."
        
        logger.info(f"🤖 IA generó pregunta de aclaración: {question}")
        return question
        
    except Exception as e:
        logger.error(f"Error generando pregunta de aclaración: {e}")
        # Fallback: pregunta simple
        options_text = ""
        for i, result in enumerate(results, 1):
            city = result.get("city", "")
            state = result.get("state", "")
            country = result.get("country", "")
            options_text += f"{i}. {city}, {state}, {country}\n"
        
        return f"Encontré varias ciudades llamadas {city_input}. ¿Podrías confirmar cuál es la correcta?\n\n{options_text}\nPor favor responde con el número de la opción que corresponde a tu ubicación."

async def analyze_external_results_with_ai(city_input: str, external_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Usa IA para analizar y validar los resultados de fuentes externas
    """
    try:
        if not external_results:
            return await normalize_city_with_ai_only(city_input)
        
        # Por ahora, usar el mejor resultado externo
        if external_results:
            best_external = max(external_results, key=lambda x: x.get("confidence", 0))
            return best_external
        
        return {
            "city": city_input,
            "state": None,
            "country": "Colombia",
            "confidence": 0.3,
            "source": "fallback"
        }
        
    except Exception as e:
        logger.error(f"Error en análisis con IA: {e}")
        return {
            "city": city_input,
            "state": None,
            "country": "Colombia",
            "confidence": 0.1,
            "source": "fallback"
        }

async def normalize_city_with_ai_only(city_input: str) -> Dict[str, Any]:
    """
    Normaliza ciudad usando solo IA (fallback cuando no hay fuentes externas)
    """
    try:
        # Por ahora, fallback simple
        return {
            "city": city_input,
            "state": None,
            "country": "Colombia",
            "confidence": 0.1,
            "source": "ai_only"
        }
    except Exception as e:
        logger.error(f"Error con IA: {e}")
        return {
            "city": city_input,
            "state": None,
            "country": "Colombia",
            "confidence": 0.1,
            "source": "ai_error"
        }

async def interpret_natural_selection(user_response: str, options: List[Dict], city_input: str) -> int:
    """
    Interpreta la respuesta del usuario en lenguaje natural para seleccionar una opción de ciudad
    """
    try:
        # Importar el servicio de IA
        from chatbot_ai_service.services.ai_service import AIService
        ai_service = AIService()
        
        # Crear el prompt para la IA
        options_text = "\n".join([f"{i+1}. {opt.get('full_location', '')}" for i, opt in enumerate(options)])
        
        prompt = f"""
        El usuario escribió la ciudad "{city_input}" y le mostré estas opciones:
        
        {options_text}
        
        El usuario respondió: "{user_response}"
        
        PRIMERO: Verifica si la respuesta del usuario es una PREGUNTA INFORMATIVA que NO está relacionada con la selección de ciudad.
        
        PREGUNTAS INFORMATIVAS (NO son selecciones de ciudad):
        - Preguntas sobre personas: "¿quién es...?", "¿qué hace...?", "¿cómo es...?"
        - Preguntas sobre el proceso: "¿por qué me preguntas esto?", "¿para qué necesitas mi ciudad?"
        - Preguntas generales: "¿qué es esto?", "¿cómo funciona?", "¿puedo cambiar mi respuesta?"
        - Preguntas sobre el sistema: "¿eres un bot?", "¿hay un humano disponible?"
        
        Si la respuesta es una PREGUNTA INFORMATIVA, responde "NO_ES_SELECCION".
        
        SEGUNDO: Si NO es una pregunta informativa, analiza si es una selección de ciudad válida:
        
        FORMAS DE RESPUESTA VÁLIDAS:
        - Números: "1", "2", "3", "la primera", "la segunda", "la última"
        - Países: "Colombia", "España", "Estados Unidos", "México", "Argentina", etc.
        - Regiones/Estados: "Cundinamarca", "Madrid", "Iowa", "California", "Buenos Aires", etc.
        - Referencias geográficas: "europa", "américa", "latinoamérica", "norteamérica"
        - Referencias de ubicación: "en españa", "de colombia", "en europa", "en américa"
        - Referencias de distancia: "la más cercana", "la más lejana"
        - Referencias de tamaño: "la más grande", "la capital", "la principal"
        
        REGLAS DE INTERPRETACIÓN:
        1. Si menciona un país, busca la opción que contenga ese país
        2. Si menciona una región/estado, busca la opción que contenga esa región
        3. Si menciona "europa", busca opciones de países europeos (España, Francia, etc.)
        4. Si menciona "américa" o "latinoamérica", busca opciones de países americanos
        5. Si menciona "la primera", "la segunda", etc., usa el número correspondiente
        6. Si menciona "la más cercana" o "la más grande", usa tu criterio geográfico
        
        Responde SOLO con:
        - "NO_ES_SELECCION" si es una pregunta informativa
        - El número de la opción (1, 2, o 3) si es una selección válida
        - "NO_CLARO" si no puedes determinar qué es
        
        Ejemplos de interpretación:
        - "¿quién es el candidato?" -> NO_ES_SELECCION
        - "¿por qué me preguntas esto?" -> NO_ES_SELECCION
        - "1" -> 1
        - "la primera" -> 1
        - "Colombia" -> 1 (si la opción 1 es de Colombia)
        - "España" -> 2 (si la opción 2 es de España)
        - "en españa" -> 2 (si la opción 2 es de España)
        - "europa" -> 2 (si la opción 2 es de España/Europa)
        - "Madrid" -> 2 (si la opción 2 es de Madrid)
        - "Estados Unidos" -> 3 (si la opción 3 es de Estados Unidos)
        - "américa" -> 3 (si la opción 3 es de América)
        - "la más grande" -> 3 (si la opción 3 es la ciudad más grande)
        - "no sé" -> NO_CLARO
        """
        
        # Usar el servicio de IA para interpretar
        response = await ai_service.generate_response(prompt, "system")
        
        if response:
            response = response.strip()
            
            # Si la IA detecta que NO es una selección de ciudad
            if response == "NO_ES_SELECCION":
                logger.info(f"🔍 IA detectó que '{user_response}' NO es una selección de ciudad")
                return None
            
            # Si es un número válido
            if response.isdigit():
                option_num = int(response)
                if 1 <= option_num <= len(options):
                    logger.info(f"✅ IA interpretó '{user_response}' como opción {option_num}")
                    return option_num
        
        logger.warn(f"❌ IA no pudo interpretar claramente: '{user_response}' -> '{response}'")
        return None
        
    except Exception as e:
        logger.error(f"Error interpretando selección natural: {e}")
        return None

def select_best_result(ai_analysis: Dict[str, Any], external_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Selecciona el mejor resultado basado en análisis de IA y resultados externos
    """
    try:
        # Si tenemos análisis de IA con buena confianza, usarlo
        if ai_analysis.get("confidence", 0) > 0.7:
            logger.info(f"🎯 Usando resultado de IA: {ai_analysis}")
            return ai_analysis
        
        # Si no, usar el mejor resultado externo
        if external_results:
            best_external = max(external_results, key=lambda x: x.get("confidence", 0))
            if best_external.get("confidence", 0) > 0.5:
                logger.info(f"🌐 Usando mejor resultado externo: {best_external}")
                return best_external
        
        # Fallback: usar análisis de IA aunque tenga baja confianza
        if ai_analysis:
            logger.info(f"🤖 Usando análisis de IA (baja confianza): {ai_analysis}")
            return ai_analysis
        
        # Último recurso
        return {
            "city": "Ciudad no encontrada",
            "state": None,
            "country": "Colombia",
            "confidence": 0.1,
            "source": "fallback_final"
        }
        
    except Exception as e:
        logger.error(f"Error seleccionando mejor resultado: {e}")
        return {
            "city": "Error",
            "state": None,
            "country": "Colombia",
            "confidence": 0.0,
            "source": "error"
        }

def check_city_nicknames(city_input: str) -> Dict[str, Any]:
    """
    Verifica si la entrada es un sobrenombre/apodo conocido de una ciudad
    """
    if not city_input:
        return None
    
    text = city_input.strip().lower()
    
    # Diccionario de apodos/alias → (city, state, country)
    nick_map = {
        # Bogotá
        "la nevera": ("Bogotá", "Cundinamarca", "Colombia"),
        "bogota": ("Bogotá", "Cundinamarca", "Colombia"),
        "bogotá": ("Bogotá", "Cundinamarca", "Colombia"),
        "atenas suramericana": ("Bogotá", "Cundinamarca", "Colombia"),
        "la atenas suramericana": ("Bogotá", "Cundinamarca", "Colombia"),
        "atenas sudamericana": ("Bogotá", "Cundinamarca", "Colombia"),
        "la atenas sudamericana": ("Bogotá", "Cundinamarca", "Colombia"),
        
        # Medellín
        "medallo": ("Medellín", "Antioquia", "Colombia"),
        "ciudad de la eterna primavera": ("Medellín", "Antioquia", "Colombia"),
        "la ciudad de la eterna primavera": ("Medellín", "Antioquia", "Colombia"),
        "medellin": ("Medellín", "Antioquia", "Colombia"),
        "medellín": ("Medellín", "Antioquia", "Colombia"),
        
        # Barranquilla
        "la arenosa": ("Barranquilla", "Atlántico", "Colombia"),
        "puerta de oro de colombia": ("Barranquilla", "Atlántico", "Colombia"),
        "la puerta de oro de colombia": ("Barranquilla", "Atlántico", "Colombia"),
        "curramba": ("Barranquilla", "Atlántico", "Colombia"),
        "barranquilla": ("Barranquilla", "Atlántico", "Colombia"),
        
        # Cali
        "la sucursal del cielo": ("Cali", "Valle del Cauca", "Colombia"),
        "sultana del valle": ("Cali", "Valle del Cauca", "Colombia"),
        "cali": ("Cali", "Valle del Cauca", "Colombia"),
        
        # Bucaramanga
        "la ciudad bonita": ("Bucaramanga", "Santander", "Colombia"),
        "ciudad de los parques": ("Bucaramanga", "Santander", "Colombia"),
        "bucaramanga": ("Bucaramanga", "Santander", "Colombia"),
        
        # Buga
        "ciudad señora": ("Buga", "Valle del Cauca", "Colombia"),
        
        # Cartagena
        "ciudad heroica": ("Cartagena", "Bolívar", "Colombia"),
        "la ciudad heróica": ("Cartagena", "Bolívar", "Colombia"),
        "corralito de piedra": ("Cartagena", "Bolívar", "Colombia"),
        
        # Chía
        "ciudad de la luna": ("Chía", "Cundinamarca", "Colombia"),
        
        # Cúcuta
        "perla del norte": ("Cúcuta", "Norte de Santander", "Colombia"),
        
        # Ibagué
        "ciudad musical": ("Ibagué", "Tolima", "Colombia"),
        
        # Ipiales
        "ciudad de las nubes verdes": ("Ipiales", "Nariño", "Colombia"),
        
        # Montería
        "perla del sinu": ("Montería", "Córdoba", "Colombia"),
        "perla del sinú": ("Montería", "Córdoba", "Colombia"),
        
        # Neiva
        "ciudad amable": ("Neiva", "Huila", "Colombia"),
        
        # Pasto
        "ciudad sorpresa": ("Pasto", "Nariño", "Colombia"),
        
        # Pereira
        "la querendona": ("Pereira", "Risaralda", "Colombia"),
        
        # Popayán
        "ciudad blanca": ("Popayán", "Cauca", "Colombia"),
        
        # Santa Marta
        "la perla de américa": ("Santa Marta", "Magdalena", "Colombia"),
        
        # Tunja
        "ciudad universitaria": ("Tunja", "Boyacá", "Colombia"),
        
        # Villavicencio
        "la puerta del llano": ("Villavicencio", "Meta", "Colombia"),
        
        # Zipaquirá
        "capital salinera": ("Zipaquirá", "Cundinamarca", "Colombia"),
    }
    
    # Match exacto por clave completa
    if text in nick_map:
        city, state, country = nick_map[text]
        return {"city": city, "state": state, "country": country}
    
    # Búsqueda por inclusión de apodos conocidos en frases completas
    for key, (city, state, country) in nick_map.items():
        if key in text:
            return {"city": city, "state": state, "country": country}
    
    # Regex para capturar patrones frecuentes en frases
    import re
    patterns = [
        r"vivo\s+en\s+la\s+nevera",
        r"estoy\s+en\s+la\s+arenosa",
    ]
    for pat in patterns:
        if re.search(pat, text):
            # Reutilizar nick_map via búsqueda por inclusión
            for key, (city, state, country) in nick_map.items():
                if key in text:
                    return {"city": city, "state": state, "country": country}
    
    return None

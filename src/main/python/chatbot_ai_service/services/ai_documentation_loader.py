"""
Servicios de carga de documentación para IA

Obtiene documentación dinámica desde la configuración de tenants en Firestore
"""
import logging
import json
import re
import asyncio
from typing import Dict, List, Optional

from chatbot_ai_service.services.tenant_service import get_tenant_service

logger = logging.getLogger(__name__)


async def load_tenant_documentation(tenant_id: str, gcs_bucket: str = None, gcs_path: str = None) -> str:
    """
    Carga la documentación del tenant desde la configuración de Firestore.
    
    Args:
        tenant_id: ID del tenant
        gcs_bucket: Bucket de GCS (opcional, para carga futura desde storage)
        gcs_path: Ruta en GCS (opcional, para carga futura desde storage)
        
    Returns:
        Documentación del tenant como string
    """
    try:
        logger.info(f"Cargando documentación para tenant: {tenant_id}")
        
        # Obtener configuración del tenant desde Firestore
        tenant_service = get_tenant_service()
        tenant_config = tenant_service.get_tenant_config(tenant_id)
        
        if not tenant_config:
            logger.warning(f"No se encontró configuración para tenant: {tenant_id}")
            return ""
        
        # Construir documentación basada en la configuración del tenant
        contact_name = tenant_config.branding.contact_name if tenant_config.branding else "la campaña"
        welcome_message = tenant_config.branding.welcome_message if tenant_config.branding else ""
        greeting_message = tenant_config.branding.greeting_message if tenant_config.branding else ""
        
        documentation = f"""
CANDIDATO: {contact_name}
CAMPAÑA: {tenant_id}

MENSAJE DE BIENVENIDA:
{welcome_message}

MENSAJE DE SALUDO:
{greeting_message if greeting_message else 'Saludo estándar de campaña'}

INFORMACIÓN DE CONTACTO:
- WhatsApp: {tenant_config.numero_whatsapp or 'No disponible'}
- Calendly: {tenant_config.link_calendly or 'No disponible'}
- Formularios: {tenant_config.link_forms or 'No disponible'}
- URL de Privacidad: {tenant_config.branding.privacy_url if tenant_config.branding else 'No disponible'}

CONFIGURACIÓN:
- Tipo de tenant: {tenant_config.tenant_type or 'No especificado'}
- Estado: {tenant_config.status or 'active'}
- Proyecto de Firebase: {tenant_config.client_project_id}
"""
        
        # Si hay URL de documentación en GCS, agregar nota
        if tenant_config.ai_config and tenant_config.ai_config.documentation_bucket_url:
            documentation += f"\nDOCUMENTACIÓN ADICIONAL:\n- URL: {tenant_config.ai_config.documentation_bucket_url}\n"
            documentation += "- TODO: Implementar carga desde GCS Storage\n"
        
        logger.info(f"Documentación generada para tenant {tenant_id}: {len(documentation)} caracteres")
        return documentation
        
    except Exception as e:
        logger.error(f"Error cargando documentación del tenant {tenant_id}: {str(e)}")
        return f"CANDIDATO: Campaña {tenant_id}\n\nInformación disponible: Documentación no disponible temporalmente."


def parse_documentation_structure(documentation: str) -> Dict[str, str]:
    """
    Parsea la documentación y extrae información estructurada.
    
    Args:
        documentation: Documentación del tenant como string
        
    Returns:
        Diccionario con información estructurada
    """
    try:
        logger.debug("Parseando estructura de documentación")
        
        # Inicializar la estructura
        structured_info = {
            "candidate_name": "",
            "party": "",
            "position": "",
            "contact_info": {},
            "proposals": [],
            "objectives": [],
            "volunteer_areas": []
        }
        
        # Extraer nombre del candidato
        candidate_match = re.search(r"CANDIDATO:\s*(.+?)(?:\n|$)", documentation)
        if candidate_match:
            structured_info["candidate_name"] = candidate_match.group(1).strip()
        
        # Extraer partido
        party_match = re.search(r"PARTIDO:\s*(.+?)(?:\n|$)", documentation)
        if party_match:
            structured_info["party"] = party_match.group(1).strip()
        
        # Extraer cargo
        position_match = re.search(r"CARGO:\s*(.+?)(?:\n|$)", documentation)
        if position_match:
            structured_info["position"] = position_match.group(1).strip()
        
        # Extraer información de contacto
        contact_section = re.search(r"INFORMACIÓN DE CONTACTO:(.+?)(?=\n\n|\Z)", documentation, re.DOTALL)
        if contact_section:
            contact_lines = contact_section.group(1).strip().split("\n")
            for line in contact_lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    structured_info["contact_info"][key.strip("- ")] = value.strip()
        
        # Extraer propuestas
        proposals_section = re.search(r"PROPUESTAS PRINCIPALES:(.+?)(?=\n\n|\Z)", documentation, re.DOTALL)
        if proposals_section:
            proposal_lines = proposals_section.group(1).strip().split("\n")
            for line in proposal_lines:
                line = line.strip()
                if line and line[0].isdigit():
                    # Remover número y punto inicial
                    proposal = re.sub(r"^\d+\.\s*", "", line)
                    structured_info["proposals"].append(proposal)
        
        # Extraer objetivos
        objectives_section = re.search(r"OBJETIVOS DE CAMPAÑA:(.+?)(?=\n\n|\Z)", documentation, re.DOTALL)
        if objectives_section:
            objective_lines = objectives_section.group(1).strip().split("\n")
            for line in objective_lines:
                line = line.strip()
                if line.startswith("-"):
                    objective = line[1:].strip()
                    structured_info["objectives"].append(objective)
        
        # Extraer áreas de voluntariado
        volunteer_section = re.search(r"VOLUNTARIOS:(.+?)(?=\n\n|\Z)", documentation, re.DOTALL)
        if volunteer_section:
            volunteer_lines = volunteer_section.group(1).strip().split("\n")
            for line in volunteer_lines:
                line = line.strip()
                if line.startswith("-"):
                    area = line[1:].strip()
                    structured_info["volunteer_areas"].append(area)
        
        logger.debug(f"Estructura parseada: {structured_info}")
        return structured_info
        
    except Exception as e:
        logger.error(f"Error parseando documentación: {str(e)}")
        return {
            "candidate_name": "",
            "party": "",
            "position": "",
            "contact_info": {},
            "proposals": [],
            "objectives": [],
            "volunteer_areas": []
        }


def extract_key_information(documentation: str, keys: List[str]) -> Dict[str, str]:
    """
    Extrae información clave específica de la documentación.
    
    Args:
        documentation: Documentación del tenant como string
        keys: Lista de claves a extraer (ej: ["CANDIDATO", "PARTIDO", "CARGO"])
        
    Returns:
        Diccionario con la información extraída
    """
    try:
        logger.debug(f"Extrayendo información clave: {keys}")
        
        extracted_info = {}
        
        for key in keys:
            # Buscar el patrón "CLAVE: valor"
            pattern = rf"{re.escape(key)}:\s*(.+?)(?:\n|$)"
            match = re.search(pattern, documentation)
            if match:
                extracted_info[key] = match.group(1).strip()
            else:
                extracted_info[key] = None
        
        logger.debug(f"Información extraída: {extracted_info}")
        return extracted_info
        
    except Exception as e:
        logger.error(f"Error extrayendo información clave: {str(e)}")
        return {key: None for key in keys}


def format_documentation_for_ai(documentation: str, max_length: int = 2000) -> str:
    """
    Formatea la documentación para ser usada en prompts de IA.
    
    Args:
        documentation: Documentación del tenant como string
        max_length: Longitud máxima en caracteres
        
    Returns:
        Documentación formateada y limitada
    """
    try:
        logger.debug(f"Formateando documentación (max_length={max_length})")
        
        # Si la documentación es menor que el máximo, retornarla tal cual
        if len(documentation) <= max_length:
            return documentation
        
        # Si es más larga, parsear y priorizar información
        structured = parse_documentation_structure(documentation)
        
        # Construir versión resumida
        formatted = f"""
CANDIDATO: {structured['candidate_name']}
PARTIDO: {structured['party']}
CARGO: {structured['position']}

PROPUESTAS PRINCIPALES:
{chr(10).join(f"- {p}" for p in structured['proposals'][:5])}

CONTACTO:
{chr(10).join(f"- {k}: {v}" for k, v in list(structured['contact_info'].items())[:3])}
"""
        
        return formatted.strip()
        
    except Exception as e:
        logger.error(f"Error formateando documentación: {str(e)}")
        # Fallback: truncar la documentación original
        return documentation[:max_length] + "..."

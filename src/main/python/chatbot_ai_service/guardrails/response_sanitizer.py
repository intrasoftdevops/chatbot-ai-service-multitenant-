"""
Response Sanitizer - Sanitizador de Respuestas

Limpia y sanitiza respuestas que violan guardrails:
- Remueve claims no soportados
- Reemplaza números no verificados
- Elimina lenguaje especulativo
- Agrega disclaimers cuando es necesario

Este componente actúa como último filtro de seguridad.
"""

import logging
import re
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)


class ResponseSanitizer:
    """
    Sanitizador de respuestas
    
    Limpia respuestas que violan guardrails, removiendo
    o reemplazando partes problemáticas.
    """
    
    def __init__(self, aggressive_mode: bool = False):
        """
        Inicializa el ResponseSanitizer
        
        Args:
            aggressive_mode: Si True, es más estricto en la sanitización
        """
        self.aggressive_mode = aggressive_mode
        logger.info(f"ResponseSanitizer inicializado (aggressive_mode={aggressive_mode})")
    
    def sanitize(
        self,
        response: str,
        documents: List[Any],
        guardrail_result: Optional[Any] = None
    ) -> Tuple[str, List[str]]:
        """
        Sanitiza la respuesta removiendo contenido problemático
        
        Args:
            response: Respuesta a sanitizar
            documents: Documentos fuente para verificación
            guardrail_result: Resultado de GuardrailVerifier (opcional)
            
        Returns:
            Tupla (respuesta_sanitizada, lista_de_cambios)
        """
        logger.info("🧹 Sanitizando respuesta...")
        
        sanitized = response
        changes = []
        
        # 1. Remover lenguaje especulativo
        sanitized, spec_changes = self._remove_speculative_language(sanitized)
        changes.extend(spec_changes)
        
        # 2. Remover o marcar números no verificados
        if documents:
            sanitized, num_changes = self._sanitize_numbers(sanitized, documents)
            changes.extend(num_changes)
        
        # 3. Remover opiniones personales
        sanitized, opinion_changes = self._remove_personal_opinions(sanitized)
        changes.extend(opinion_changes)
        
        # 4. Agregar disclaimers si es necesario
        if guardrail_result and not guardrail_result.all_passed:
            sanitized, disclaimer = self._add_disclaimer(sanitized, guardrail_result)
            if disclaimer:
                changes.append("disclaimer_added")
        
        if changes:
            logger.info(f"✅ Sanitización completada: {len(changes)} cambios realizados")
        else:
            logger.debug("No se requirieron cambios de sanitización")
        
        return sanitized, changes
    
    def _remove_speculative_language(self, response: str) -> Tuple[str, List[str]]:
        """Remueve o reemplaza lenguaje especulativo"""
        changes = []
        sanitized = response
        
        # Palabras especulativas a remover/reemplazar
        speculative_replacements = {
            r'\baproximadamente\s+': '',
            r'\balrededor de\s+': '',
            r'\bmás o menos\s+': '',
            r'\bcercano a\s+': '',
            r'\bpodría ser\s+': 'es ',
            r'\bposiblemente\s+': '',
            r'\bprobablemente\s+': '',
            r'\bquizás\s+': '',
            r'\btal vez\s+': '',
        }
        
        for pattern, replacement in speculative_replacements.items():
            if re.search(pattern, sanitized, re.IGNORECASE):
                sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
                changes.append(f"removed_speculative: {pattern}")
        
        return sanitized, changes
    
    def _sanitize_numbers(
        self,
        response: str,
        documents: List[Any]
    ) -> Tuple[str, List[str]]:
        """Sanitiza números no verificados"""
        changes = []
        
        # Obtener contenido de documentos
        doc_contents = []
        for doc in documents:
            if hasattr(doc, 'content'):
                doc_contents.append(doc.content)
            elif isinstance(doc, str):
                doc_contents.append(doc)
        
        all_docs_text = " ".join(doc_contents)
        
        # Encontrar números en la respuesta
        number_pattern = r'\b\d+(?:[.,]\d+)*\b'
        numbers = re.finditer(number_pattern, response)
        
        sanitized = response
        for match in numbers:
            number = match.group()
            clean_number = number.replace(',', '').replace('.', '')
            
            # Verificar si el número está en documentos
            if clean_number not in all_docs_text.replace(',', '').replace('.', ''):
                # Número no verificado
                if self.aggressive_mode:
                    # Remover el número completamente
                    sanitized = sanitized.replace(number, '[dato no verificado]')
                    changes.append(f"removed_unverified_number: {number}")
                else:
                    # Agregar disclaimer al número
                    sanitized = sanitized.replace(number, f"{number}*")
                    changes.append(f"marked_unverified_number: {number}")
        
        # Si agregamos asteriscos, agregar nota al final
        if '*' in sanitized and '*' not in response:
            sanitized += "\n\n*Nota: Algunos datos numéricos requieren verificación con el equipo de campaña."
        
        return sanitized, changes
    
    def _remove_personal_opinions(self, response: str) -> Tuple[str, List[str]]:
        """Remueve expresiones de opinión personal"""
        changes = []
        sanitized = response
        
        # Frases de opinión personal a remover
        opinion_phrases = [
            r'creo que\s+',
            r'pienso que\s+',
            r'me parece que\s+',
            r'en mi opinión,?\s+',
            r'personalmente,?\s+',
            r'yo considero que\s+',
            r'desde mi punto de vista,?\s+',
        ]
        
        for pattern in opinion_phrases:
            if re.search(pattern, sanitized, re.IGNORECASE):
                sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
                changes.append(f"removed_opinion: {pattern}")
        
        return sanitized, changes
    
    def _add_disclaimer(
        self,
        response: str,
        guardrail_result: Any
    ) -> Tuple[str, bool]:
        """Agrega disclaimer si la respuesta tiene problemas"""
        
        if guardrail_result.critical_failures > 0:
            disclaimer = "\n\n⚠️ **Nota importante:** Esta respuesta puede contener información que requiere verificación adicional con el equipo de campaña."
            return response + disclaimer, True
        elif guardrail_result.warnings > 2:
            disclaimer = "\n\n💡 **Sugerencia:** Para información más detallada, contacta directamente al equipo de campaña."
            return response + disclaimer, True
        
        return response, False
    
    def clean_formatting(self, response: str) -> str:
        """
        Limpia formato de la respuesta
        
        Args:
            response: Respuesta a limpiar
            
        Returns:
            Respuesta con formato limpio
        """
        # Remover espacios múltiples
        cleaned = re.sub(r' +', ' ', response)
        
        # Remover líneas vacías múltiples
        cleaned = re.sub(r'\n\n\n+', '\n\n', cleaned)
        
        # Limpiar espacios al inicio y final
        cleaned = cleaned.strip()
        
        return cleaned
    
    def ensure_citations(self, response: str, min_citations: int = 1) -> Tuple[str, bool]:
        """
        Asegura que la respuesta tenga citas
        
        Args:
            response: Respuesta a verificar
            min_citations: Mínimo número de citas requeridas
            
        Returns:
            Tupla (respuesta, tiene_citas_suficientes)
        """
        # Contar citas
        citation_patterns = [
            r'\[Documento\s+\d+\]',
            r'\[Doc\s+\d+\]',
            r'\[Fuente\s+\d+\]'
        ]
        
        total_citations = 0
        for pattern in citation_patterns:
            total_citations += len(re.findall(pattern, response, re.IGNORECASE))
        
        has_enough = total_citations >= min_citations
        
        if not has_enough and self.aggressive_mode:
            # Agregar nota sobre falta de citas
            response += "\n\n⚠️ **Nota:** Esta información requiere verificación de fuentes con el equipo de campaña."
        
        return response, has_enough
    
    def split_claims(self, response: str) -> List[str]:
        """
        Divide la respuesta en claims individuales
        
        Args:
            response: Respuesta completa
            
        Returns:
            Lista de claims
        """
        # Dividir por oraciones
        sentences = re.split(r'[.!?]+\s+', response)
        
        # Filtrar oraciones muy cortas o vacías
        claims = [s.strip() for s in sentences if len(s.split()) >= 3]
        
        return claims
    
    def verify_claim_support(
        self,
        claim: str,
        documents: List[Any]
    ) -> bool:
        """
        Verifica si un claim específico está soportado
        
        Args:
            claim: Claim a verificar
            documents: Documentos fuente
            
        Returns:
            True si el claim está soportado
        """
        claim_lower = claim.lower()
        
        # Obtener contenido de documentos
        for doc in documents:
            content = ""
            if hasattr(doc, 'content'):
                content = doc.content.lower()
            elif isinstance(doc, str):
                content = doc.lower()
            
            # Buscar palabras clave del claim en el documento
            claim_words = set(re.findall(r'\b\w+\b', claim_lower))
            claim_words = {w for w in claim_words if len(w) > 3}  # Solo palabras >3 chars
            
            if not claim_words:
                continue
            
            # Contar cuántas palabras del claim están en el documento
            matches = sum(1 for word in claim_words if word in content)
            
            # Si >60% de las palabras están, considerar soportado
            if matches / len(claim_words) > 0.6:
                return True
        
        return False


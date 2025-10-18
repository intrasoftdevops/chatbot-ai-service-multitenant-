"""
Source Verifier - Verificador de fuentes y respuestas

Verifica que las respuestas generadas estén fundamentadas en los
documentos fuente y agrega citas apropiadas.

Características:
- Verificación básica de claims
- Detección de posibles alucinaciones
- Generación de citas
- Scoring de confiabilidad
"""

import logging
import re
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Resultado de verificación de una respuesta"""
    is_verified: bool
    confidence: float  # 0-1
    unsupported_claims: List[str]
    sources_used: List[Dict[str, Any]]
    hallucination_risk: float  # 0-1
    recommendation: str


class SourceVerifier:
    """
    Verificador de fuentes y respuestas
    
    Valida que las respuestas generadas estén fundamentadas en
    los documentos fuente y no contengan alucinaciones.
    """
    
    def __init__(self):
        """Inicializa el SourceVerifier"""
        self.min_confidence_threshold = 0.5
        logger.info("SourceVerifier inicializado")
    
    def _extract_sentences(self, text: str) -> List[str]:
        """
        Extrae oraciones del texto
        
        Args:
            text: Texto a procesar
            
        Returns:
            Lista de oraciones
        """
        # Split por puntos, pero mantener abreviaturas comunes
        sentences = re.split(r'(?<![A-Z])\.(?![0-9])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def _extract_claims(self, response: str) -> List[str]:
        """
        Extrae claims (afirmaciones) de la respuesta
        
        Args:
            response: Respuesta generada
            
        Returns:
            Lista de claims extraídos
        """
        # Por ahora, usamos oraciones como claims
        claims = self._extract_sentences(response)
        
        # Filtrar claims muy cortos o sin contenido
        claims = [
            claim for claim in claims 
            if len(claim.split()) >= 3  # Al menos 3 palabras
        ]
        
        logger.debug(f"Extraídos {len(claims)} claims de la respuesta")
        return claims
    
    def _check_claim_in_document(
        self, 
        claim: str, 
        document_content: str
    ) -> Tuple[bool, float]:
        """
        Verifica si un claim está soportado por el documento
        
        Args:
            claim: Claim a verificar
            document_content: Contenido del documento
            
        Returns:
            Tupla (is_supported, confidence)
        """
        claim_lower = claim.lower()
        doc_lower = document_content.lower()
        
        # Extraer palabras clave del claim (sin stopwords)
        stopwords = {
            'el', 'la', 'los', 'las', 'un', 'una', 'de', 'del', 
            'a', 'al', 'en', 'por', 'para', 'con', 'que', 'es', 'son'
        }
        
        claim_words = set(re.findall(r'\b\w+\b', claim_lower))
        claim_words = claim_words - stopwords
        
        if not claim_words:
            return False, 0.0
        
        # Contar cuántas palabras clave están en el documento
        words_found = sum(1 for word in claim_words if word in doc_lower)
        
        # Calcular confidence basado en proporción de palabras encontradas
        confidence = words_found / len(claim_words)
        
        # Considerar soportado si > 60% de las palabras están presentes
        is_supported = confidence >= 0.6
        
        return is_supported, confidence
    
    def verify_response(
        self, 
        response: str, 
        source_documents: List[Any]
    ) -> VerificationResult:
        """
        Verifica que la respuesta esté fundamentada en los documentos
        
        Args:
            response: Respuesta generada a verificar
            source_documents: Documentos fuente (RetrievedDocument objects)
            
        Returns:
            VerificationResult con detalles de la verificación
        """
        logger.info("🔍 Verificando respuesta contra documentos fuente...")
        
        if not source_documents:
            logger.warning("⚠️ No hay documentos fuente para verificar")
            return VerificationResult(
                is_verified=False,
                confidence=0.0,
                unsupported_claims=[],
                sources_used=[],
                hallucination_risk=1.0,
                recommendation="No hay documentos fuente para verificar la respuesta"
            )
        
        # Extraer claims de la respuesta
        claims = self._extract_claims(response)
        
        if not claims:
            logger.debug("No se encontraron claims en la respuesta")
            return VerificationResult(
                is_verified=True,
                confidence=1.0,
                unsupported_claims=[],
                sources_used=[],
                hallucination_risk=0.0,
                recommendation="Respuesta sin claims específicos"
            )
        
        # Verificar cada claim contra todos los documentos
        unsupported_claims = []
        claim_confidences = []
        sources_used = set()
        
        for claim in claims:
            claim_supported = False
            max_confidence = 0.0
            
            for doc in source_documents:
                doc_content = getattr(doc, 'content', '')
                is_supported, confidence = self._check_claim_in_document(
                    claim, 
                    doc_content
                )
                
                if is_supported:
                    claim_supported = True
                    max_confidence = max(max_confidence, confidence)
                    sources_used.add(getattr(doc, 'doc_id', 'unknown'))
            
            if not claim_supported:
                unsupported_claims.append(claim)
                claim_confidences.append(0.0)
            else:
                claim_confidences.append(max_confidence)
        
        # Calcular métricas generales
        avg_confidence = sum(claim_confidences) / len(claim_confidences) if claim_confidences else 0.0
        hallucination_risk = len(unsupported_claims) / len(claims) if claims else 0.0
        is_verified = hallucination_risk < 0.3  # Menos del 30% de claims sin soporte
        
        # Generar recomendación
        if is_verified:
            recommendation = "✅ Respuesta verificada y fundamentada en documentos"
        elif hallucination_risk < 0.5:
            recommendation = "⚠️ Respuesta parcialmente verificada, algunos claims no tienen soporte claro"
        else:
            recommendation = "❌ Respuesta con alto riesgo de alucinación, mayoría de claims sin soporte"
        
        # Convertir sources_used a lista de dicts
        sources_list = [{"doc_id": doc_id} for doc_id in sources_used]
        
        result = VerificationResult(
            is_verified=is_verified,
            confidence=avg_confidence,
            unsupported_claims=unsupported_claims,
            sources_used=sources_list,
            hallucination_risk=hallucination_risk,
            recommendation=recommendation
        )
        
        logger.info(
            f"✅ Verificación completada - "
            f"Verified: {is_verified}, "
            f"Confidence: {avg_confidence:.2f}, "
            f"Hallucination Risk: {hallucination_risk:.2f}"
        )
        
        if unsupported_claims:
            logger.warning(
                f"⚠️ {len(unsupported_claims)} claims sin soporte detectados"
            )
        
        return result
    
    def add_citations(
        self, 
        response: str, 
        source_documents: List[Any]
    ) -> str:
        """
        Agrega citas a la respuesta
        
        Args:
            response: Respuesta original
            source_documents: Documentos fuente
            
        Returns:
            Respuesta con citas agregadas
        """
        if not source_documents:
            return response
        
        # Construir sección de fuentes
        sources_section = "\n\n📚 **Fuentes:**\n"
        
        for i, doc in enumerate(source_documents, 1):
            title = getattr(doc, 'title', 'Documento sin título')
            doc_id = getattr(doc, 'doc_id', 'unknown')
            score = getattr(doc, 'combined_score', 0.0)
            
            sources_section += f"[{i}] {title} (relevancia: {score:.0%})\n"
        
        # Agregar indicador de uso de fuentes
        header = "💡 *Respuesta basada en documentos de la campaña:*\n\n"
        
        return header + response + sources_section
    
    def generate_confidence_message(self, verification: VerificationResult) -> str:
        """
        Genera mensaje de confianza para el usuario
        
        Args:
            verification: Resultado de verificación
            
        Returns:
            Mensaje de confianza
        """
        if verification.is_verified and verification.confidence > 0.8:
            return "✅ Alta confiabilidad - Información verificada en documentos oficiales"
        elif verification.is_verified:
            return "✓ Información fundamentada en documentos disponibles"
        elif verification.hallucination_risk < 0.5:
            return "⚠️ Información parcialmente verificada - Algunos detalles pueden requerir confirmación"
        else:
            return "⚠️ Respuesta generada con información limitada - Se recomienda verificar con el equipo"


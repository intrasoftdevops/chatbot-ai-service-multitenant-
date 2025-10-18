"""
Guardrail Verifier - Verificador de Guardrails

Verifica que las respuestas cumplan con los guardrails establecidos:
- Sin números inventados
- Con citas apropiadas
- Sin claims no soportados
- Tono apropiado
- Admite ignorancia cuando corresponde

Este componente es una capa adicional de seguridad sobre SourceVerifier.
"""

import logging
import re
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GuardrailCheckResult:
    """Resultado de una verificación individual de guardrail"""
    passed: bool
    rule_name: str
    details: str
    severity: str  # 'critical', 'warning', 'info'


@dataclass
class GuardrailVerificationResult:
    """Resultado completo de verificación de guardrails"""
    all_passed: bool
    checks: List[GuardrailCheckResult]
    critical_failures: int
    warnings: int
    score: float  # 0-1
    recommendation: str


class GuardrailVerifier:
    """
    Verificador de guardrails estrictos
    
    Verifica múltiples aspectos de la respuesta para asegurar
    que cumpla con las reglas de guardrails establecidas.
    """
    
    def __init__(self, strict_mode: bool = True):
        """
        Inicializa el GuardrailVerifier
        
        Args:
            strict_mode: Si True, fallas críticas invalidan la respuesta
        """
        self.strict_mode = strict_mode
        logger.info(f"GuardrailVerifier inicializado (strict_mode={strict_mode})")
    
    def verify(
        self,
        response: str,
        documents: List[Any],
        query: str = ""
    ) -> GuardrailVerificationResult:
        """
        Verifica que la respuesta cumpla todos los guardrails
        
        Args:
            response: Respuesta a verificar
            documents: Documentos fuente
            query: Query original (opcional, para contexto)
            
        Returns:
            GuardrailVerificationResult con resultados detallados
        """
        logger.info("🛡️ Iniciando verificación de guardrails...")
        
        checks = []
        
        # 1. Verificar que tenga citas
        checks.append(self._check_has_citations(response))
        
        # 2. Verificar números (solo si hay documentos)
        if documents:
            checks.append(self._check_numbers(response, documents))
        
        # 3. Verificar tono apropiado
        checks.append(self._check_tone(response))
        
        # 4. Verificar que no haya lenguaje inventivo
        checks.append(self._check_no_speculative_language(response))
        
        # 5. Verificar longitud apropiada
        checks.append(self._check_length(response))
        
        # 6. Verificar formato de respuesta
        checks.append(self._check_format(response))
        
        # 7. Verificar que NO haya URLs/enlaces (seguridad)
        checks.append(self._check_no_urls(response))
        
        # Contar fallos críticos y warnings
        critical_failures = sum(1 for c in checks if not c.passed and c.severity == 'critical')
        warnings = sum(1 for c in checks if not c.passed and c.severity == 'warning')
        
        # Calcular score
        passed_checks = sum(1 for c in checks if c.passed)
        score = passed_checks / len(checks) if checks else 0.0
        
        # Determinar si pasa en general
        all_passed = critical_failures == 0 if self.strict_mode else score >= 0.7
        
        # Generar recomendación
        recommendation = self._generate_recommendation(
            all_passed, critical_failures, warnings, score
        )
        
        result = GuardrailVerificationResult(
            all_passed=all_passed,
            checks=checks,
            critical_failures=critical_failures,
            warnings=warnings,
            score=score,
            recommendation=recommendation
        )
        
        logger.info(
            f"✅ Verificación completada - "
            f"Passed: {all_passed}, Score: {score:.2f}, "
            f"Critical: {critical_failures}, Warnings: {warnings}"
        )
        
        return result
    
    def _check_has_citations(self, response: str) -> GuardrailCheckResult:
        """Verifica que la respuesta tenga citas"""
        # Buscar patrones de citas: [Documento N], [Doc N], etc.
        citation_patterns = [
            r'\[Documento\s+\d+\]',
            r'\[Doc\s+\d+\]',
            r'\[Fuente\s+\d+\]'
        ]
        
        has_citations = any(
            re.search(pattern, response, re.IGNORECASE)
            for pattern in citation_patterns
        )
        
        # También verificar sección de fuentes
        has_sources_section = "📚" in response or "Fuentes:" in response
        
        passed = has_citations or has_sources_section
        
        return GuardrailCheckResult(
            passed=passed,
            rule_name="has_citations",
            details="Citas encontradas" if passed else "Sin citas de fuentes",
            severity="critical" if not passed else "info"
        )
    
    def _check_numbers(
        self, 
        response: str, 
        documents: List[Any]
    ) -> GuardrailCheckResult:
        """Verifica que los números estén en los documentos"""
        # Extraer números de la respuesta
        numbers = re.findall(r'\b\d+(?:[.,]\d+)*\b', response)
        
        if not numbers:
            return GuardrailCheckResult(
                passed=True,
                rule_name="numbers_verified",
                details="No hay números en la respuesta",
                severity="info"
            )
        
        # Obtener contenido de documentos
        doc_contents = []
        for doc in documents:
            if hasattr(doc, 'content'):
                doc_contents.append(doc.content)
            elif isinstance(doc, str):
                doc_contents.append(doc)
        
        all_docs_text = " ".join(doc_contents)
        
        # Verificar cada número
        unverified_numbers = []
        for number in numbers:
            # Limpiar el número para comparación
            clean_number = number.replace(',', '').replace('.', '')
            
            # Buscar en documentos
            if clean_number not in all_docs_text.replace(',', '').replace('.', ''):
                unverified_numbers.append(number)
        
        passed = len(unverified_numbers) == 0
        
        details = f"Todos los {len(numbers)} números verificados" if passed else \
                 f"{len(unverified_numbers)}/{len(numbers)} números no verificados"
        
        return GuardrailCheckResult(
            passed=passed,
            rule_name="numbers_verified",
            details=details,
            severity="critical" if not passed else "info"
        )
    
    def _check_tone(self, response: str) -> GuardrailCheckResult:
        """Verifica que el tono sea apropiado"""
        response_lower = response.lower()
        
        # Palabras que indican tono inapropiado
        inappropriate_words = [
            "creo que", "pienso que", "me parece", "probablemente",
            "quizás", "tal vez", "supongo", "imagino"
        ]
        
        # Palabras de opinión personal
        personal_opinions = [
            "en mi opinión", "personalmente", "yo considero",
            "desde mi punto de vista"
        ]
        
        found_inappropriate = []
        for word in inappropriate_words + personal_opinions:
            if word in response_lower:
                found_inappropriate.append(word)
        
        passed = len(found_inappropriate) == 0
        
        details = "Tono profesional y objetivo" if passed else \
                 f"Lenguaje especulativo encontrado: {', '.join(found_inappropriate[:3])}"
        
        return GuardrailCheckResult(
            passed=passed,
            rule_name="appropriate_tone",
            details=details,
            severity="warning" if not passed else "info"
        )
    
    def _check_no_speculative_language(self, response: str) -> GuardrailCheckResult:
        """Verifica que no haya lenguaje especulativo"""
        response_lower = response.lower()
        
        speculative_phrases = [
            "aproximadamente", "alrededor de", "más o menos",
            "cercano a", "podría ser", "posiblemente",
            "se estima", "se calcula"
        ]
        
        found_speculative = []
        for phrase in speculative_phrases:
            if phrase in response_lower:
                found_speculative.append(phrase)
        
        # Permitir "aproximadamente" si viene con disclaimer
        if "aproximadamente" in found_speculative and "según" in response_lower:
            found_speculative.remove("aproximadamente")
        
        passed = len(found_speculative) == 0
        
        details = "Sin lenguaje especulativo" if passed else \
                 f"Lenguaje especulativo: {', '.join(found_speculative[:3])}"
        
        return GuardrailCheckResult(
            passed=passed,
            rule_name="no_speculative_language",
            details=details,
            severity="warning" if not passed else "info"
        )
    
    def _check_length(self, response: str) -> GuardrailCheckResult:
        """Verifica que la longitud sea apropiada"""
        word_count = len(response.split())
        
        # Longitud apropiada: entre 20 y 500 palabras
        is_too_short = word_count < 20
        is_too_long = word_count > 500
        
        passed = not (is_too_short or is_too_long)
        
        if is_too_short:
            details = f"Respuesta muy corta ({word_count} palabras, mínimo 20)"
            severity = "warning"
        elif is_too_long:
            details = f"Respuesta muy larga ({word_count} palabras, máximo 500)"
            severity = "warning"
        else:
            details = f"Longitud apropiada ({word_count} palabras)"
            severity = "info"
        
        return GuardrailCheckResult(
            passed=passed,
            rule_name="appropriate_length",
            details=details,
            severity=severity
        )
    
    def _check_format(self, response: str) -> GuardrailCheckResult:
        """Verifica que el formato sea apropiado"""
        # Verificar que tenga estructura básica
        has_structure = any([
            '\n' in response,  # Tiene saltos de línea
            '•' in response or '-' in response or '*' in response,  # Tiene listas
            '[' in response and ']' in response,  # Tiene citas
        ])
        
        passed = has_structure
        
        details = "Formato estructurado adecuado" if passed else \
                 "Formato plano, considerar agregar estructura"
        
        return GuardrailCheckResult(
            passed=passed,
            rule_name="appropriate_format",
            details=details,
            severity="info"  # Informativo, no crítico
        )
    
    def _check_no_urls(self, response: str) -> GuardrailCheckResult:
        """Verifica que NO haya URLs o enlaces en la respuesta (seguridad)"""
        # Patrones para detectar URLs
        url_patterns = [
            r'https?://[^\s]+',  # http:// o https://
            r'www\.[^\s]+',  # www.
            r'[a-zA-Z0-9-]+\.(com|org|net|io|co|gov|edu)[^\s]*',  # dominios comunes
            r'tinyurl\.com/[^\s]+',  # TinyURL específicamente
            r'bit\.ly/[^\s]+',  # Bit.ly
            r'drive\.google\.com[^\s]*',  # Google Drive
            r'docs\.google\.com[^\s]*',  # Google Docs
            r'storage\.googleapis\.com[^\s]*',  # GCS
        ]
        
        found_urls = []
        for pattern in url_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            found_urls.extend(matches)
        
        # También detectar menciones de archivos
        file_mentions = re.findall(
            r'\b[\w-]+\.(pdf|docx?|xlsx?|txt|csv|md)\b',
            response,
            re.IGNORECASE
        )
        
        passed = len(found_urls) == 0 and len(file_mentions) == 0
        
        if not passed:
            details_parts = []
            if found_urls:
                details_parts.append(f"{len(found_urls)} URL(s) detectada(s)")
            if file_mentions:
                details_parts.append(f"{len(file_mentions)} archivo(s) mencionado(s)")
            details = "⚠️ SEGURIDAD: " + ", ".join(details_parts)
        else:
            details = "✅ Sin URLs ni referencias a archivos"
        
        return GuardrailCheckResult(
            passed=passed,
            rule_name="no_urls_or_files",
            details=details,
            severity="critical" if not passed else "info"
        )
    
    def _generate_recommendation(
        self,
        all_passed: bool,
        critical_failures: int,
        warnings: int,
        score: float
    ) -> str:
        """Genera recomendación basada en resultados"""
        if all_passed and score >= 0.9:
            return "✅ Respuesta cumple todos los guardrails. Lista para enviar."
        elif all_passed:
            return f"✓ Respuesta aceptable (score: {score:.0%}). Considera mejoras menores."
        elif critical_failures > 0:
            return f"❌ {critical_failures} fallas críticas. Respuesta requiere corrección."
        elif warnings > 2:
            return f"⚠️ {warnings} warnings. Respuesta aceptable pero mejorable."
        else:
            return f"⚠️ Score bajo ({score:.0%}). Considera regenerar respuesta."


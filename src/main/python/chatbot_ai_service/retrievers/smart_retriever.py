"""
Smart Retriever - Sistema de búsqueda RAG optimizado y limpio

Este retriever reemplaza todos los sistemas de búsqueda anteriores con un enfoque
simple, rápido y efectivo para encontrar documentos relevantes.
"""

import logging
import re
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Resultado de búsqueda con metadata"""
    doc_id: str
    filename: str
    content: str
    score: float
    match_type: str  # 'exact_phrase', 'filename_match', 'keyword_match', 'partial_match'


class SmartRetriever:
    """
    Retriever inteligente que combina múltiples estrategias de búsqueda
    
    Características:
    - Búsqueda de frases exactas (mayor prioridad)
    - Búsqueda por filename (alta prioridad)
    - Búsqueda por keywords (prioridad media)
    - Búsqueda parcial (prioridad baja)
    - Scoring inteligente y ranking
    """
    
    def __init__(self):
        self.stopwords = {
            'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
            'de', 'del', 'a', 'al', 'en', 'por', 'para', 'con', 'sin',
            'sobre', 'bajo', 'entre', 'y', 'o', 'pero', 'si', 'no',
            'es', 'son', 'está', 'están', 'ser', 'estar', 'qué', 'cómo',
            'cuál', 'cuáles', 'quién', 'dónde', 'cuándo', 'me', 'te', 'se',
            'que', 'se', 'lo', 'las', 'los', 'una', 'un', 'de', 'del'
        }
        
        logger.info("SmartRetriever inicializado")
    
    def search_documents(
        self, 
        documents: List[Dict[str, Any]], 
        query: str, 
        max_results: int = 5
    ) -> List[SearchResult]:
        """
        Busca documentos relevantes usando múltiples estrategias
        
        Args:
            documents: Lista de documentos disponibles
            query: Consulta del usuario
            max_results: Número máximo de resultados
            
        Returns:
            Lista de resultados ordenados por relevancia
        """
        if not documents or not query.strip():
            return []
        
        query_clean = query.lower().strip()
        results = []
        
        logger.info(f"🔍 Buscando en {len(documents)} documentos: '{query_clean}'")
        
        for doc in documents:
            score, match_type = self._calculate_document_score(doc, query_clean)
            
            if score > 0:
                results.append(SearchResult(
                    doc_id=doc.get('id', doc.get('filename', 'unknown')),
                    filename=doc.get('filename', 'Sin título'),
                    content=doc.get('content', ''),
                    score=score,
                    match_type=match_type
                ))
        
        # Ordenar por score descendente
        results.sort(key=lambda x: x.score, reverse=True)
        
        # Log resultados top
        logger.info(f"✅ Encontrados {len(results)} documentos relevantes")
        for i, result in enumerate(results[:3]):
            logger.info(f"   {i+1}. {result.filename} (score: {result.score:.1f}, tipo: {result.match_type})")
        
        return results[:max_results]
    
    def _calculate_document_score(self, doc: Dict[str, Any], query: str) -> Tuple[float, str]:
        """
        Calcula el score de relevancia de un documento
        
        Returns:
            Tupla (score, match_type)
        """
        content = doc.get('content', '').lower()
        filename = doc.get('filename', '').lower()
        
        # 1. Búsqueda de frase exacta (score 100-200)
        if query in content:
            return 200.0, 'exact_phrase'
        if query in filename:
            return 150.0, 'filename_match'
        
        # 2. Búsqueda de frases parciales (score 50-100)
        query_words = [w for w in query.split() if len(w) > 2 and w not in self.stopwords]
        
        if len(query_words) >= 2:
            # Buscar frases de 2-3 palabras consecutivas
            for i in range(len(query_words) - 1):
                phrase = f"{query_words[i]} {query_words[i+1]}"
                if phrase in content:
                    return 80.0, 'partial_phrase'
                if phrase in filename:
                    return 100.0, 'filename_partial'
        
        # 3. Búsqueda por keywords individuales (score 10-50)
        keyword_score = 0
        matched_keywords = 0
        
        for word in query_words:
            if word in content:
                keyword_score += 10
                matched_keywords += 1
            if word in filename:
                keyword_score += 20
                matched_keywords += 1
        
        if matched_keywords > 0:
            # Bonus por múltiples keywords
            keyword_score *= (1 + matched_keywords * 0.2)
            return keyword_score, 'keyword_match'
        
        # 4. Búsqueda fuzzy/partial (score 1-10)
        for word in query_words:
            if len(word) > 4:  # Solo para palabras largas
                # Buscar substrings
                for i in range(len(content) - len(word) + 1):
                    if content[i:i+len(word)] == word:
                        return 5.0, 'fuzzy_match'
                    # Buscar con 1-2 caracteres de diferencia
                    if self._fuzzy_match(word, content[i:i+len(word)]):
                        return 3.0, 'fuzzy_match'
        
        return 0.0, 'no_match'
    
    def _fuzzy_match(self, word1: str, word2: str, max_diff: int = 2) -> bool:
        """
        Verifica si dos palabras coinciden con diferencias menores
        """
        if len(word1) != len(word2):
            return False
        
        differences = sum(1 for a, b in zip(word1, word2) if a != b)
        return differences <= max_diff
    
    def get_context_from_results(self, results: List[SearchResult], max_context_length: int = 2000) -> str:
        """
        Construye contexto a partir de los resultados de búsqueda
        
        Args:
            results: Resultados de búsqueda ordenados
            max_context_length: Longitud máxima del contexto
            
        Returns:
            Contexto formateado como string
        """
        if not results:
            return ""
        
        context_parts = []
        current_length = 0
        
        for result in results:
            # Tomar fragmento del contenido
            content_preview = result.content[:800] + "..." if len(result.content) > 800 else result.content
            
            context_part = f"**{result.filename}** (relevancia: {result.score:.1f}):\n{content_preview}\n"
            
            if current_length + len(context_part) > max_context_length:
                break
            
            context_parts.append(context_part)
            current_length += len(context_part)
        
        return "\n".join(context_parts)


# Instancia global
smart_retriever = SmartRetriever()

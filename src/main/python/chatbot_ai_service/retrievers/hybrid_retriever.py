"""
Hybrid Retriever - Búsqueda híbrida de documentos

Combina búsqueda semántica (embeddings) con búsqueda por keywords
para obtener los documentos más relevantes.

Estrategia:
1. Búsqueda semántica (por significado)
2. Búsqueda por keywords (palabras exactas)
3. Merge y deduplicación
4. Ranking por relevancia
"""

import logging
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RetrievedDocument:
    """Documento recuperado con metadata de scoring"""
    doc_id: str
    content: str
    title: str
    metadata: Dict[str, Any]
    semantic_score: float = 0.0
    keyword_score: float = 0.0
    combined_score: float = 0.0
    source: str = ""  # 'semantic', 'keyword', or 'both'


class HybridRetriever:
    """
    Retriever híbrido que combina búsqueda semántica y por keywords
    
    Características:
    - Búsqueda semántica via DocumentContextService
    - Búsqueda por keywords con regex
    - Scoring combinado
    - Deduplicación inteligente
    - Ranking por relevancia
    """
    
    def __init__(self, document_service=None):
        """
        Inicializa el HybridRetriever
        
        Args:
            document_service: Servicio de documentos (DocumentContextService)
        """
        self.document_service = document_service
        self.semantic_weight = 0.6  # 60% peso semántico
        self.keyword_weight = 0.4   # 40% peso keywords
        
        logger.info("HybridRetriever inicializado")
    
    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extrae keywords importantes del query
        
        Args:
            query: Query del usuario
            
        Returns:
            Lista de keywords extraídas
        """
        # Eliminar stopwords comunes en español
        stopwords = {
            'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
            'de', 'del', 'a', 'al', 'en', 'por', 'para', 'con', 'sin',
            'sobre', 'bajo', 'entre', 'y', 'o', 'pero', 'si', 'no',
            'es', 'son', 'está', 'están', 'ser', 'estar', 'qué', 'cómo',
            'cuál', 'cuáles', 'quién', 'dónde', 'cuándo', 'me', 'te', 'se'
        }
        
        # Tokenizar y limpiar
        words = re.findall(r'\b\w+\b', query.lower())
        
        # Filtrar stopwords y palabras muy cortas
        keywords = [
            word for word in words 
            if word not in stopwords and len(word) > 2
        ]
        
        logger.debug(f"Keywords extraídas de '{query}': {keywords}")
        return keywords
    
    def _calculate_keyword_score(self, content: str, keywords: List[str]) -> float:
        """
        Calcula score basado en presencia de keywords
        
        Args:
            content: Contenido del documento
            keywords: Lista de keywords a buscar
            
        Returns:
            Score entre 0 y 1
        """
        if not keywords:
            return 0.0
        
        content_lower = content.lower()
        matches = 0
        
        for keyword in keywords:
            # Contar ocurrencias de cada keyword
            count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', content_lower))
            if count > 0:
                matches += 1
        
        # Score = proporción de keywords encontradas
        score = matches / len(keywords)
        
        return score
    
    async def retrieve_semantic(
        self, 
        query: str, 
        tenant_id: str, 
        max_results: int = 5
    ) -> List[RetrievedDocument]:
        """
        Búsqueda semántica usando embeddings
        
        Args:
            query: Query del usuario
            tenant_id: ID del tenant
            max_results: Máximo número de resultados
            
        Returns:
            Lista de documentos recuperados
        """
        if not self.document_service:
            logger.warning("DocumentService no disponible para búsqueda semántica")
            return []
        
        try:
            # Usar el DocumentContextService existente
            context = await self.document_service.get_relevant_context(
                tenant_id, 
                query, 
                max_results=max_results
            )
            
            if not context:
                logger.info(f"No se encontraron documentos semánticos para tenant {tenant_id}")
                return []
            
            # Convertir a RetrievedDocument
            # (Por ahora usamos el contexto como un solo documento)
            doc = RetrievedDocument(
                doc_id=f"semantic_{tenant_id}",
                content=context,
                title="Documentos relevantes",
                metadata={"tenant_id": tenant_id},
                semantic_score=0.8,  # Score fijo por ahora
                keyword_score=0.0,
                combined_score=0.8,
                source="semantic"
            )
            
            logger.info(f"✅ Búsqueda semántica: 1 documento encontrado")
            return [doc]
            
        except Exception as e:
            logger.error(f"Error en búsqueda semántica: {str(e)}")
            return []
    
    def retrieve_keyword(
        self, 
        query: str, 
        documents: List[Dict[str, Any]], 
        max_results: int = 5
    ) -> List[RetrievedDocument]:
        """
        Búsqueda por keywords
        
        Args:
            query: Query del usuario
            documents: Lista de documentos disponibles
            max_results: Máximo número de resultados
            
        Returns:
            Lista de documentos recuperados por keywords
        """
        keywords = self._extract_keywords(query)
        
        if not keywords:
            logger.debug("No se extrajeron keywords del query")
            return []
        
        scored_docs = []
        
        for doc in documents:
            content = doc.get('content', '')
            keyword_score = self._calculate_keyword_score(content, keywords)
            
            if keyword_score > 0:
                retrieved_doc = RetrievedDocument(
                    doc_id=doc.get('id', 'unknown'),
                    content=content,
                    title=doc.get('title', 'Sin título'),
                    metadata=doc.get('metadata', {}),
                    semantic_score=0.0,
                    keyword_score=keyword_score,
                    combined_score=keyword_score,
                    source="keyword"
                )
                scored_docs.append(retrieved_doc)
        
        # Ordenar por score y retornar top N
        scored_docs.sort(key=lambda x: x.keyword_score, reverse=True)
        
        logger.info(f"✅ Búsqueda por keywords: {len(scored_docs[:max_results])} documentos encontrados")
        return scored_docs[:max_results]
    
    def _merge_and_deduplicate(
        self, 
        semantic_docs: List[RetrievedDocument],
        keyword_docs: List[RetrievedDocument]
    ) -> List[RetrievedDocument]:
        """
        Combina resultados semánticos y por keywords, eliminando duplicados
        
        Args:
            semantic_docs: Documentos de búsqueda semántica
            keyword_docs: Documentos de búsqueda por keywords
            
        Returns:
            Lista combinada y deduplicada
        """
        # Usar dict para deduplicar por doc_id
        merged = {}
        
        # Agregar documentos semánticos
        for doc in semantic_docs:
            merged[doc.doc_id] = doc
        
        # Agregar o combinar documentos por keywords
        for doc in keyword_docs:
            if doc.doc_id in merged:
                # Ya existe - combinar scores
                existing = merged[doc.doc_id]
                existing.keyword_score = doc.keyword_score
                existing.source = "both"
                # Recalcular combined score
                existing.combined_score = (
                    existing.semantic_score * self.semantic_weight +
                    existing.keyword_score * self.keyword_weight
                )
            else:
                # Nuevo documento
                merged[doc.doc_id] = doc
        
        return list(merged.values())
    
    async def retrieve(
        self, 
        query: str, 
        tenant_id: str,
        documents: Optional[List[Dict[str, Any]]] = None,
        max_results: int = 5
    ) -> List[RetrievedDocument]:
        """
        Búsqueda híbrida completa
        
        Combina búsqueda semántica y por keywords para obtener
        los documentos más relevantes.
        
        Args:
            query: Query del usuario
            tenant_id: ID del tenant
            documents: Lista opcional de documentos para búsqueda por keywords
            max_results: Máximo número de resultados
            
        Returns:
            Lista de documentos recuperados y rankeados
        """
        logger.info(f"🔍 Iniciando búsqueda híbrida para: '{query}'")
        
        # 1. Búsqueda semántica
        semantic_docs = await self.retrieve_semantic(query, tenant_id, max_results)
        
        # 2. Búsqueda por keywords (si hay documentos disponibles)
        keyword_docs = []
        if documents:
            keyword_docs = self.retrieve_keyword(query, documents, max_results)
        
        # 3. Merge y deduplicate
        merged_docs = self._merge_and_deduplicate(semantic_docs, keyword_docs)
        
        # 4. Ordenar por combined score
        merged_docs.sort(key=lambda x: x.combined_score, reverse=True)
        
        # 5. Retornar top N
        final_docs = merged_docs[:max_results]
        
        logger.info(f"✅ Búsqueda híbrida completada: {len(final_docs)} documentos")
        for i, doc in enumerate(final_docs, 1):
            logger.debug(
                f"  {i}. {doc.title[:50]}... "
                f"(score: {doc.combined_score:.2f}, source: {doc.source})"
            )
        
        return final_docs
    
    def set_weights(self, semantic_weight: float, keyword_weight: float):
        """
        Ajusta los pesos de búsqueda semántica vs keywords
        
        Args:
            semantic_weight: Peso de búsqueda semántica (0-1)
            keyword_weight: Peso de búsqueda por keywords (0-1)
        """
        total = semantic_weight + keyword_weight
        self.semantic_weight = semantic_weight / total
        self.keyword_weight = keyword_weight / total
        
        logger.info(
            f"Pesos ajustados - Semántico: {self.semantic_weight:.2f}, "
            f"Keywords: {self.keyword_weight:.2f}"
        )


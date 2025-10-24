"""
Servicio de IA optimizado con timeout y logging mejorado
"""
import logging
import time
from typing import Dict, Any, Optional
from chatbot_ai_service.config.optimization_config import optimization_config

logger = logging.getLogger(__name__)

class OptimizedAIService:
    """Servicio de IA optimizado con timeout y logging mejorado"""
    
    def __init__(self, base_ai_service):
        self.base_ai_service = base_ai_service
        self.logger = logging.getLogger(__name__)
    
    async def process_chat_message_optimized(self, tenant_id: str, query: str, 
                                           user_context: Dict[str, Any], 
                                           session_id: str = None, 
                                           tenant_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Procesa mensaje de chat con optimizaciones simplificadas
        
        Args:
            tenant_id: ID del tenant
            query: Mensaje del usuario
            user_context: Contexto del usuario
            session_id: ID de la sesión
            tenant_config: Configuración del tenant
            
        Returns:
            Respuesta optimizada
        """
        print(f"🚀 [OPTIMIZED] MÉTODO INICIADO - tenant: {tenant_id}, query: '{query[:50]}...'")
        self.logger.info(f"🚀 [OPTIMIZED] MÉTODO INICIADO - tenant: {tenant_id}, query: '{query[:50]}...'")
        
        start_time = time.time()
        
        try:
            # 1. VERIFICAR CONFIGURACIÓN DEL TENANT
            if not tenant_config:
                self.logger.warning(f"⚠️ No se recibió tenant_config en el request, obteniendo desde servicio Java...")
                tenant_config = self._get_tenant_config(tenant_id)
                if not tenant_config:
                    return self._create_error_response("Tenant no encontrado", start_time)
            
            # 2. CLASIFICAR INTENCIÓN
            self.logger.info(f"🎯 [OPTIMIZED] Clasificando intención...")
            intent_result = await self._classify_intent_optimized(tenant_id, query, user_context)
            intent = intent_result.get("category", "saludo_apoyo")
            confidence = intent_result.get("confidence", 0.0)
            
            # 📊 IMPRIMIR CLASIFICACIÓN DETALLADA
            self.logger.info(f"📊 [CLASIFICACIÓN] Mensaje: '{query[:100]}...'")
            self.logger.info(f"📊 [CLASIFICACIÓN] Categoría: '{intent}'")
            self.logger.info(f"📊 [CLASIFICACIÓN] Confianza: {confidence:.2f}")
            self.logger.info(f"📊 [CLASIFICACIÓN] Tenant: {tenant_id}")
            self.logger.info(f"📊 [CLASIFICACIÓN] Session: {session_id}")
            self.logger.info(f"📊 [CLASIFICACIÓN] {'='*50}")
            
            # 3. PROCESAR CON SERVICIO BASE (con timeout)
            self.logger.info(f"📚 [OPTIMIZED] Procesando con servicio base...")
            import asyncio
            
            try:
                result = await asyncio.wait_for(
                    self.base_ai_service.process_chat_message(
                        tenant_id, query, user_context, session_id, tenant_config
                    ),
                    timeout=optimization_config.AI_RESPONSE_TIMEOUT
                )
                
                # Agregar información de optimización al resultado
                result["intent"] = intent
                result["confidence"] = confidence
                result["optimized"] = True
                
                processing_time = time.time() - start_time
                result["processing_time"] = processing_time
                
                self.logger.info(f"✅ [OPTIMIZED] Procesamiento completado en {processing_time:.2f}s")
                self.logger.info(f"✅ [OPTIMIZED] INTENT FINAL: {intent} (confianza: {confidence})")
                
                return result
                
            except asyncio.TimeoutError:
                self.logger.error(f"⏰ Timeout generando respuesta para tenant {tenant_id}")
                return self._create_error_response("Timeout en procesamiento", start_time)
            
        except Exception as e:
            self.logger.error(f"❌ [OPTIMIZED] Error en procesamiento optimizado: {str(e)}")
            self.logger.error(f"❌ [OPTIMIZED] Traceback: {e}", exc_info=True)
            
            # Fallback al servicio base
            self.logger.info(f"🔄 [OPTIMIZED] Fallback al servicio base...")
            try:
                result = await self.base_ai_service.process_chat_message(
                    tenant_id, query, user_context, session_id, tenant_config
                )
                result["optimized"] = False  # Marcar como no optimizado
                return result
            except Exception as fallback_error:
                self.logger.error(f"❌ [OPTIMIZED] Error en fallback: {str(fallback_error)}")
                return self._create_error_response("Error en procesamiento", start_time)
    
    def _get_tenant_config(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene configuración del tenant"""
        try:
            from chatbot_ai_service.services.configuration_service import configuration_service
            config = configuration_service.get_tenant_config(tenant_id)
            if config:
                self.logger.info(f"✅ Configuración obtenida para tenant {tenant_id}")
            else:
                self.logger.warning(f"⚠️ No se encontró configuración para tenant {tenant_id}")
            return config
        except Exception as e:
            self.logger.error(f"Error obteniendo configuración del tenant {tenant_id}: {str(e)}")
            return None
    
    
    async def _classify_intent_optimized(self, tenant_id: str, query: str, 
                                       user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Clasifica intención de forma optimizada"""
        try:
            self.logger.info(f"🎯 [CLASIFICACIÓN] Iniciando clasificación para: '{query[:50]}...'")
            self.logger.info(f"🎯 [CLASIFICACIÓN] Tenant ID: {tenant_id}")
            
            # Usar el método de clasificación del servicio base
            result = await self.base_ai_service.classify_intent(tenant_id, query, user_context)
            
            if result and result.get("category"):
                self.logger.info(f"✅ [CLASIFICACIÓN] Clasificación exitosa: {result['category']} (confianza: {result.get('confidence', 0):.2f})")
                return result
            else:
                self.logger.warning("⚠️ [CLASIFICACIÓN] Clasificación falló, usando fallback")
                return {"category": "saludo_apoyo", "confidence": 0.5}
                
        except Exception as e:
            self.logger.error(f"❌ [CLASIFICACIÓN] Error en clasificación: {str(e)}")
            return {"category": "saludo_apoyo", "confidence": 0.5}
    
    def _create_error_response(self, error_message: str, start_time: float) -> Dict[str, Any]:
        """Crea respuesta de error"""
        return {
            "response": f"Lo siento, {error_message.lower()}.",
            "followup_message": "",
            "processing_time": time.time() - start_time,
            "error": error_message,
            "optimized": True
        }

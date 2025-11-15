"""
Chatbot AI Service - Simplificado
================================

Servicio de IA que se enfoca únicamente en procesamiento de IA.
Recibe configuración del proyecto Political Referrals via HTTP.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import httpx
from dotenv import load_dotenv
import logging

from chatbot_ai_service.controllers.chat_controller import router as chat_router
from chatbot_ai_service.controllers.city_normalization_controller import router as city_router
from chatbot_ai_service.controllers.preprocessing_controller import router as preprocessing_router

# Cargar variables de entorno
# Buscar .env en el directorio raíz del proyecto (3 niveles arriba)
import pathlib
project_root = pathlib.Path(__file__).parent.parent.parent.parent.parent
env_path = project_root / ".env"
print(f"📁 Archivo .env existe: {env_path.exists()}")
load_dotenv(env_path)

# Verificar que POLITICAL_REFERRALS_SERVICE_URL se cargó
political_url = os.getenv("POLITICAL_REFERRALS_SERVICE_URL")
if political_url:
    print(f"✅ POLITICAL_REFERRALS_SERVICE_URL cargada: {political_url}")
else:
    print("❌ POLITICAL_REFERRALS_SERVICE_URL no encontrada")

# Configurar logging global para que se vean logs de controllers/servicios
log_level_str = os.getenv("LOG_LEVEL", "DEBUG").upper()
log_level = getattr(logging, log_level_str, logging.DEBUG)
logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logging.getLogger(__name__).info(f"Logging configurado en nivel: {log_level_str}")

# Verificar que la API key se cargó correctamente
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    print(f"✅ GEMINI_API_KEY cargada correctamente")
else:
    print("❌ GEMINI_API_KEY no encontrada")

# 🚀 DEBUG: Verificar variables de optimización
local_dev = os.getenv("LOCAL_DEVELOPMENT", "false").lower() == "true"
ultra_fast = os.getenv("ULTRA_FAST_MODE", "false").lower() == "true"
print(f"🚀 DEBUG - LOCAL_DEVELOPMENT: {local_dev}")
print(f"🚀 DEBUG - ULTRA_FAST_MODE: {ultra_fast}")

# 🚀 OPTIMIZACIÓN: Pre-cargar modelos de IA después de cargar variables de entorno
try:
    print("🚀 Iniciando pre-carga de modelos de IA...")
    from chatbot_ai_service.services.ai_service import ai_service
    ai_service.preload_models_on_startup()
    print("✅ Pre-carga de modelos completada")
except Exception as e:
    print(f"❌ Error durante pre-carga: {e}")
    # No fallar el startup si hay error en la pre-carga

# 🚀 PRECARGA AUTOMÁTICA DE DOCUMENTOS
async def preload_documents_on_startup_optimized():
    """Precargar documentos automáticamente al inicio del servicio usando el servicio optimizado"""
    try:
        print("🚀 Iniciando precarga optimizada de documentos...")
        
        # Importar servicios optimizados
        from chatbot_ai_service.services.document_preprocessor_service import document_preprocessor_service
        from chatbot_ai_service.services.tenant_memory_service import tenant_memory_service
        
        # 🗄️ NUEVO: Solo inicializar memoria si no está ya cargada desde Firestore
        if len(tenant_memory_service._tenant_memories) > 0:
            print(f"✅ {len(tenant_memory_service._tenant_memories)} memorias ya cargadas desde Firestore - saltando inicialización")
            return
        
        # Obtener configuración de tenants desde Firestore
        response_data = await get_tenant_configs_from_firestore()
        
        if not response_data or not isinstance(response_data, dict):
            print("⚠️ No se pudieron obtener configuraciones de tenants desde Firestore")
            return
        
        # Extraer la lista de tenants de la respuesta
        tenant_configs = response_data.get("tenants", {})
        
        if not tenant_configs:
            print("⚠️ No se encontraron configuraciones de tenants en la respuesta")
            return
        
        print(f"📊 Encontrados {len(tenant_configs)} tenants para precargar")
        
        # Inicializar memoria para cada tenant (rápido)
        for tenant_id, tenant_config in tenant_configs.items():
            print(f"🧠 Inicializando memoria para tenant {tenant_id}...")
            memory_success = tenant_memory_service.initialize_tenant_memory(
                tenant_id=tenant_id,
                tenant_config=tenant_config,
                document_summary=""  # Se llenará después si hay documentos
            )
            
            if memory_success:
                print(f"✅ Memoria inicializada para tenant {tenant_id}")
            else:
                print(f"⚠️ No se pudo inicializar memoria para tenant {tenant_id}")
        
        # Hacer preprocesamiento SÍNCRONO usando asyncio.run() en un hilo separado
        print("🚀 Iniciando preprocesamiento SÍNCRONO...")
        import asyncio
        import threading
        
        def run_sync_preprocessing():
            async def synchronous_preprocessing():
                try:
                    print("📚 [SYNC] Iniciando preprocesamiento de documentos...")
                    results = await document_preprocessor_service.preprocess_all_tenants()
                    
                    successful_tenants = sum(1 for success in results.values() if success)
                    print(f"✅ [SYNC] Preprocesamiento completado: {successful_tenants}/{len(results)} tenants exitosos")
                    
                    # Mostrar estadísticas de memoria
                    memory_stats = tenant_memory_service.get_memory_stats()
                    print(f"🧠 [SYNC] Estadísticas de memoria:")
                    print(f"  - Memorias de tenants: {memory_stats['tenant_memories']}")
                    print(f"  - Conciencias de usuarios: {memory_stats['user_consciousness']}")
                    
                    print("🎉 [SYNC] ¡Preprocesamiento completado! El servicio está completamente optimizado.")
                    return True
                    
                except Exception as e:
                    print(f"❌ [SYNC] Error en preprocesamiento: {e}")
                    return False
            
            # Ejecutar en un nuevo event loop
            return asyncio.run(synchronous_preprocessing())
        
        # Ejecutar preprocesamiento en un hilo separado para evitar conflictos con el event loop principal
        preprocessing_thread = threading.Thread(target=run_sync_preprocessing)
        preprocessing_thread.start()
        preprocessing_thread.join()  # Esperar a que termine
        
        print("✅ Servicio completamente listo - todos los documentos preprocesados")
    except Exception as e:
        print(f"❌ Error durante precarga optimizada de documentos: {e}")
        # No fallar el startup si hay error en la precarga

async def get_tenant_configs_from_firestore():
    """Obtener configuración de todos los tenants directamente desde Firestore"""
    try:
        from chatbot_ai_service.services.firestore_tenant_service import firestore_tenant_service
        
        print("🔍 Obteniendo configuraciones de tenants desde Firestore...")
        tenant_configs = await firestore_tenant_service.get_all_tenant_configs()
        
        if tenant_configs:
            print(f"✅ Configuraciones obtenidas desde Firestore: {len(tenant_configs)} tenants")
            return {
                "status": "success",
                "tenants": tenant_configs,
                "total_tenants": len(tenant_configs)
            }
        else:
            print("⚠️ No se encontraron configuraciones de tenants en Firestore")
            return {
                "status": "success",
                "tenants": {},
                "total_tenants": 0
            }
            
    except Exception as e:
        print(f"❌ Error obteniendo configuración de tenants desde Firestore: {e}")
        return {
            "status": "error",
            "tenants": {},
            "total_tenants": 0,
            "error": str(e)
        }

# Configuración de la aplicación
app = FastAPI(
    title="Chatbot AI Service",
    description="Servicio de IA para chatbots políticos - Solo procesamiento de IA",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(chat_router)
app.include_router(city_router)
app.include_router(preprocessing_router)

# Importar y agregar el nuevo controlador de clasificación de intenciones
from chatbot_ai_service.controllers.intent_classification_controller import router as intent_classification_router
app.include_router(intent_classification_router)

# 🧠 FUNCIÓN: Generar variaciones con IA si es necesario
async def _generate_ai_welcome_variations_if_needed(tenant_id: str, tenant_memory):
    """Genera variaciones de saludo con IA si no existen o son pocas"""
    try:
        from chatbot_ai_service.services.optimized_ai_service import OptimizedAIService
        from chatbot_ai_service.services.document_index_persistence_service import document_index_persistence_service
        from chatbot_ai_service.services.ai_service import ai_service
        
        # Verificar cuántas variaciones hay (cache por tenant)
        cache_key = f'{tenant_id}_welcome_variations'
        existing_variations = OptimizedAIService._prompts_cache.get(cache_key, [])
        num_existing = len(existing_variations) if existing_variations else 0
        
        # Si ya hay suficientes variaciones (3+), no generar
        if num_existing >= 3:
            return
        
        print(f"      • 🧠 Generando {3 - num_existing} variaciones nuevas con IA...")
        
        # Obtener contexto del tenant para generar variaciones relevantes
        campaign_context = tenant_memory.campaign_context if tenant_memory and hasattr(tenant_memory, 'campaign_context') else ""
        common_questions = tenant_memory.common_questions[:3] if tenant_memory and hasattr(tenant_memory, 'common_questions') and tenant_memory.common_questions else []
        
        # Obtener configuración del tenant
        from chatbot_ai_service.services.firestore_tenant_service import firestore_tenant_service
        tenant_config = await firestore_tenant_service.get_tenant_config(tenant_id)
        contact_name = "el candidato"
        if tenant_config and tenant_config.get('branding'):
            contact_name = tenant_config['branding'].get('contactName', 'el candidato')
        
        # Crear prompt ULTRA CORTO para generación rápida
        generation_prompt = f"""Genera 3 saludos para campaña política, máximo 100 caracteres cada uno. Separar con "---".

1:
2:
3:"""
        
        # Generar con IA con TIMEOUT CORTO (3 segundos máximo)
        try:
            import asyncio
            generated_text = await asyncio.wait_for(
                ai_service._generate_content_optimized(generation_prompt),
                timeout=3.0
            )
        except asyncio.TimeoutError:
            print(f"      • ⚠️ Timeout generando con IA (3s) - usando variaciones básicas")
            generated_text = None
        
        if generated_text:
            # Parsear las variaciones (splitting por líneas o separadores)
            variations = generated_text.split("---")
            variations = [v.strip() for v in variations if v.strip() and len(v.strip()) > 10]
            
            # Si no funcionó, intentar por números
            if len(variations) < 3:
                parts = generated_text.split("\n")
                variations = [p.strip() for p in parts if p.strip() and len(p.strip()) > 10 and not p.strip().isdigit()]
            
            # Filtrar por longitud razonable
            variations = [v for v in variations if 15 <= len(v) <= 200]
            
            # Agregar a las existentes
            if num_existing > 0:
                all_variations = existing_variations + variations
            else:
                all_variations = variations
            
            # Limitar a 5 variaciones
            all_variations = all_variations[:5]
            
            # Guardar en cache por tenant
            OptimizedAIService._prompts_cache[cache_key] = all_variations
            print(f"      • ✅ Generadas {len(variations)} variaciones nuevas ({len(all_variations)} total)")
            
            # Opcional: Guardar en DB para persistencia
            if tenant_memory:
                prompts = document_index_persistence_service.get_tenant_prompts(tenant_id)
                if not prompts:
                    prompts = {}
                prompts['welcome_variations'] = all_variations
                await document_index_persistence_service.save_tenant_prompts(tenant_id, prompts)
                print(f"      • 💾 Variaciones guardadas en DB para persistencia")
        else:
            print(f"      • ⚠️ No se pudieron generar variaciones con IA")
            
    except Exception as e:
        print(f"      • ❌ Error generando variaciones: {e}")

# 🚀 EVENTO DE STARTUP: Carga lazy desde DB
@app.on_event("startup")
async def startup_event():
    """Evento de startup - carga lazy desde DB"""
    # 🗄️ NUEVO: Cargar metadatos de índices desde DB
    from chatbot_ai_service.services.document_index_persistence_service import document_index_persistence_service
    
    print("🗄️ Cargando metadatos de índices desde Firestore...")
    
    try:
        # Verificar si Firestore está disponible
        db = document_index_persistence_service.db
        if db is None:
            print("⚠️ Firestore no disponible en este momento - saltando carga de metadatos")
            print("ℹ️ Los índices se cargarán de forma lazy cuando sea necesario")
            all_indexes = []
        else:
            # Obtener todos los índices guardados
            all_indexes = []
            indexes_ref = db.collection("document_indexes").get()
            for doc in indexes_ref:
                index_data = doc.to_dict()
                if index_data:
                    all_indexes.append(index_data)
        
        if all_indexes:
            print(f"✅ {len(all_indexes)} índices encontrados en DB:")
            for idx in all_indexes:
                print(f"  - Tenant {idx.get('tenant_id')}: {idx.get('documents_count', 0)} documentos")
                
                # 🚀 Carga SINCRÓNICA al inicio con persistencia en disco
                tenant_id = idx.get('tenant_id')
                bucket_url = idx.get('bucket_url')
                if bucket_url:
                    print(f"      • ✅ URL configurada: {bucket_url[:50]}...")
                    
                    # Importar servicio de documentos
                    from chatbot_ai_service.services.document_context_service import document_context_service
                    
                    try:
                        print(f"      • 📚 Cargando índice (desde disco si existe, sino desde bucket)...")
                        # Este método ahora carga desde disco si existe (rápido ~1s)
                        # Si no existe, carga desde bucket y guarda en disco (lento ~10-30s la primera vez)
                        success = await document_context_service.load_tenant_documents(tenant_id, bucket_url)
                        if success:
                            print(f"      • ✅ Índice listo - {idx.get('documents_count', 0)} documentos disponibles")
                        else:
                            print(f"      • ⚠️ No se pudo cargar índice")
                    except Exception as e:
                        print(f"      • ❌ Error cargando: {e}")
        else:
            print("ℹ️ No hay índices guardados en DB aún")
        
        # 🧠 NUEVO: Cargar memorias de tenants desde Firestore
        from chatbot_ai_service.services.tenant_memory_service import tenant_memory_service
        
        print("🧠 Cargando memorias de tenants desde Firestore...")
        if db is None:
            print("⚠️ Firestore no disponible - saltando carga de memorias")
            tenant_ids = []
        else:
            # 🔧 FIX: Obtener tenant IDs desde la colección 'tenants' (configuraciones reales)
            # en lugar de 'tenant_memory_cache' (que puede tener documentos viejos o de prueba)
            try:
                print("🔍 Obteniendo tenant IDs desde colección 'tenants' (configuraciones reales)...")
                tenants_ref = db.collection('tenants')
                tenant_docs = tenants_ref.get()
                
                # Extraer tenant_ids de las configuraciones reales
                tenant_ids = []
                for doc in tenant_docs:
                    data = doc.to_dict()
                    tenant_id = data.get('tenant_id')
                    if tenant_id:
                        tenant_ids.append(str(tenant_id))
                
                print(f"✅ {len(tenant_ids)} tenants encontrados en configuración: {tenant_ids}")
                
                # Opcional: También verificar si hay memorias guardadas para estos tenants
                # pero NO usar documentos que no estén en la lista de tenants válidos
                memory_docs = db.collection('tenant_memory_cache').get()
                memory_tenant_ids = [doc.id for doc in memory_docs]
                
                # Filtrar solo los tenant IDs que están en la configuración real
                valid_memory_ids = [tid for tid in memory_tenant_ids if tid in tenant_ids]
                
                if len(valid_memory_ids) < len(memory_tenant_ids):
                    skipped = set(memory_tenant_ids) - set(tenant_ids)
                    if skipped:
                        print(f"⚠️ Se encontraron {len(skipped)} documentos de memoria no válidos (serán ignorados): {list(skipped)}")
                
                # Usar los tenant_ids de configuración, no los de memoria
                # tenant_ids ya tiene los IDs válidos
                
            except Exception as e:
                print(f"⚠️ Error obteniendo tenant IDs desde configuración: {e}")
                print("⚠️ Usando método anterior (puede incluir documentos inválidos)...")
                tenant_ids = tenant_memory_service.get_all_tenant_memories_from_firestore()
        
        if tenant_ids:
            print(f"✅ {len(tenant_ids)} memorias encontradas en Firestore:")
            
            # 🔧 FIX: Obtener configuraciones de tenants para usar las bases de datos correctas
            tenant_configs_map = {}
            try:
                print("🔍 Obteniendo configuraciones de tenants para usar bases de datos correctas...")
                from chatbot_ai_service.services.firestore_tenant_service import firestore_tenant_service
                import asyncio
                
                # Obtener todas las configuraciones
                all_configs = await firestore_tenant_service.get_all_tenant_configs()
                for tid, config in all_configs.items():
                    tenant_configs_map[str(tid)] = config
                
                print(f"✅ {len(tenant_configs_map)} configuraciones obtenidas para cargar memoria")
            except Exception as e:
                print(f"⚠️ Error obteniendo configuraciones: {e} - se usará base de datos por defecto")
            
            for tenant_id in tenant_ids:
                # Intentar cargar memoria usando la configuración del tenant si está disponible
                tenant_config = tenant_configs_map.get(tenant_id)
                memory_loaded = False
                
                if tenant_config:
                    client_project_id = tenant_config.get('client_project_id')
                    client_database_id = tenant_config.get('client_database_id', '(default)')
                    print(f"🔍 Cargando memoria para tenant {tenant_id} desde proyecto: {client_project_id}, database: {client_database_id}")
                    
                    # Usar el nuevo servicio de memoria que soporta conexiones específicas
                    try:
                        from chatbot_ai_service.memory import get_tenant_memory_service
                        new_memory_service = get_tenant_memory_service()
                        
                        # Cargar usando la configuración correcta (await ya que estamos en contexto async)
                        memory = await new_memory_service.get_tenant_memory(tenant_id, tenant_config)
                        
                        if memory:
                            print(f"✅ Memoria cargada para tenant {tenant_id} desde su base de datos específica")
                            memory_loaded = True
                            # Continuar con el resto del procesamiento...
                        else:
                            print(f"⚠️ No se encontró memoria para tenant {tenant_id} en su base de datos específica")
                            # Intentar con el método anterior como fallback
                            if tenant_memory_service.load_tenant_memory_from_firestore(tenant_id):
                                print(f"✅ Memoria cargada para tenant {tenant_id} desde base de datos por defecto (fallback)")
                                memory_loaded = True
                            else:
                                print(f"⚠️ Tenant {tenant_id}: no se pudo cargar memoria ni desde su base específica ni desde la por defecto")
                                continue
                    except Exception as e:
                        print(f"⚠️ Error cargando memoria con configuración específica para tenant {tenant_id}: {e}")
                        print(f"⚠️ Intentando con método anterior (base por defecto)...")
                        # Fallback al método anterior
                        if tenant_memory_service.load_tenant_memory_from_firestore(tenant_id):
                            memory_loaded = True
                else:
                    print(f"⚠️ No se encontró configuración para tenant {tenant_id}, usando base de datos por defecto")
                    # Usar método anterior sin configuración
                    if tenant_memory_service.load_tenant_memory_from_firestore(tenant_id):
                        memory_loaded = True
                
                # Si la memoria se cargó exitosamente, mostrar datos
                if memory_loaded:
                    # Mostrar datos cargados para cada tenant
                    precomputed = tenant_memory_service.get_tenant_precomputed_responses(tenant_id)
                    questions = tenant_memory_service.get_tenant_common_questions(tenant_id)
                    context = tenant_memory_service.get_tenant_campaign_context(tenant_id)
                    
                    # 🗄️ NUEVO: Cargar prompts desde DB y cachearlos en OptimizedAIService
                    prompts = document_index_persistence_service.get_tenant_prompts(tenant_id)
                    
                    if prompts:
                        # Cachear en el servicio optimizado para acceso rápido
                        from chatbot_ai_service.services.optimized_ai_service import OptimizedAIService
                        if not hasattr(OptimizedAIService, '_prompts_cache'):
                            OptimizedAIService._prompts_cache = {}
                        OptimizedAIService._prompts_cache[tenant_id] = prompts
                        
                        # Cargar variaciones de 'welcome' si existen
                        num_existing = 0
                        if 'welcome_variations' in prompts:
                            variations = prompts['welcome_variations']
                            # Cachear por tenant
                            OptimizedAIService._prompts_cache[f'{tenant_id}_welcome_variations'] = variations
                            num_existing = len(variations)
                            print(f"      • ✅ {num_existing} variaciones de saludo cargadas desde DB")
                        else:
                            print(f"      • ⚠️ No hay variaciones de saludo en DB - se generarán al primer uso")
                        
                        # 🧠 NUEVO: Precargar variaciones generadas por IA (si no existen o son pocas)
                        # ⚡ Hacerlo en background para no bloquear startup
                        if num_existing < 3:
                            print(f"      • ⚡ Generando variaciones en background (no bloquea startup)")
                            import asyncio
                            loaded_memory = tenant_memory_service._tenant_memories.get(tenant_id)
                            if loaded_memory:
                                # Crear tarea en background
                                asyncio.create_task(_generate_ai_welcome_variations_if_needed(tenant_id, loaded_memory))
                            else:
                                print(f"      • ⚠️ No hay memoria cargada")
                        else:
                            print(f"      • ✅ Ya hay {num_existing} variaciones - no necesita generar más")
                    
                    print(f"  - ✅ Tenant {tenant_id}:")
                    print(f"      • {len(precomputed) if precomputed else 0} respuestas precomputadas")
                    print(f"      • {len(questions)} preguntas comunes")
                    print(f"      • Contexto: {len(context) if context else 0} caracteres")
                    print(f"      • {'✅ Prompts cargados y cacheados' if prompts else '⚠️ No prompts'} desde DB")
                else:
                    print(f"  - ⚠️ Tenant {tenant_id}: no se pudo cargar")
        else:
            print("ℹ️ No hay memorias guardadas en Firestore aún")
        
        # 🔧 OPTIMIZACIÓN: Hacer el preprocesamiento opcional para inicio rápido
        enable_preprocessing = os.getenv("ENABLE_DOCUMENT_PREPROCESSING", "false").lower() == "true"
        
        # 🗄️ Si ya hay datos en DB, saltar preprocesamiento automáticamente
        has_indexes = len(all_indexes) > 0
        has_memories = len(tenant_ids) > 0
        
        if has_indexes or has_memories:
            print(f"✅ Sistema ya optimizado - {len(all_indexes)} índices y {len(tenant_ids)} memorias en DB")
            print("⚡ Saltando preprocesamiento automático (inicio rápido)")
            
            if enable_preprocessing:
                print("💡 Para forzar reprocesamiento: reiniciar con ENABLE_DOCUMENT_PREPROCESSING=true")
            
        elif enable_preprocessing:
            print("🚀 Preprocesamiento de documentos HABILITADO - procesando nuevos documentos...")
            await preload_documents_on_startup_optimized()
        else:
            print("⚡ Preprocesamiento DESHABILITADO - usando índices de DB (inicio rápido)")
            print("💡 Para reprocesar: set ENABLE_DOCUMENT_PREPROCESSING=true")
            
    except Exception as e:
        print(f"⚠️ Error cargando metadatos desde DB: {e}")
        print("ℹ️ El servicio funcionará normalmente con carga lazy")

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "service": "chatbot-ai-service",
        "version": "1.0.0",
        "description": "Servicio de IA para chatbots políticos",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check del servicio con verificación de preprocesamiento"""
    try:
        from chatbot_ai_service.services.document_preprocessor_service import document_preprocessor_service
        from chatbot_ai_service.services.document_context_service import document_context_service
        
        # Obtener estado del preprocesamiento
        cache_stats = document_preprocessor_service.get_cache_stats()
        processing_statuses = cache_stats.get("processing_status", {})
        
        # Verificar si hay tenants en procesamiento o fallidos
        processing_tenants = [tenant for tenant, status in processing_statuses.items() 
                            if status in ["processing"]]
        failed_tenants = [tenant for tenant, status in processing_statuses.items() 
                        if status in ["failed", "timeout"]]
        completed_tenants = [tenant for tenant, status in processing_statuses.items() 
                            if status == "completed"]
        
        # 🔧 FIX: Verificar también si hay documentos cargados directamente en document_context_service
        # Esto ocurre cuando los documentos se cargan desde Firestore en el startup
        # sin pasar por el preprocesador
        loaded_tenants_from_context = set()
        try:
            if hasattr(document_context_service, '_index_cache') and document_context_service._index_cache:
                loaded_tenants_from_context.update(document_context_service._index_cache.keys())
            if hasattr(document_context_service, '_document_cache') and document_context_service._document_cache:
                loaded_tenants_from_context.update(document_context_service._document_cache.keys())
        except Exception:
            # Si hay error accediendo a los caches, asumir que no hay documentos cargados
            pass
        
        # Si hay documentos cargados en document_context_service, considerarlos como "ready"
        # incluso si no están en el preprocesador
        has_loaded_documents = len(loaded_tenants_from_context) > 0
        
        # Determinar estado de salud
        # CRÍTICO: Considerar "healthy" si:
        # 1. Hay tenants completados en el preprocesador, O
        # 2. Hay documentos cargados directamente en document_context_service
        if processing_tenants:
            health_status = "preprocessing"  # Cloud Run NO enviará tráfico
        elif failed_tenants and not has_loaded_documents:
            health_status = "degraded"      # Cloud Run NO enviará tráfico
        elif completed_tenants or has_loaded_documents:
            health_status = "healthy"       # Cloud Run SÍ enviará tráfico
        else:
            health_status = "starting"      # Cloud Run NO enviará tráfico
        
        return {
            "status": health_status,
            "service": "chatbot-ai-service",
            "version": "1.0.0",
            "preprocessing": {
                "completed_tenants": len(completed_tenants),
                "processing_tenants": len(processing_tenants),
                "failed_tenants": len(failed_tenants),
                "total_tenants": cache_stats.get("total_tenants", 0),
                "loaded_from_context": len(loaded_tenants_from_context),
                "loaded_tenant_ids": list(loaded_tenants_from_context)
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "service": "chatbot-ai-service",
            "version": "1.0.0",
            "error": str(e)
        }

@app.get("/ready")
async def readiness_check():
    """Readiness check - Con preprocesamiento síncrono, si el servicio está disponible ya está listo"""
    return {"status": "ready"}

# Nota: La aplicación se ejecuta con Granian (servidor ASGI en Rust)
# Ver run_server.sh (local) o Dockerfile (producción) para configuración del servidor
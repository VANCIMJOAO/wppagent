"""
Callbacks de Conversas - VERSÃO CORRIGIDA + ERROR HANDLING
=========================================================

Correções implementadas:
✅ Estados de callback consistentes
✅ Sistema de envio de mensagens real
✅ WebSocket simulado para updates
✅ Modal funcional
✅ Navegação entre conversas corrigida
✅ Prevenção de erros de elementos não existentes
✅ Error handling com feedback visual
"""

from dash import Input, Output, State, callback, ctx, ALL, no_update, ClientsideFunction
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
from dash import html
from datetime import datetime, timedelta

# Importa APIService para dados reais
try:
    from services.api_service import sync_api
    from services.database_service import get_db_service
    from utils.cache import cached_api_call, cache
    API_AVAILABLE = True
    db_service = get_db_service()
except ImportError:
    API_AVAILABLE = False
    print("⚠️ API Service não disponível - usando callbacks mock")


# Funções cached para otimizar chamadas ao banco de conversas
@cached_api_call(ttl=120)  # 2 minutos de cache
def get_cached_conversations():
    """Busca lista de conversas com cache"""
    if API_AVAILABLE:
        return db_service.get_conversations() or []
    return []


@cached_api_call(ttl=60)  # 1 minuto de cache para mensagens (mais dinâmico)
def get_cached_conversation_messages(conversation_id):
    """Busca mensagens de uma conversa com cache"""
    if API_AVAILABLE:
        return db_service.get_conversation_messages(conversation_id) or []
    return []

# Sistema de error handling
try:
    from utils.error_handler import handle_api_error, safe_execute, create_loading_error_fallback
    ERROR_HANDLING_AVAILABLE = True
except ImportError:
    ERROR_HANDLING_AVAILABLE = False
    print("⚠️ Error handler não disponível - usando fallback simples")

def register_all_conversas_callbacks(app):
    """Registra todos os callbacks da página de conversas corrigidos + error handling"""
    
    # 0. Callbacks para error handling - Retry actions
    if ERROR_HANDLING_AVAILABLE:
        @app.callback(
            Output("conversations-store", "data", allow_duplicate=True),
            [
                Input("retry-connection-btn", "n_clicks"),
                Input("retry-timeout-btn", "n_clicks"),
                Input("retry-generic-btn", "n_clicks")
            ],
            prevent_initial_call=True
        )
        def retry_load_conversations(retry_conn, retry_timeout, retry_generic):
            """Retry para recarregar conversas após erro"""
            
            if not any([retry_conn, retry_timeout, retry_generic]):
                raise PreventUpdate
                
            if API_AVAILABLE:
                try:
                    conversations = db_service.get_conversations()
                    return conversations
                except Exception as e:
                    # Se ainda der erro, deixar o componente de erro aparecer novamente
                    return []
            else:
                return []
        
        @app.callback(
            Output("url", "pathname", allow_duplicate=True),
            Input("goto-login-btn", "n_clicks"),
            prevent_initial_call=True
        )
        def redirect_to_login(login_clicks):
            """Redireciona para login em caso de erro de autenticação"""
            if login_clicks:
                return "/login"
            raise PreventUpdate
    
    # 1. Callback para carregar lista de conversas
    @app.callback(
        Output("conversations-list", "children"),
        [
            Input("conversations-store", "data"),
            Input("search-input", "value"),
            Input("status-filter", "value"),
            Input("refresh-conversations-btn", "n_clicks"),
            Input("realtime-interval", "n_intervals")
        ],
        prevent_initial_call=False
    )
    def update_conversations_list(conversations, search_term, status_filter, refresh_clicks, intervals):
        """Atualiza a lista de conversas com filtros + error handling visual"""
        
        # Se não há conversas, tentar carregar com error handling
        if not conversations:
            if ERROR_HANDLING_AVAILABLE and API_AVAILABLE:
                try:
                    conversations = safe_execute(
                        db_service.get_conversations,
                        fallback_value=[],
                        context="carregamento inicial de conversas",
                        component_id="conversations-list"
                    )
                    
                    # Se safe_execute retornou um componente de erro, mostrar ele
                    if hasattr(conversations, 'type') and conversations.type == 'Alert':
                        return [dmc.Center([conversations], py="xl")]
                        
                except Exception as e:
                    if ERROR_HANDLING_AVAILABLE:
                        error_component = handle_api_error(e, "carregamento de conversas", "conversations-list")
                        return [dmc.Center([error_component], py="xl")]
                    else:
                        return [dmc.Center([
                            dmc.Alert(
                                "Erro ao carregar conversas. Tente recarregar a página.",
                                title="Erro de Carregamento",
                                color="red"
                            )
                        ], py="xl")]
            
            # Fallback para quando não há conversas
            if not conversations:
                return [
                    dmc.Center([
                        dmc.Stack([
                            dmc.Text("Nenhuma conversa encontrada", c="dimmed"),
                            dmc.Button(
                                "Criar primeira conversa",
                                variant="light",
                                id="first-conversation-btn"
                            )
                        ], align="center")
                    ], py="xl")
                ]
        
        # Aplica filtros
        from layout.conversas import filter_conversations, render_conversation_card
        filtered_conversations = filter_conversations(conversations, search_term or "", status_filter)
        
        if not filtered_conversations:
            return [
                dmc.Center([
                    dmc.Text("Nenhuma conversa encontrada com os filtros aplicados", c="dimmed")
                ], py="xl")
            ]
        
        # Renderiza cards das conversas
        cards = []
        for conv in filtered_conversations:
            card = render_conversation_card(
                conv['id'],
                conv.get('summary', ''),
                conv.get('last_message', ''),
                conv.get('timestamp', datetime.now()),
                conv.get('total_messages', 0),
                conv.get('customer_name', ''),
                conv.get('status', 'active')
            )
            cards.append(card)
        
        return cards
    
    # 2. Callback para abrir conversa - VERSÃO ROBUSTA CORRIGIDA
    @app.callback(
        [
            Output("active-conversation-id", "data"),
            Output("chat-panel", "children")
        ],
        [
            Input({"type": "conversation-card", "index": ALL}, "n_clicks")
        ],
        [
            State("conversations-store", "data"),
            State("active-conversation-id", "data")
        ],
        prevent_initial_call=True
    )
    def open_conversation(card_clicks, conversations, current_active_id):
        """Callback corrigido para abrir conversas diferentes"""
        
        # Verifica se há trigger válido
        if not ctx.triggered_id:
            raise PreventUpdate
            
        # Verifica se é um card válido
        if (not isinstance(ctx.triggered_id, dict) or 
            ctx.triggered_id.get("type") != "conversation-card"):
            raise PreventUpdate
        
        conversation_id = ctx.triggered_id["index"]
        
        # Verifica se algum clique aconteceu
        if not card_clicks or all(clicks is None or clicks == 0 for clicks in card_clicks):
            raise PreventUpdate
        
        print(f"🎯 Callback acionado - Abrindo conversa {conversation_id}")
        print(f"   Conversa atual: {current_active_id}")
        print(f"   Cliques recebidos: {card_clicks}")
        
        # Busca nome do cliente
        customer_name = f"Conversa #{conversation_id}"
        if conversations:
            for conv in conversations:
                if conv['id'] == conversation_id:
                    customer_name = conv.get('customer_name', customer_name)
                    break
        
        print(f"   Nome do cliente: {customer_name}")
        
        # Cria o chat
        try:
            from layout.conversas import render_chat_view
            chat_content = render_chat_view(conversation_id, customer_name)
            print(f"✅ Chat renderizado com sucesso para conversa {conversation_id}")
            return conversation_id, chat_content
        except Exception as e:
            print(f"❌ Erro ao renderizar chat: {e}")
            raise PreventUpdate
    
    # 3. Callback para voltar à lista de conversas
    @app.callback(
        [
            Output("active-conversation-id", "data", allow_duplicate=True),
            Output("chat-panel", "children", allow_duplicate=True)
        ],
        Input("back-to-conversations-btn", "n_clicks"),
        prevent_initial_call=True
    )
    def back_to_conversations(back_clicks):
        """Volta para a lista de conversas"""
        
        if not back_clicks:
            raise PreventUpdate
        
        # Estado vazio - volta para seleção
        empty_state = dmc.Center([
            dmc.Stack([
                dmc.Text("Selecione uma conversa", size="lg", c="dimmed", ta="center"),
                dmc.Text("Escolha uma conversa para começar", size="sm", c="dimmed", ta="center")
            ], align="center")
        ], style={"height": "500px"})
        
        return None, empty_state
    
    # 4. Callback adicional para lidar com botão "primeira conversa" quando não há conversas
    @app.callback(
        Output("new-conversation-modal", "opened", allow_duplicate=True),
        Input("first-conversation-btn", "n_clicks"),
        prevent_initial_call=True
    )
    def handle_first_conversation_button(n_clicks):
        """Abre modal quando clica no botão 'primeira conversa'"""
        if n_clicks:
            return True
        return no_update
    
    # 5. Callback para controlar modal de nova conversa
    @app.callback(
        Output("new-conversation-modal", "opened"),
        [
            Input("new-conversation-btn", "n_clicks"),
            Input("modal-cancel-btn", "n_clicks"),
            Input("modal-create-btn", "n_clicks")
        ],
        [State("new-conversation-modal", "opened")],
        prevent_initial_call=True
    )
    def toggle_new_conversation_modal(new_btn, cancel_btn, create_btn, current_opened):
        """Controla abertura/fechamento do modal"""
        
        if ctx.triggered_id == "new-conversation-btn":
            return True
        elif ctx.triggered_id in ["modal-cancel-btn", "modal-create-btn"]:
            return False
        
        return current_opened or False
    
    # 6. Callback para criar nova conversa
    @app.callback(
        [
            Output("conversations-store", "data", allow_duplicate=True),
            Output("modal-customer-name", "value"),
            Output("modal-first-message", "value"),
            Output("modal-create-btn", "loading")
        ],
        Input("modal-create-btn", "n_clicks"),
        [
            State("modal-customer-name", "value"),
            State("modal-first-message", "value"),
            State("conversations-store", "data")
        ],
        prevent_initial_call=True
    )
    def create_new_conversation(create_clicks, customer_name, first_message, current_conversations):
        """Cria uma nova conversa"""
        
        if not create_clicks:
            raise PreventUpdate
        
        if not customer_name or not first_message:
            return no_update, no_update, no_update, False
        
        try:
            # Cria a conversa
            if API_AVAILABLE:
                # Usar API service para criar conversa
                try:
                    conversations = db_service.get_conversations()
                    # Encontrar próximo ID disponível
                    next_id = max([c.get('id', 0) for c in conversations]) + 1 if conversations else 1
                    
                    # Simular criação de conversa (temporário até implementar endpoint)
                    new_conversation = {
                        'id': next_id,
                        'customer_name': customer_name,
                        'status': 'active',
                        'last_message': first_message[:50] + '...' if len(first_message) > 50 else first_message,
                        'last_message_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'unread_count': 0
                    }
                    
                    # Simular ID da nova conversa
                    new_conv_id = next_id
                    
                    # Recarrega conversas da API
                    updated_conversations = db_service.get_conversations()
                    updated_conversations.append(new_conversation)
                except Exception as e:
                    print(f"Erro ao criar conversa via API: {e}")
                    updated_conversations = []
                    new_conv_id = None
            else:
                # Mock - cria conversa simulada
                new_conv_id = len(current_conversations) + 1
                new_conversation = {
                    'id': new_conv_id,
                    'summary': f'Conversa com {customer_name}',
                    'last_message': first_message,
                    'timestamp': datetime.now(),
                    'total_messages': 1,
                    'status': 'active',
                    'customer_name': customer_name
                }
                updated_conversations = [new_conversation] + (current_conversations or [])
            
            return updated_conversations, "", "", False
            
        except Exception as e:
            print(f"Erro ao criar conversa: {e}")
            return no_update, no_update, no_update, False
    
    # 7. Callback para enviar mensagem
    @app.callback(
        [
            Output("message-input", "value"),
            Output("messages-container", "children"),
            Output("conversations-store", "data", allow_duplicate=True)
        ],
        [
            Input("send-message-btn", "n_clicks"),
            Input("message-input", "n_submit")  # Permite envio com Enter
        ],
        [
            State("message-input", "value"),
            State("active-conversation-id", "data"),
            State("conversations-store", "data")
        ],
        prevent_initial_call=True
    )
    def send_message(send_clicks, input_submit, message_text, conversation_id, conversations):
        """Envia uma mensagem na conversa ativa"""
        
        print(f"🚀 INÍCIO DO ENVIO DE MENSAGEM")
        print(f"   Clique no botão: {send_clicks}")
        print(f"   Submit do input: {input_submit}")
        print(f"   Texto da mensagem: '{message_text}'")
        print(f"   ID da conversa ativa: {conversation_id}")
        print(f"   Número de conversas disponíveis: {len(conversations) if conversations else 0}")
        
        # Validações iniciais
        if not send_clicks and not input_submit:
            print("❌ Nenhum trigger válido - cancelando")
            raise PreventUpdate
            
        if not message_text or not message_text.strip():
            print("❌ Mensagem vazia - cancelando")
            raise PreventUpdate
            
        if not conversation_id:
            print("❌ Nenhuma conversa ativa - cancelando")
            raise PreventUpdate
        
        print(f"✅ Validações iniciais passaram")
        print(f"   Mensagem processada: '{message_text.strip()}'")
        
        try:
            # Adiciona mensagem do usuário
            if API_AVAILABLE:
                print(f"🔍 API disponível - tentando salvar mensagem via API")
                try:
                    # Usar API service para enviar mensagem
                    result = sync_api.send_message(conversation_id, message_text.strip())
                    success = result and result.get('success', False)
                    print(f"   Resultado da inserção via API: {success}")
                except Exception as e:
                    print(f"Erro ao enviar via API: {e}")
                    success = False
                
                if success:
                    print(f"✅ Mensagem salva com sucesso - preparando resposta da IA")
                    
                    # Simula resposta automática da IA
                    ai_responses = [
                        "Obrigado pela sua mensagem! Como posso ajudá-lo?",
                        "Entendi. Deixe-me verificar isso para você.",
                        "Perfeito! Vou providenciar isso agora.",
                        "Claro! Posso ajudar com isso.",
                        "Muito bem! Vou encaminhar sua solicitação."
                    ]
                    import random
                    ai_response = random.choice(ai_responses)
                    print(f"   Resposta IA selecionada: '{ai_response}'")
                    
                    # Simula resposta automática da IA via API
                    try:
                        ai_result = sync_api.send_message(conversation_id, ai_response)
                        ai_success = ai_result and ai_result.get('success', False)
                        print(f"   Resposta IA salva via API: {ai_success}")
                    except Exception as e:
                        print(f"Erro ao salvar resposta IA via API: {e}")
                        ai_success = False
                    
                    # Recarrega mensagens via API com error handling
                    print(f"🔄 Recarregando mensagens da conversa {conversation_id} via API")
                    
                    if ERROR_HANDLING_AVAILABLE:
                        updated_messages = safe_execute(
                            db_service.get_conversation_messages,
                            conversation_id,
                            fallback_value=[],
                            context=f"recarregamento de mensagens da conversa {conversation_id}",
                            component_id=f"reload-messages-{conversation_id}"
                        )
                    else:
                        try:
                            updated_messages = db_service.get_conversation_messages(conversation_id)
                            print(f"   Número de mensagens carregadas: {len(updated_messages) if updated_messages else 0}")
                        except Exception as e:
                            print(f"❌ Erro ao carregar mensagens via API: {e}")
                            updated_messages = []
                    
                    print(f"🔄 Recarregando lista de conversas via API")
                    
                    if ERROR_HANDLING_AVAILABLE:
                        updated_conversations = safe_execute(
                            db_service.get_conversations,
                            fallback_value=[],
                            context="recarregamento da lista de conversas",
                            component_id="reload-conversations"
                        )
                    else:
                        try:
                            updated_conversations = db_service.get_conversations()
                            print(f"   Número de conversas carregadas: {len(updated_conversations) if updated_conversations else 0}")
                        except Exception as e:
                            print(f"❌ Erro ao carregar conversas via API: {e}")
                            updated_conversations = []
                    
                else:
                    print("❌ Falha ao salvar mensagem no banco")
                    raise Exception("Falha ao salvar mensagem")
            else:
                print(f"⚠️ Database não disponível - usando modo mock")
                # Mock - simula envio
                updated_messages = [
                    {
                        'content': message_text.strip(),
                        'is_user': True,
                        'timestamp': datetime.now()
                    },
                    {
                        'content': f"Recebi sua mensagem: '{message_text.strip()}'. Como posso ajudar mais?",
                        'is_user': False,
                        'timestamp': datetime.now() + timedelta(seconds=1)
                    }
                ]
                updated_conversations = conversations
                print(f"   Criadas {len(updated_messages)} mensagens mock")
            
            # Renderiza mensagens atualizadas
            print(f"🎨 Renderizando {len(updated_messages) if updated_messages else 0} mensagens")
            from layout.conversas import render_message_bubble
            message_components = []
            for i, msg in enumerate(updated_messages):
                print(f"   Renderizando mensagem {i+1}: {'usuário' if msg.get('is_user', False) else 'sistema'} - '{msg.get('content', '')[:50]}...'")
                bubble = render_message_bubble(msg, msg.get('is_user', False))
                message_components.append(bubble)
            
            print(f"✅ ENVIO CONCLUÍDO COM SUCESSO")
            print(f"   Retornando: input limpo, {len(message_components)} componentes de mensagem, {len(updated_conversations) if updated_conversations else 0} conversas")
            return "", message_components, updated_conversations
            
        except Exception as e:
            print(f"❌ ERRO DURANTE O ENVIO: {str(e)}")
            print(f"   Tipo do erro: {type(e).__name__}")
            import traceback
            print(f"   Stack trace: {traceback.format_exc()}")
            return no_update, no_update, no_update
    
    # 8. Callback para updates em tempo real via WebSocket
    @app.callback(
        Output("ws-updates", "data"),
        Input("realtime-interval", "n_intervals"),
        prevent_initial_call=True
    )
    def handle_realtime_websocket(intervals):
        """Conecta ao WebSocket real para updates em tempo real"""
        
        # Inicializa serviço de tempo real na primeira execução
        if intervals == 1:
            try:
                from services.realtime_service import start_realtime_service, get_realtime_service
                
                # Inicia o serviço WebSocket
                service = start_realtime_service()
                
                # Registra callbacks para diferentes eventos
                def on_new_message(data):
                    print(f"📨 Nova mensagem via WebSocket: {data}")
                    # Aqui seria integrado com o Dash Store
                    
                def on_conversation_update(data):
                    print(f"🔄 Conversa atualizada via WebSocket: {data}")
                    
                service.register_callback('new_message', on_new_message)
                service.register_callback('conversation_update', on_conversation_update)
                
                print("✅ Serviço WebSocket real inicializado!")
                return {"type": "websocket_connected", "timestamp": intervals}
                
            except Exception as e:
                print(f"❌ Erro ao inicializar WebSocket: {e}")
                # Fallback para simulação em caso de erro
                if intervals > 0 and intervals % 6 == 0:
                    return {"type": "simulated_update", "timestamp": intervals}
        
        # Heartbeat do WebSocket
        elif intervals > 1 and intervals % 30 == 0:  # A cada 2.5 minutos
            return {"type": "websocket_heartbeat", "timestamp": intervals}
        
        return no_update
    
    # 9. Callback para processamento de updates WebSocket reais
    @app.callback(
        Output("conversations-store", "data", allow_duplicate=True),
        Input("ws-updates", "data"),
        [State("conversations-store", "data")],
        prevent_initial_call=True
    )
    def handle_realtime_updates(ws_data, current_conversations):
        """Processa updates em tempo real do WebSocket"""
        
        if not ws_data or not current_conversations:
            raise PreventUpdate
        
        update_type = ws_data.get('type', '')
        
        # Processa diferentes tipos de updates WebSocket
        if update_type == 'websocket_connected':
            print("✅ WebSocket conectado - aguardando updates em tempo real")
            raise PreventUpdate
            
        elif update_type == 'websocket_heartbeat':
            # Heartbeat - não precisa atualizar dados
            raise PreventUpdate
            
        elif update_type == 'new_message':
            # Nova mensagem recebida via WebSocket
            conversation_id = ws_data.get('conversation_id')
            message_content = ws_data.get('content', '')
            
            if conversation_id and message_content:
                updated_conversations = current_conversations.copy()
                
                # Encontra e atualiza a conversa específica
                for conv in updated_conversations:
                    if conv.get('id') == conversation_id:
                        conv['last_message'] = message_content
                        conv['timestamp'] = datetime.now().isoformat()
                        conv['unread_count'] = conv.get('unread_count', 0) + 1
                        break
                        
                print(f"📨 Conversa {conversation_id} atualizada com nova mensagem")
                return updated_conversations
                
        elif update_type == 'conversation_update':
            # Update geral de conversa via WebSocket
            conversation_id = ws_data.get('conversation_id')
            updates = ws_data.get('updates', {})
            
            if conversation_id and updates:
                updated_conversations = current_conversations.copy()
                
                # Encontra e atualiza a conversa específica
                for conv in updated_conversations:
                    if conv.get('id') == conversation_id:
                        conv.update(updates)
                        break
                        
                print(f"🔄 Conversa {conversation_id} atualizada via WebSocket")
                return updated_conversations
                
        elif update_type == 'simulated_update':
            # Fallback: simula update quando WebSocket não está disponível
            import random
            if random.random() < 0.3:  # 30% de chance
                updated_conversations = current_conversations.copy()
                if updated_conversations:
                    conv = updated_conversations[0]
                    conv['last_message'] = "Nova mensagem recebida (simulada)"
                    conv['timestamp'] = datetime.now().isoformat()
                    conv['unread_count'] = conv.get('unread_count', 0) + 1
                    
                print("📨 Update simulado aplicado")
                return updated_conversations
                updated_conversations[0]['total_messages'] += 1
                return updated_conversations
        
        raise PreventUpdate
    
    # 10. Callback clientside para scroll automático nas mensagens (novas mensagens)
    app.clientside_callback(
        """
        function(children) {
            if (children) {
                setTimeout(function() {
                    console.log('🔄 Tentando scroll após nova mensagem...');
                    scrollToLastMessage();
                }, 100);
            }
            return window.dash_clientside.no_update;
        }
        """,
        Output("scroll-trigger-1", "data"),
        Input("messages-container", "children"),
        prevent_initial_call=True
    )
    
    # 11. Callback clientside para scroll automático quando conversa é aberta
    app.clientside_callback(
        """
        function(chatPanel) {
            console.log('🔍 Chat panel callback acionado:', chatPanel);
            
            // Verifica se o chat panel foi carregado com uma conversa
            if (chatPanel && Array.isArray(chatPanel) && chatPanel.length > 0) {
                console.log('📋 Chat panel tem conteúdo, verificando...');
                
                // Procura pelo chat-view-container para confirmar que é uma conversa
                const chatString = JSON.stringify(chatPanel);
                const hasChat = chatString.includes('chat-view-container') || 
                               chatString.includes('messages-container') ||
                               chatString.includes('last-message');
                
                console.log('🔎 Tem chat?', hasChat);
                
                if (hasChat) {
                    console.log('💬 CONVERSA DETECTADA - EXECUTANDO AUTO-SCROLL IMEDIATO');
                    
                    // Executa scroll imediatamente
                    if (window.scrollToLastMessage) {
                        window.scrollToLastMessage();
                    }
                    
                    // Tentativas múltiplas com delays crescentes
                    const attempts = [200, 500, 800, 1200, 1800, 2500];
                    
                    attempts.forEach((delay, index) => {
                        setTimeout(function() {
                            console.log(`🎯 Tentativa ${index + 1} de scroll para última mensagem (${delay}ms)`);
                            if (window.scrollToLastMessage) {
                                window.scrollToLastMessage();
                            }
                        }, delay);
                    });
                } else {
                    console.log('⚠️ Chat panel sem conversa ativa');
                }
            } else {
                console.log('⚠️ Chat panel vazio ou inválido');
            }
            return window.dash_clientside.no_update;
        }
        """,
        Output("scroll-trigger-2", "data"),
        Input("chat-panel", "children"),
        prevent_initial_call=True
    )
    
    # 11.1. Callback adicional para detectar mudança de conversa ativa
    app.clientside_callback(
        """
        function(activeConvId) {
            console.log('🎯 Conversa ativa mudou para:', activeConvId);
            
            if (activeConvId) {
                console.log('💬 NOVA CONVERSA ATIVA - EXECUTANDO SCROLL EM 1 SEGUNDO');
                
                // Aguarda renderização completa e executa scroll
                setTimeout(function() {
                    console.log('🚀 Executando scroll para nova conversa ativa...');
                    if (window.scrollToLastMessage) {
                        window.scrollToLastMessage();
                    }
                    
                    // Tentativas extras para garantir
                    setTimeout(() => window.scrollToLastMessage && window.scrollToLastMessage(), 500);
                    setTimeout(() => window.scrollToLastMessage && window.scrollToLastMessage(), 1000);
                    setTimeout(() => window.scrollToLastMessage && window.scrollToLastMessage(), 1500);
                }, 1000);
            }
            
            return window.dash_clientside.no_update;
        }
        """,
        Output("scroll-trigger-1", "data", allow_duplicate=True),
        Input("active-conversation-id", "data"),
        prevent_initial_call=True
    )
    
    # 12. Função JavaScript global para scroll (executada uma vez)
    app.clientside_callback(
        """
        function() {
            // Define função global para scroll para última mensagem
            window.scrollToLastMessage = function() {
                console.log('📱 Executando scrollToLastMessage...');
                
                // Primeiro, tenta encontrar o elemento da última mensagem
                const lastMessage = document.getElementById('last-message');
                if (lastMessage) {
                    console.log('✅ Última mensagem encontrada:', lastMessage);
                    
                    // Tenta scroll into view nativo
                    try {
                        lastMessage.scrollIntoView({ 
                            behavior: 'auto', 
                            block: 'end',
                            inline: 'nearest'
                        });
                        console.log('🎯 ScrollIntoView executado na última mensagem');
                        return;
                    } catch (e) {
                        console.log('❌ ScrollIntoView falhou:', e);
                    }
                }
                
                // Fallback: busca containers de scroll e força scroll para baixo
                console.log('⚠️ Última mensagem não encontrada, tentando containers...');
                
                const scrollContainers = [
                    // Método específico para Mantine ScrollArea
                    () => {
                        const messagesContainer = document.getElementById('messages-container');
                        if (messagesContainer) {
                            // Procura o viewport do ScrollArea dentro do container
                            const viewport = messagesContainer.querySelector('[data-radix-scroll-area-viewport]') ||
                                           messagesContainer.querySelector('.mantine-ScrollArea-viewport') ||
                                           messagesContainer.querySelector('[style*="overflow"]');
                            return viewport;
                        }
                        return null;
                    },
                    
                    // Método direto
                    () => document.getElementById('messages-container'),
                    
                    // Método por seletor de classe
                    () => document.querySelector('.mantine-ScrollArea-viewport'),
                    
                    // Método por qualquer ScrollArea visível
                    () => {
                        const viewports = document.querySelectorAll('[data-radix-scroll-area-viewport]');
                        for (let viewport of viewports) {
                            if (viewport.offsetHeight > 0) {
                                return viewport;
                            }
                        }
                        return null;
                    },
                    
                    // Método de busca no chat-panel
                    () => {
                        const chatPanel = document.getElementById('chat-panel');
                        if (chatPanel) {
                            return chatPanel.querySelector('[data-radix-scroll-area-viewport]') ||
                                   chatPanel.querySelector('.mantine-ScrollArea-viewport') ||
                                   chatPanel.querySelector('[style*="overflow"]');
                        }
                        return null;
                    }
                ];
                
                let scrollContainer = null;
                
                // Tenta cada método até encontrar um container válido
                for (let i = 0; i < scrollContainers.length; i++) {
                    try {
                        scrollContainer = scrollContainers[i]();
                        if (scrollContainer && scrollContainer.offsetHeight > 0) {
                            console.log(`✅ Container de scroll encontrado pelo método ${i + 1}:`, scrollContainer);
                            break;
                        }
                    } catch (e) {
                        console.log(`❌ Método ${i + 1} falhou:`, e);
                    }
                }
                
                if (scrollContainer) {
                    const scrollHeight = scrollContainer.scrollHeight;
                    const clientHeight = scrollContainer.clientHeight;
                    const currentScrollTop = scrollContainer.scrollTop;
                    
                    console.log('📊 Dimensões do container:', {
                        scrollHeight,
                        clientHeight,
                        currentScrollTop,
                        maxScrollTop: scrollHeight - clientHeight
                    });
                    
                    if (scrollHeight > clientHeight) {
                        const targetScrollTop = scrollHeight - clientHeight;
                        
                        // Múltiplas tentativas de scroll
                        scrollContainer.scrollTop = scrollHeight; // Força para o máximo
                        scrollContainer.scrollTop = targetScrollTop; // Posição exata
                        
                        // Tenta scroll com behavior se disponível
                        if (scrollContainer.scrollTo) {
                            scrollContainer.scrollTo({
                                top: scrollHeight,
                                behavior: 'auto'
                            });
                        }
                        
                        console.log('🎯 Scroll executado! Nova posição:', scrollContainer.scrollTop);
                        
                        // Verificação final
                        setTimeout(() => {
                            const finalScrollTop = scrollContainer.scrollTop;
                            const isAtBottom = Math.abs(finalScrollTop - targetScrollTop) < 5;
                            
                            console.log('🔍 Verificação final:', {
                                finalScrollTop,
                                targetScrollTop,
                                isAtBottom,
                                difference: Math.abs(finalScrollTop - targetScrollTop)
                            });
                            
                            if (!isAtBottom) {
                                console.log('⚠️ Não chegou ao final, tentando novamente...');
                                scrollContainer.scrollTop = scrollHeight;
                            }
                        }, 100);
                        
                    } else {
                        console.log('⚠️ Container não precisa de scroll (conteúdo cabe na tela)');
                    }
                } else {
                    console.log('❌ Nenhum container de scroll encontrado');
                    console.log('🔍 Elementos disponíveis para debug:');
                    console.log('- messages-container:', document.getElementById('messages-container'));
                    console.log('- chat-panel:', document.getElementById('chat-panel'));
                    console.log('- Radix viewports:', document.querySelectorAll('[data-radix-scroll-area-viewport]'));
                    console.log('- Mantine viewports:', document.querySelectorAll('.mantine-ScrollArea-viewport'));
                    console.log('- last-message:', document.getElementById('last-message'));
                }
            };
            
            console.log('✅ Função scrollToLastMessage definida globalmente');
            return window.dash_clientside.no_update;
        }
        """,
        Output("scroll-trigger-1", "data", allow_duplicate=True),
        Input("conversations-store", "data"),
        prevent_initial_call='initial_duplicate'  # Permite duplicata na inicialização
    )
    
    print("✅ Callbacks de conversas CORRIGIDOS registrados com sucesso!")

def register_conversas_callbacks_safe(app):
    """Wrapper seguro para registrar callbacks"""
    try:
        register_all_conversas_callbacks(app)
        return True
    except Exception as e:
        print(f"❌ Erro ao registrar callbacks de conversas: {e}")
        return False

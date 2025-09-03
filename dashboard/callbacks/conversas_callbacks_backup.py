"""
Callbacks para a página de conversas
"""

from dash import Input, Output, State, callback, ctx, ALL, no_update
from utils.database import get_conversations, get_conversation_messages, create_conversation, add_message_to_conversation

def register_all_conversas_callbacks(app):
    """Registra todos os callbacks da página de conversas"""
    
    @app.callback(
        Output("conversations-content", "children"),
        [Input("conversations-data", "data"),
         Input("search-conversations", "value"),
         Input("filter-conversations", "value")],
        prevent_initial_call=True
    )
    def update_conversations_list(conversations, search_term, filter_option):
        # Sempre retorna apenas a lista de conversas para o painel esquerdo
        from layout.conversas import render_conversations_grid
        return render_conversations_grid(conversations or [], search_term, filter_option)
    
    @app.callback(
        Output("chat-panel-content", "children"),
        [Input("active-conversation", "data")],
        [State("conversations-data", "data")],
        prevent_initial_call=True
    )
    def update_chat_panel(active_conversation, conversations_data):
        if active_conversation:
            from layout.conversas import render_chat_view
            
            # Busca o nome do cliente na lista de conversas
            customer_name = None
            if conversations_data:
                for conv in conversations_data:
                    if conv.get('id') == active_conversation:
                        customer_name = conv.get('customer_name')
                        break
            
            return render_chat_view(active_conversation, customer_name)
        else:
            # Estado vazio - selecione uma conversa
            from dash import html
            return html.Div([
                html.Div([
                    html.I(className="fas fa-comments empty-icon"),
                    html.H2("Selecione uma conversa", className="empty-title"),
                    html.P("Escolha uma conversa à esquerda para iniciar", className="empty-subtitle")
                ], className="empty-chat-state")
            ])

    @app.callback(
        Output("active-conversation", "data"),
        [Input({"type": "open-chat", "index": ALL}, "n_clicks")],
        [State("active-conversation", "data")],
        prevent_initial_call=True
    )
    def handle_conversation_navigation(chat_clicks, current_active):
        if ctx.triggered_id and ctx.triggered_id.get("type") == "open-chat":
            return ctx.triggered_id["index"]
        return current_active
    
    # Callback separado para o botão de voltar que só é executado quando existe
    @app.callback(
        Output("active-conversation", "data", allow_duplicate=True),
        [Input("back-to-conversations", "n_clicks")],
        prevent_initial_call=True
    )
    def handle_back_to_conversations(back_clicks):
        if back_clicks:
            return None
        return None

    @app.callback(
        Output("new-conversation-modal", "style"),
        [Input("new-conversation-btn", "n_clicks"),
         Input("first-conversation-btn", "n_clicks"),
         Input("close-modal", "n_clicks"),
         Input("cancel-new-conversation", "n_clicks")],
        prevent_initial_call=True
    )
    def toggle_new_conversation_modal(new_btn, first_btn, close_btn, cancel_btn):
        if ctx.triggered_id in ["new-conversation-btn", "first-conversation-btn"]:
            return {"display": "flex"}
        else:
            return {"display": "none"}

    @app.callback(
        [Output("conversations-data", "data", allow_duplicate=True),
         Output("new-conversation-subject", "value"),
         Output("new-conversation-message", "value")],
        [Input("create-new-conversation", "n_clicks")],
        [State("new-conversation-subject", "value"),
         State("new-conversation-message", "value")],
        prevent_initial_call=True
    )
    def create_new_conversation_callback(n_clicks, subject, message):
        if n_clicks and message:
            new_conv_id = create_conversation(subject or "Nova conversa", message)
            if new_conv_id:
                updated_conversations = get_conversations()
                return updated_conversations, "", ""
        return no_update, no_update, no_update

    # Callback para enviar mensagens - evita erros de elementos não existentes
    @app.callback(
        Output("chat-panel-content", "children", allow_duplicate=True),
        [Input("send-message-btn", "n_clicks")],
        [State("new-message-input", "value"),
         State("active-conversation", "data"),
         State("conversations-data", "data")],
        prevent_initial_call=True
    )
    def send_message(n_clicks, message_content, conversation_id, conversations_data):
        # Só executa se todos os elementos existirem
        if not n_clicks or not message_content or not conversation_id:
            return no_update
            
        try:
            # Adiciona a mensagem do usuário
            success = add_message_to_conversation(conversation_id, message_content, is_user=True)
            
            if success:
                # Simula uma resposta da IA
                ai_response = f"Recebi sua mensagem: '{message_content}'. Como posso ajudá-lo mais?"
                add_message_to_conversation(conversation_id, ai_response, is_user=False)
                
                # Busca o nome do cliente na lista de conversas
                customer_name = None
                if conversations_data:
                    for conv in conversations_data:
                        if conv.get('id') == conversation_id:
                            customer_name = conv.get('customer_name')
                            break
                
                # Retorna a view atualizada do chat
                from layout.conversas import render_chat_view
                return render_chat_view(conversation_id, customer_name)
        except Exception as e:
            print(f"Erro ao enviar mensagem: {e}")
            return no_update
        
        return no_update

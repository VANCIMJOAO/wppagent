"""
Callback Alternativo - Mais Robusto
==================================
"""

# Se os logs mostrarem que ainda há problema, substitua o callback atual por esta versão:

def open_conversation_robust(card_clicks, conversations, current_active_id):
    """Versão mais robusta do callback"""
    
    # FILTRO 1: Só prossegue se há trigger válido
    if not ctx.triggered or not ctx.triggered_id:
        raise PreventUpdate
    
    # FILTRO 2: Só prossegue se é um card de conversa
    if not isinstance(ctx.triggered_id, dict):
        raise PreventUpdate
        
    if ctx.triggered_id.get("type") != "conversation-card":
        raise PreventUpdate
    
    # FILTRO 3: Só prossegue se houve clique real (valor > 0)
    triggered_info = ctx.triggered[0]
    click_value = triggered_info.get('value')
    
    if not click_value or click_value <= 0:
        raise PreventUpdate
    
    # FILTRO 4: Só prossegue se é conversa diferente
    conversation_id = ctx.triggered_id["index"]
    
    if current_active_id == conversation_id:
        raise PreventUpdate
    
    # PROCESSA: Se chegou aqui, é um clique válido
    print(f"\\n🔄 ABRINDO CONVERSA {conversation_id}")
    
    # Busca dados da conversa
    customer_name = "Cliente Desconhecido"
    if conversations:
        for conv in conversations:
            if conv['id'] == conversation_id:
                customer_name = conv.get('customer_name', f'Cliente #{conversation_id}')
                break
    
    # Renderiza chat
    from layout.conversas import render_chat_view
    chat_content = render_chat_view(conversation_id, customer_name)
    
    print(f"✅ Chat criado: {customer_name}\\n")
    
    return conversation_id, chat_content

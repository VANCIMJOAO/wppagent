# 🛡️ EXEMPLO DE USO DAS VALIDAÇÕES NO DASHBOARD

"""
import logging
logger = logging.getLogger(__name__)

Exemplos de como usar as validações robustas em callbacks do Dash.
Este arquivo demonstra as melhores práticas de segurança.
"""

from dash import callback, Input, Output, State, html, dbc
from app.utils.validators import ValidationError, validate_dashboard_form, sanitize_dashboard_input

# ==================== EXEMPLO DE CALLBACK SEGURO ====================

@callback(
    [Output('user-form-feedback', 'children'),
     Output('user-form-feedback', 'color')],
    [Input('submit-user-btn', 'n_clicks')],
    [State('user-name-input', 'value'),
     State('user-phone-input', 'value'),
     State('user-email-input', 'value')]
)
def handle_user_form_submission(n_clicks, name, phone, email):
    """Exemplo de callback seguro para formulário de usuário"""
    if not n_clicks:
        return "", "light"
    
    try:
        # 1. Sanitizar todas as entradas primeiro
        raw_data = {
            'nome': name,
            'telefone': phone,
            'email': email
        }
        
        # 2. Sanitizar dados
        sanitized_data = sanitize_dashboard_input(raw_data)
        logger.info(f"🧹 Dados sanitizados: {sanitized_data}")
        
        # 3. Validar formulário
        validated_data = validate_dashboard_form(sanitized_data, 'user')
        logger.info("✅ Dados validados: {validated_data}")
        
        # 4. Aqui você salvaria no banco usando safe_execute_query
        # safe_execute_query(
        #     "INSERT INTO users (nome, telefone, wa_id, email) VALUES (:nome, :telefone, :wa_id, :email)",
        #     validated_data
        # )
        
        return dbc.Alert(
            [
                html.I(className="fas fa-check-circle me-2"),
                f"✅ Usuário {validated_data['nome']} criado com sucesso!"
            ],
            color="success",
            dismissable=True
        ), "success"
        
    except ValidationError as e:
        return dbc.Alert(
            [
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"❌ Erro de validação: {str(e)}"
            ],
            color="danger",
            dismissable=True
        ), "danger"
        
    except Exception as e:
        logger.error("❌ Erro inesperado: {e}")
        return dbc.Alert(
            [
                html.I(className="fas fa-bug me-2"),
                "❌ Erro interno do sistema. Tente novamente."
            ],
            color="danger",
            dismissable=True
        ), "danger"

# ==================== EXEMPLO DE BUSCA SEGURA ====================

@callback(
    Output('search-results', 'children'),
    [Input('search-btn', 'n_clicks')],
    [State('search-input', 'value'),
     State('search-table-dropdown', 'value')]
)
def handle_search(n_clicks, search_term, table_name):
    """Exemplo de callback seguro para busca"""
    if not n_clicks or not search_term:
        return "Digite um termo para buscar..."
    
    try:
        # 1. Validar parâmetros de busca
        from dashboard_whatsapp_complete import validate_search_params
        
        clean_term, validated_table = validate_search_params(search_term, table_name)
        
        # 2. Montar query segura
        if validated_table == 'users':
            query = """
                SELECT nome, telefone, email, created_at 
                FROM users 
                WHERE nome ILIKE :search_term 
                   OR telefone ILIKE :search_term 
                   OR email ILIKE :search_term
                ORDER BY created_at DESC 
                LIMIT 50
            """
        elif validated_table == 'messages':
            query = """
                SELECT m.content, m.direction, m.created_at, u.nome
                FROM messages m
                LEFT JOIN users u ON m.user_id = u.id
                WHERE m.content ILIKE :search_term
                ORDER BY m.created_at DESC
                LIMIT 50
            """
        else:
            raise ValidationError(f"Busca não implementada para tabela: {validated_table}")
        
        # 3. Executar query segura
        from dashboard_whatsapp_complete import safe_execute_query
        
        result = safe_execute_query(query, {'search_term': f'%{clean_term}%'})
        rows = result.fetchall() if result else []
        
        # 4. Retornar resultados
        if not rows:
            return dbc.Alert("Nenhum resultado encontrado.", color="info")
        
        return dbc.Table.from_dataframe(
            pd.DataFrame(rows),
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            className="mt-3"
        )
        
    except ValidationError as e:
        return dbc.Alert(f"❌ Erro de validação: {str(e)}", color="danger")
        
    except Exception as e:
        logger.error("❌ Erro na busca: {e}")
        return dbc.Alert("❌ Erro interno na busca.", color="danger")

# ==================== EXEMPLO DE PAGINAÇÃO SEGURA ====================

@callback(
    [Output('data-table', 'data'),
     Output('pagination-info', 'children')],
    [Input('page-input', 'value'),
     Input('per-page-dropdown', 'value')]
)
def handle_pagination(page, per_page):
    """Exemplo de callback seguro para paginação"""
    try:
        # 1. Validar parâmetros de paginação
        from dashboard_whatsapp_complete import validate_pagination_params
        
        valid_page, valid_per_page = validate_pagination_params(
            page or 1, 
            per_page or 25
        )
        
        # 2. Calcular offset
        offset = (valid_page - 1) * valid_per_page
        
        # 3. Query segura com paginação
        query = """
            SELECT nome, telefone, email, created_at
            FROM users
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """
        
        count_query = "SELECT COUNT(*) FROM users"
        
        # 4. Executar queries
        from dashboard_whatsapp_complete import safe_execute_query
        
        data_result = safe_execute_query(query, {
            'limit': valid_per_page,
            'offset': offset
        })
        
        count_result = safe_execute_query(count_query)
        
        # 5. Processar resultados
        rows = data_result.fetchall() if data_result else []
        total_count = count_result.fetchone()[0] if count_result else 0
        
        total_pages = (total_count + valid_per_page - 1) // valid_per_page
        
        data = [dict(row._mapping) for row in rows] if rows else []
        
        info = f"Página {valid_page} de {total_pages} ({total_count} registros total)"
        
        return data, info
        
    except ValidationError as e:
        return [], f"❌ Erro de validação: {str(e)}"
        
    except Exception as e:
        logger.error("❌ Erro na paginação: {e}")
        return [], "❌ Erro ao carregar dados"

# ==================== EXEMPLO DE FILTRO DE DATA SEGURO ====================

@callback(
    Output('filtered-data', 'children'),
    [Input('apply-date-filter-btn', 'n_clicks')],
    [State('start-date-picker', 'date'),
     State('end-date-picker', 'date')]
)
def handle_date_filter(n_clicks, start_date, end_date):
    """Exemplo de callback seguro para filtro de datas"""
    if not n_clicks:
        return "Selecione um intervalo de datas..."
    
    try:
        # 1. Validar intervalo de datas
        from dashboard_whatsapp_complete import validate_date_range
        
        valid_start, valid_end = validate_date_range(start_date, end_date)
        
        # 2. Query segura com filtro de data
        query = """
            SELECT 
                DATE(created_at) as data,
                COUNT(*) as total_mensagens,
                COUNT(DISTINCT user_id) as usuarios_unicos
            FROM messages
            WHERE created_at >= :start_date 
              AND created_at <= :end_date
            GROUP BY DATE(created_at)
            ORDER BY data DESC
        """
        
        # 3. Executar query
        from dashboard_whatsapp_complete import safe_execute_query
        
        result = safe_execute_query(query, {
            'start_date': valid_start,
            'end_date': valid_end
        })
        
        rows = result.fetchall() if result else []
        
        # 4. Criar visualização
        if not rows:
            return dbc.Alert("Nenhum dado encontrado no período selecionado.", color="info")
        
        df = pd.DataFrame(rows, columns=['Data', 'Total Mensagens', 'Usuários Únicos'])
        
        return [
            html.H5(f"Dados de {valid_start.strftime('%d/%m/%Y')} a {valid_end.strftime('%d/%m/%Y')}"),
            dbc.Table.from_dataframe(
                df,
                striped=True,
                bordered=True,
                hover=True,
                responsive=True
            )
        ]
        
    except ValidationError as e:
        return dbc.Alert(f"❌ Erro de validação: {str(e)}", color="danger")
        
    except Exception as e:
        logger.error("❌ Erro no filtro de data: {e}")
        return dbc.Alert("❌ Erro ao aplicar filtro de data.", color="danger")

# ==================== EXEMPLO DE UPLOAD SEGURO ====================

@callback(
    Output('upload-feedback', 'children'),
    [Input('upload-component', 'contents')],
    [State('upload-component', 'filename')]
)
def handle_file_upload(contents, filename):
    """Exemplo de callback seguro para upload de arquivos"""
    if not contents:
        return ""
    
    try:
        import base64
        import io
        
        # 1. Validar arquivo
        if not filename:
            raise ValidationError("Nome do arquivo é obrigatório")
        
        # Validar extensão
        allowed_extensions = ['.csv', '.xlsx', '.txt']
        if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
            raise ValidationError(f"Tipo de arquivo não permitido. Use: {', '.join(allowed_extensions)}")
        
        # Validar tamanho (base64 encoded)
        if len(contents) > 5 * 1024 * 1024:  # 5MB
            raise ValidationError("Arquivo muito grande (máximo 5MB)")
        
        # 2. Decodificar arquivo
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # 3. Processar baseado no tipo
        if filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif filename.endswith('.xlsx'):
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            raise ValidationError("Formato de arquivo não suportado para processamento")
        
        # 4. Validar estrutura dos dados
        if df.empty:
            raise ValidationError("Arquivo está vazio")
        
        if len(df) > 1000:
            raise ValidationError("Arquivo muito grande (máximo 1000 linhas)")
        
        # 5. Validar colunas necessárias (exemplo para usuários)
        required_columns = ['nome', 'telefone']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValidationError(f"Colunas obrigatórias ausentes: {', '.join(missing_columns)}")
        
        # 6. Validar cada linha
        validated_rows = []
        errors = []
        
        for index, row in df.iterrows():
            try:
                row_data = {
                    'nome': row.get('nome', ''),
                    'telefone': row.get('telefone', ''),
                    'email': row.get('email', '')
                }
                
                validated_row = validate_dashboard_form(row_data, 'user')
                validated_rows.append(validated_row)
                
            except ValidationError as e:
                errors.append(f"Linha {index + 1}: {str(e)}")
        
        # 7. Relatório de resultados
        if errors:
            error_summary = html.Div([
                html.H6("❌ Erros encontrados:", className="text-danger"),
                html.Ul([html.Li(error) for error in errors[:10]])  # Mostrar apenas 10 primeiros
            ])
            
            if len(errors) > 10:
                error_summary.children.append(
                    html.P(f"... e mais {len(errors) - 10} erros")
                )
        else:
            error_summary = ""
        
        success_count = len(validated_rows)
        
        return dbc.Card([
            dbc.CardBody([
                html.H5(f"📁 Arquivo: {filename}"),
                html.P(f"✅ {success_count} registros válidos"),
                html.P(f"❌ {len(errors)} registros com erro"),
                error_summary,
                html.Hr(),
                html.P("Registros válidos foram processados com sucesso!" if success_count > 0 else "Nenhum registro válido encontrado.")
            ])
        ])
        
    except ValidationError as e:
        return dbc.Alert(f"❌ Erro de validação: {str(e)}", color="danger")
        
    except Exception as e:
        logger.error("❌ Erro no upload: {e}")
        return dbc.Alert("❌ Erro ao processar arquivo.", color="danger")

logger.info("✅ Exemplos de callbacks seguros carregados!")

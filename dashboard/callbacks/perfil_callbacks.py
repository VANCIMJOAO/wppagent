"""
Perfil Callbacks
===============

Callbacks para a página de perfil do usuário, incluindo gerenciamento
de informações pessoais, configurações de notificação, logs de atividade
e status das integrações.
"""

from dash import Input, Output, State, callback, no_update, ctx
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from datetime import datetime, timedelta
import json

from services.queries import ProfileQueries

def register_perfil_callbacks(app):
    """
    Registra todos os callbacks da página de perfil.
    
    Args:
        app: Instância do app Dash
    """
    
    # Callback para carregar dados do perfil
    @app.callback(
        [
            Output('user-profile-data', 'data'),
            Output('notification-settings', 'data'),
            Output('activity-logs', 'data')
        ],
        Input('profile-tabs', 'value'),
        prevent_initial_call=False
    )
    def load_profile_data(active_tab):
        """
        Carrega dados do perfil do usuário quando a página é acessada.
        """
        try:
            # Carrega dados básicos do usuário
            user_data = {
                "full_name": "Administrador do Sistema",
                "email": "admin@wppagent.com", 
                "phone": "+55 11 99999-9999",
                "role": "Administrador",
                "timezone": "America/Sao_Paulo",
                "language": "pt-BR",
                "avatar_url": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&h=150&fit=crop&crop=face",
                "member_since": datetime.now() - timedelta(days=365),
                "status": "active"
            }
            
            # Configurações de notificação
            notification_settings = {
                "email_notifications": True,
                "desktop_notifications": True,
                "sound_notifications": False,
                "dark_theme": False,
                "whatsapp": {
                    "new_message": True,
                    "missed_message": True,
                    "auto_reply": False
                },
                "appointments": {
                    "new": True,
                    "reminder": True,
                    "cancelled": True
                },
                "system": {
                    "errors": True,
                    "updates": False,
                    "maintenance": True
                }
            }
            
            # Logs de atividade
            activity_logs = ProfileQueries.get_recent_activity(limit=20)
            
            return user_data, notification_settings, activity_logs
            
        except Exception as e:
            print(f"Erro ao carregar dados do perfil: {e}")
            return {}, {}, []
    
    # Callback para salvar alterações do perfil
    @app.callback(
        Output('save-profile-btn', 'children'),
        [
            Input('save-profile-btn', 'n_clicks')
        ],
        [
            State('user-full-name', 'value'),
            State('user-email', 'value'),
            State('user-phone', 'value'),
            State('user-role', 'value'),
            State('user-timezone', 'value'),
            State('user-language', 'value'),
            State('dark-theme-switch', 'checked'),
            State('email-notifications-switch', 'checked'),
            State('desktop-notifications-switch', 'checked'),
            State('sound-notifications-switch', 'checked')
        ],
        prevent_initial_call=True
    )
    def save_profile_changes(n_clicks, full_name, email, phone, role, timezone, language, 
                           dark_theme, email_notif, desktop_notif, sound_notif):
        """
        Salva alterações do perfil do usuário.
        """
        if not n_clicks:
            raise PreventUpdate
        
        try:
            # Simula salvamento dos dados
            profile_data = {
                "full_name": full_name,
                "email": email,
                "phone": phone,
                "role": role,
                "timezone": timezone,
                "language": language,
                "preferences": {
                    "dark_theme": dark_theme,
                    "email_notifications": email_notif,
                    "desktop_notifications": desktop_notif,
                    "sound_notifications": sound_notif
                }
            }
            
            # Aqui você salvaria os dados no banco de dados
            # success = ProfileQueries.update_user_profile(profile_data)
            
            # Simula sucesso
            success = True
            
            if success:
                return [
                    DashIconify(icon="tabler:check", width=16, height=16),
                    " Salvo!"
                ]
            else:
                return [
                    DashIconify(icon="tabler:x", width=16, height=16),
                    " Erro ao salvar"
                ]
                
        except Exception as e:
            print(f"Erro ao salvar perfil: {e}")
            return [
                DashIconify(icon="tabler:x", width=16, height=16),
                " Erro ao salvar"
            ]
    
    # Callback para alterar avatar
    @app.callback(
        Output('user-avatar', 'src'),
        Input('change-avatar-btn', 'n_clicks'),
        prevent_initial_call=True
    )
    def change_avatar(n_clicks):
        """
        Simula alteração do avatar do usuário.
        """
        if not n_clicks:
            raise PreventUpdate
        
        # Lista de avatares de exemplo
        avatars = [
            "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&h=150&fit=crop&crop=face",
            "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face",
            "https://images.unsplash.com/photo-1494790108755-2616c04e79e4?w=150&h=150&fit=crop&crop=face",
            "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face"
        ]
        
        # Alterna entre os avatares baseado no número de cliques
        return avatars[n_clicks % len(avatars)]
    
    # Callback para atualizar timeline de atividades
    @app.callback(
        Output('activity-timeline', 'children'),
        Input('activity-filter', 'value'),
        prevent_initial_call=True
    )
    def update_activity_timeline(filter_value):
        """
        Atualiza timeline de atividades baseado no filtro selecionado.
        """
        try:
            # Busca atividades baseado no filtro
            if filter_value == "today":
                activities = ProfileQueries.get_recent_activity(limit=10, period_hours=24)
            elif filter_value == "week":
                activities = ProfileQueries.get_recent_activity(limit=20, period_days=7)
            elif filter_value == "month":
                activities = ProfileQueries.get_recent_activity(limit=50, period_days=30)
            else:  # all
                activities = ProfileQueries.get_recent_activity(limit=100)
            
            if not activities:
                return create_empty_timeline()
            
            return create_activity_timeline_items(activities)
            
        except Exception as e:
            print(f"Erro ao atualizar timeline de atividades: {e}")
            return create_empty_timeline()
    
    # Callback para refresh dos dados
    @app.callback(
        [
            Output('user-profile-data', 'data', allow_duplicate=True),
            Output('activity-logs', 'data', allow_duplicate=True)
        ],
        Input('refresh-profile-btn', 'n_clicks'),
        prevent_initial_call=True
    )
    def refresh_profile_data(n_clicks):
        """
        Atualiza todos os dados da página de perfil.
        """
        if not n_clicks:
            raise PreventUpdate
        
        try:
            # Recarrega dados do usuário
            user_data = {
                "full_name": "Administrador do Sistema",
                "email": "admin@wppagent.com",
                "phone": "+55 11 99999-9999",
                "role": "Administrador",
                "timezone": "America/Sao_Paulo",
                "language": "pt-BR",
                "last_updated": datetime.now().isoformat()
            }
            
            # Recarrega logs de atividade
            activity_logs = ProfileQueries.get_recent_activity(limit=20)
            
            return user_data, activity_logs
            
        except Exception as e:
            print(f"Erro ao atualizar dados do perfil: {e}")
            return no_update, no_update
    
    # Callback para notificações
    @app.callback(
        Output('notification-settings', 'data', allow_duplicate=True),
        [
            Input('whatsapp-new-message', 'checked'),
            Input('whatsapp-missed-message', 'checked'),
            Input('whatsapp-auto-reply', 'checked'),
            Input('appointment-new', 'checked'),
            Input('appointment-reminder', 'checked'),
            Input('appointment-cancelled', 'checked'),
            Input('system-errors', 'checked'),
            Input('system-updates', 'checked'),
            Input('system-maintenance', 'checked')
        ],
        prevent_initial_call=True
    )
    def update_notification_settings(whatsapp_new, whatsapp_missed, whatsapp_auto,
                                   appointment_new, appointment_reminder, appointment_cancelled,
                                   system_errors, system_updates, system_maintenance):
        """
        Atualiza configurações de notificação.
        """
        settings = {
            "whatsapp": {
                "new_message": whatsapp_new,
                "missed_message": whatsapp_missed,
                "auto_reply": whatsapp_auto
            },
            "appointments": {
                "new": appointment_new,
                "reminder": appointment_reminder,
                "cancelled": appointment_cancelled
            },
            "system": {
                "errors": system_errors,
                "updates": system_updates,
                "maintenance": system_maintenance
            },
            "last_updated": datetime.now().isoformat()
        }
        
        # Salva configurações no banco de dados
        # ProfileQueries.update_notification_settings(settings)
        
        return settings

def create_activity_timeline_items(activities):
    """
    Cria itens da timeline de atividades.
    """
    timeline_items = []
    
    for activity in activities:
        # Mapeia tipos de atividade para ícones e cores
        icon_map = {
            "conversation": {"icon": "tabler:message", "color": "blue"},
            "appointment": {"icon": "tabler:calendar", "color": "green"},
            "login": {"icon": "tabler:login", "color": "orange"},
            "logout": {"icon": "tabler:logout", "color": "gray"},
            "system": {"icon": "tabler:settings", "color": "purple"},
            "backup": {"icon": "tabler:database", "color": "teal"},
            "error": {"icon": "tabler:alert-circle", "color": "red"}
        }
        
        activity_type = activity.get("type", "system")
        icon_info = icon_map.get(activity_type, icon_map["system"])
        
        # Formata timestamp
        timestamp = activity.get("timestamp", datetime.now())
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        time_str = timestamp.strftime("%H:%M")
        date_str = timestamp.strftime("%d/%m")
        
        timeline_items.append(
            dmc.Group([
                dmc.ThemeIcon(
                    DashIconify(icon=icon_info["icon"], width=16),
                    color=icon_info["color"],
                    variant="light",
                    size="lg"
                ),
                
                dmc.Stack([
                    dmc.Group([
                        dmc.Text(activity.get("description", "Atividade"), fw=600, size="sm"),
                        dmc.Text(f"{date_str} {time_str}", size="xs", c="dimmed")
                    ], position="space-between"),
                    dmc.Text(activity.get("details", ""), size="sm", c="dimmed") if activity.get("details") else None
                ], spacing="xs")
                
            ], spacing="md", align="flex-start", className="activity-item")
        )
    
    return dmc.Stack(timeline_items, spacing="lg")

def create_empty_timeline():
    """
    Cria estado vazio para timeline.
    """
    return dmc.Center([
        dmc.Stack([
            DashIconify(icon="tabler:calendar-x", width=48, height=48, color="gray"),
            dmc.Text("Nenhuma atividade encontrada", size="lg", c="dimmed"),
            dmc.Text("Tente ajustar o filtro de período", size="sm", c="dimmed")
        ], align="center", spacing="sm")
    ], style={"height": "200px"})

def create_notification_toast(title, message, color="blue"):
    """
    Cria notificação toast para feedback do usuário.
    """
    return dmc.Notification(
        title=title,
        message=message,
        color=color,
        icon=DashIconify(icon="tabler:check"),
        autoClose=3000
    )

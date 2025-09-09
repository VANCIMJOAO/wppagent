"""
import logging
logger = logging.getLogger(__name__)

Report Export Service - Sistema de Exportação de Relatórios
Gera relatórios em CSV, Excel e PDF para dashboard analytics
"""

import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import xlsxwriter
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List

from app.models.database import User, Message, Appointment, Business, Service, Conversation

class ReportExportService:
    """
    🏭 Fábrica de Relatórios - Sistema de Exportação Avançado
    
    Características:
    • CSV para agendamentos detalhados
    • Excel com múltiplas abas de analytics
    • PDF executivo profissional formatado
    • Streaming para downloads eficientes
    """
    
    def __init__(self, analytics_engine):
        self.analytics = analytics_engine
        self.session = analytics_engine.session
    
    async def export_appointments_csv(self, start_date: datetime, end_date: datetime) -> BytesIO:
        """
        📊 Exportar agendamentos detalhados para CSV
        
        Features:
        • Dados completos do cliente
        • Status e valores formatados
        • Ordenação cronológica
        • Encoding UTF-8 para acentos
        """
        logger.info(f"🔄 Exportando agendamentos CSV: {start_date} até {end_date}")
        
        try:
            # Query otimizada para agendamentos
            query = select(
                Appointment.id,
                Appointment.date_time,
                Appointment.status,
                Appointment.price,
                Appointment.notes,
                Appointment.created_at,
                User.nome.label('cliente_nome'),
                User.telefone.label('cliente_telefone'),
                User.email.label('cliente_email'),
                Service.name.label('servico_nome'),
                Business.name.label('business_name')
            ).select_from(
                Appointment
                .join(User, Appointment.user_id == User.id)
                .join(Business, Appointment.business_id == Business.id)
                .outerjoin(Service, Appointment.service_id == Service.id)
            ).where(
                and_(
                    Appointment.created_at >= start_date,
                    Appointment.created_at <= end_date
                )
            ).order_by(desc(Appointment.created_at))
            
            result = await self.session.execute(query)
            data = []
            
            for row in result:
                data.append({
                    'ID': row.id,
                    'Data/Hora Agendamento': row.date_time.strftime('%d/%m/%Y %H:%M') if row.date_time else 'N/A',
                    'Cliente': row.cliente_nome or 'N/A',
                    'Telefone': row.cliente_telefone or 'N/A',
                    'Email': row.cliente_email or 'N/A',
                    'Serviço': row.servico_nome or 'Consulta Geral',
                    'Status': self._format_status(row.status),
                    'Valor': f'R$ {float(row.price):.2f}' if row.price else 'R$ 0,00',
                    'Observações': row.notes or '',
                    'Empresa': row.business_name or 'N/A',
                    'Data Criação': row.created_at.strftime('%d/%m/%Y %H:%M')
                })
            
            # Converter para DataFrame e CSV
            df = pd.DataFrame(data)
            csv_buffer = BytesIO()
            
            # CSV com encoding UTF-8 e separador adequado para Excel BR
            csv_content = df.to_csv(index=False, encoding='utf-8-sig', sep=';')
            csv_buffer.write(csv_content.encode('utf-8-sig'))
            csv_buffer.seek(0)
            
            logger.info(f"✅ CSV gerado com {len(data)} agendamentos")
            return csv_buffer
            
        except Exception as e:
            logger.error(f"❌ Erro ao exportar CSV: {e}")
            raise
    
    async def export_analytics_excel(self, period_days: int = 30) -> BytesIO:
        """
        📈 Exportar analytics completas para Excel com múltiplas abas
        
        Abas:
        • Funil de Conversão
        • Clientes VIP
        • Análise Temporal
        • Resumo Executivo
        """
        logger.info(f"🔄 Exportando analytics Excel: {period_days} dias")
        
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)
            
            # Buscar dados do analytics engine
            funnel_data = await self.analytics.get_conversion_funnel(start_date, end_date)
            time_data = await self.analytics.get_time_based_analytics(period_days)
            customer_data = await self.analytics.get_customer_insights(period_days)
            business_data = await self.analytics.get_business_metrics(period_days)
            
            # Criar arquivo Excel
            excel_buffer = BytesIO()
            workbook = xlsxwriter.Workbook(excel_buffer)
            
            # Definir formatos
            header_format = workbook.add_format({
                'bold': True,
                'font_color': 'white',
                'bg_color': '#366092',
                'align': 'center',
                'border': 1
            })
            
            number_format = workbook.add_format({
                'num_format': '#,##0',
                'align': 'center',
                'border': 1
            })
            
            percent_format = workbook.add_format({
                'num_format': '0.0%',
                'align': 'center',
                'border': 1
            })
            
            currency_format = workbook.add_format({
                'num_format': 'R$ #,##0.00',
                'align': 'center',
                'border': 1
            })
            
            date_format = workbook.add_format({
                'num_format': 'dd/mm/yyyy',
                'align': 'center',
                'border': 1
            })
            
            # ABA 1: Resumo Executivo
            summary_sheet = workbook.add_worksheet('Resumo Executivo')
            summary_sheet.set_column('A:B', 25)
            
            summary_sheet.write('A1', 'RESUMO EXECUTIVO', header_format)
            summary_sheet.write('A2', 'Período de Análise', header_format)
            summary_sheet.write('B2', f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}")
            
            row = 4
            summary_sheet.write(f'A{row}', 'Métrica', header_format)
            summary_sheet.write(f'B{row}', 'Valor', header_format)
            
            summary_metrics = [
                ('Taxa Conversão Geral', f"{funnel_data['conversion_rates']['overall_conversion']:.1f}%"),
                ('Total Primeiros Contatos', funnel_data['funnel_stages']['first_contact']),
                ('Total Agendamentos', funnel_data['funnel_stages']['scheduled']),
                ('Agendamentos Realizados', funnel_data['funnel_stages']['completed']),
                ('Receita Total', f"R$ {business_data['revenue']['current_period']:.2f}"),
                ('Ticket Médio', f"R$ {business_data['revenue']['avg_ticket']:.2f}"),
                ('Clientes VIP', customer_data['customer_summary']['total_vip'])
            ]
            
            for metric, value in summary_metrics:
                row += 1
                summary_sheet.write(f'A{row}', metric)
                if isinstance(value, (int, float)) and 'R$' not in str(value):
                    summary_sheet.write(f'B{row}', value, number_format)
                else:
                    summary_sheet.write(f'B{row}', value)
            
            # ABA 2: Funil de Conversão
            funnel_sheet = workbook.add_worksheet('Funil de Conversão')
            funnel_sheet.set_column('A:C', 20)
            
            funnel_headers = ['Etapa do Funil', 'Quantidade', 'Taxa Conversão']
            for col, header in enumerate(funnel_headers):
                funnel_sheet.write(0, col, header, header_format)
            
            funnel_rows = [
                ('Primeiro Contato', funnel_data['funnel_stages']['first_contact'], '-'),
                ('Resposta Bot', funnel_data['funnel_stages']['bot_response'], '-'),
                ('Agendado', funnel_data['funnel_stages']['scheduled'], 
                 funnel_data['conversion_rates']['contact_to_schedule'] / 100),
                ('Confirmado', funnel_data['funnel_stages']['confirmed'],
                 funnel_data['conversion_rates']['schedule_to_confirm'] / 100),
                ('Realizado', funnel_data['funnel_stages']['completed'],
                 funnel_data['conversion_rates']['confirm_to_complete'] / 100)
            ]
            
            for row, (stage, count, rate) in enumerate(funnel_rows, 1):
                funnel_sheet.write(row, 0, stage)
                funnel_sheet.write(row, 1, count, number_format)
                if rate != '-':
                    funnel_sheet.write(row, 2, rate, percent_format)
                else:
                    funnel_sheet.write(row, 2, rate)
            
            # ABA 3: Clientes VIP
            vip_sheet = workbook.add_worksheet('Clientes VIP')
            vip_sheet.set_column('A:D', 20)
            
            vip_headers = ['Nome', 'Telefone', 'Total Agendamentos', 'Valor Total']
            for col, header in enumerate(vip_headers):
                vip_sheet.write(0, col, header, header_format)
            
            for row, customer in enumerate(customer_data['vip_customers'], 1):
                vip_sheet.write(row, 0, customer['name'])
                vip_sheet.write(row, 1, customer['phone'])
                vip_sheet.write(row, 2, customer['appointments'], number_format)
                vip_sheet.write(row, 3, customer['total_spent'], currency_format)
            
            # ABA 4: Análise Temporal
            time_sheet = workbook.add_worksheet('Análise Temporal')
            time_sheet.set_column('A:C', 15)
            
            time_headers = ['Hora do Dia', 'Total Mensagens', 'Usuários Únicos']
            for col, header in enumerate(time_headers):
                time_sheet.write(0, col, header, header_format)
            
            for row, hour_data in enumerate(time_data['hourly_patterns'], 1):
                time_sheet.write(row, 0, f"{hour_data['hour']:02d}:00")
                time_sheet.write(row, 1, hour_data['messages'], number_format)
                time_sheet.write(row, 2, hour_data['unique_users'], number_format)
            
            workbook.close()
            excel_buffer.seek(0)
            
            logger.info(f"✅ Excel gerado com 4 abas de analytics")
            return excel_buffer
            
        except Exception as e:
            logger.error(f"❌ Erro ao exportar Excel: {e}")
            raise
    
    async def export_executive_pdf(self, period_days: int = 30) -> BytesIO:
        """
        📑 Gerar relatório executivo profissional em PDF
        
        Features:
        • Layout profissional
        • Tabelas formatadas
        • Métricas principais
        • Funil de conversão detalhado
        """
        logger.info(f"🔄 Exportando relatório executivo PDF: {period_days} dias")
        
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)
            
            # Buscar dados
            funnel_data = await self.analytics.get_conversion_funnel(start_date, end_date)
            customer_data = await self.analytics.get_customer_insights(period_days)
            business_data = await self.analytics.get_business_metrics(period_days)
            
            # Criar PDF
            pdf_buffer = BytesIO()
            doc = SimpleDocTemplate(
                pdf_buffer, 
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            styles = getSampleStyleSheet()
            story = []
            
            # Título Principal
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                textColor=colors.darkblue,
                alignment=1  # Centro
            )
            story.append(Paragraph("RELATÓRIO EXECUTIVO", title_style))
            story.append(Paragraph("WhatsApp Agent - Business Intelligence", styles['Heading2']))
            story.append(Spacer(1, 20))
            
            # Período
            period_text = f"<b>Período de Análise:</b> {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
            story.append(Paragraph(period_text, styles['Normal']))
            story.append(Paragraph(f"<b>Data do Relatório:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
            story.append(Spacer(1, 30))
            
            # Resumo Executivo
            story.append(Paragraph("RESUMO EXECUTIVO", styles['Heading2']))
            story.append(Spacer(1, 10))
            
            summary_data = [
                ['MÉTRICA', 'VALOR'],
                ['Taxa de Conversão Geral', f"{funnel_data['conversion_rates']['overall_conversion']:.1f}%"],
                ['Total de Primeiros Contatos', f"{funnel_data['funnel_stages']['first_contact']:,}"],
                ['Agendamentos Realizados', f"{funnel_data['funnel_stages']['completed']:,}"],
                ['Receita Total do Período', f"R$ {business_data['revenue']['current_period']:,.2f}"],
                ['Ticket Médio', f"R$ {business_data['revenue']['avg_ticket']:,.2f}"],
                ['Clientes VIP Ativos', f"{customer_data['customer_summary']['total_vip']:,}"],
                ['Taxa de Confirmação', f"{funnel_data['conversion_rates']['schedule_to_confirm']:.1f}%"]
            ]
            
            summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 30))
            
            # Funil de Conversão Detalhado
            story.append(Paragraph("ANÁLISE DO FUNIL DE CONVERSÃO", styles['Heading2']))
            story.append(Spacer(1, 10))
            
            funnel_table_data = [
                ['ETAPA DO PROCESSO', 'QUANTIDADE', 'TAXA CONVERSÃO', 'PERDA'],
                ['Primeiro Contato', f"{funnel_data['funnel_stages']['first_contact']:,}", '-', '-'],
                ['Resposta do Bot', f"{funnel_data['funnel_stages']['bot_response']:,}", '-', '-'],
                ['Agendamentos Criados', f"{funnel_data['funnel_stages']['scheduled']:,}", 
                 f"{funnel_data['conversion_rates']['contact_to_schedule']:.1f}%",
                 f"{funnel_data['funnel_stages']['first_contact'] - funnel_data['funnel_stages']['scheduled']:,}"],
                ['Agendamentos Confirmados', f"{funnel_data['funnel_stages']['confirmed']:,}",
                 f"{funnel_data['conversion_rates']['schedule_to_confirm']:.1f}%",
                 f"{funnel_data['funnel_stages']['scheduled'] - funnel_data['funnel_stages']['confirmed']:,}"],
                ['Agendamentos Realizados', f"{funnel_data['funnel_stages']['completed']:,}",
                 f"{funnel_data['conversion_rates']['confirm_to_complete']:.1f}%",
                 f"{funnel_data['funnel_stages']['confirmed'] - funnel_data['funnel_stages']['completed']:,}"]
            ]
            
            funnel_table = Table(funnel_table_data, colWidths=[2.2*inch, 1.2*inch, 1.2*inch, 1*inch])
            funnel_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            
            story.append(funnel_table)
            story.append(Spacer(1, 20))
            
            # Top Clientes VIP
            if customer_data['vip_customers']:
                story.append(Paragraph("TOP 5 CLIENTES VIP", styles['Heading2']))
                story.append(Spacer(1, 10))
                
                vip_table_data = [['CLIENTE', 'TELEFONE', 'AGENDAMENTOS', 'VALOR TOTAL']]
                
                for customer in customer_data['vip_customers'][:5]:
                    vip_table_data.append([
                        customer['name'][:20],
                        customer['phone'],
                        f"{customer['appointments']:,}",
                        f"R$ {customer['total_spent']:,.2f}"
                    ])
                
                vip_table = Table(vip_table_data, colWidths=[2*inch, 1.5*inch, 1*inch, 1.5*inch])
                vip_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                ]))
                
                story.append(vip_table)
            
            # Gerar PDF
            doc.build(story)
            pdf_buffer.seek(0)
            
            logger.info("✅ PDF executivo gerado com sucesso")
            return pdf_buffer
            
        except Exception as e:
            logger.error(f"❌ Erro ao exportar PDF: {e}")
            raise
    
    def _format_status(self, status: str) -> str:
        """Formatar status para exibição"""
        status_map = {
            'pendente': 'Pendente',
            'confirmado': 'Confirmado',
            'realizado': 'Realizado',
            'cancelado': 'Cancelado',
            'remarcado': 'Remarcado'
        }
        return status_map.get(status, status.title())

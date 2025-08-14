#!/usr/bin/env python3
"""
Popular banco Railway com dados de teste completos
Empresa, serviços, valores, endereços, etc.
"""

import asyncio
import asyncpg
import os
from decimal import Decimal

# Configuração do banco
DATABASE_URL = 'postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway'

async def populate_test_data():
    """Popular banco com dados completos de teste"""
    print("🚀 POPULANDO BANCO COM DADOS DE TESTE")
    print("=" * 60)
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Conectado ao banco Railway!")
        
        # ========================================
        # 1. BUSINESS (Negócio) - CRIAR PRIMEIRO
        # ========================================
        print("\n🏪 Inserindo dados do negócio...")
        
        await conn.execute("DELETE FROM businesses")
        
        await conn.execute('''
            INSERT INTO businesses (
                name, description, address, phone, email, business_hours,
                created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6::json, now(), now()
            )
        ''', 
        'Studio Beleza & Bem-Estar',
        'Estúdio completo de beleza e estética especializado em tratamentos faciais, massagens, depilação e cuidados corporais.',
        'Rua das Flores, 123 - Centro, São Paulo - SP, CEP: 01234-567',
        '(11) 99999-8888',
        'contato@studiobeleza.com.br',
        '{"seg_sex": "09:00-18:00", "sab": "09:00-15:00", "dom": "fechado", "almoco": "12:00-13:00"}'
        )
        
        print("✅ Dados do negócio inseridos!")
        
        # ========================================
        # 2. INFORMAÇÕES DA EMPRESA
        # ========================================
        print("\n🏢 Inserindo informações da empresa...")
        
        # Limpar dados existentes
        await conn.execute("DELETE FROM company_info")
        
        company_data = {
            'business_id': 1,
            'company_name': 'Studio Beleza & Bem-Estar',
            'slogan': 'Sua beleza é nossa paixão',
            'about_us': 'Há mais de 10 anos cuidando da sua beleza e bem-estar com carinho e profissionalismo. Nossa equipe especializada oferece os melhores tratamentos em um ambiente aconchegante e seguro.',
            'whatsapp_number': '5511999998888',
            'phone_secondary': '(11) 3333-4444',
            'email_contact': 'contato@studiobeleza.com.br',
            'website': 'https://studiobeleza.com.br',
            'street_address': 'Rua das Flores, 123 - Centro',
            'city': 'São Paulo',
            'state': 'SP',
            'zip_code': '01234-567',
            'country': 'Brasil',
            'instagram': '@studiobelezasp',
            'facebook': 'StudioBelezaSP',
            'linkedin': 'studio-beleza-sp',
            'welcome_message': 'Olá! 😊 Bem-vindo(a) ao Studio Beleza & Bem-Estar! Como posso ajudá-lo(a) hoje? Oferecemos diversos tratamentos de beleza e estética. Digite "menu" para ver nossos serviços ou "agendar" para marcar seu horário.',
            'auto_response_enabled': True,
            'business_description': 'Estúdio especializado em tratamentos estéticos, massagens relaxantes e cuidados com a beleza. Oferecemos serviços personalizados em um ambiente aconchegante com profissionais experientes e certificados.'
        }
        
        await conn.execute('''
            INSERT INTO company_info (
                business_id, company_name, slogan, about_us, whatsapp_number, 
                phone_secondary, email_contact, website, street_address, city, 
                state, zip_code, country, instagram, facebook, linkedin,
                welcome_message, auto_response_enabled, business_description,
                created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, now(), now()
            )
        ''', *company_data.values())
        
        print("✅ Informações da empresa inseridas!")
        
        # ========================================
        # 3. SERVIÇOS COMPLETOS
        # ========================================
        print("\n💅 Inserindo serviços...")
        
        await conn.execute("DELETE FROM services")
        
        services_data = [
            # Tratamentos Faciais
            ('Limpeza de Pele Profunda', 'Limpeza completa com extração, tonificação e hidratação. Inclui esfoliação e máscara personalizada.', 90, 'R$ 80,00', 1, True),
            
            ('Hidrofacial Diamante', 'Tratamento premium com tecnologia de ponta. Limpeza, esfoliação e hidratação profunda com resultados imediatos.', 60, 'R$ 150,00', 1, True),
            
            ('Peeling Químico', 'Renovação celular com ácidos específicos. Remove manchas e melhora textura da pele.', 45, 'R$ 120,00', 1, True),
            
            # Massagens
            ('Massagem Relaxante', 'Massagem corporal completa com óleos aromáticos. Alívio do estresse e tensões musculares.', 60, 'R$ 100,00', 1, True),
            
            ('Massagem Modeladora', 'Técnica específica para redução de medidas e celulite. Estimula circulação e drenagem linfática.', 75, 'R$ 120,00', 1, True),
            
            ('Drenagem Linfática', 'Massagem terapêutica para eliminação de toxinas e retenção de líquidos. Indicada pós-cirúrgica.', 60, 'R$ 90,00', 1, True),
            
            # Estética Corporal
            ('Criolipólise', 'Tratamento não invasivo para redução de gordura localizada através do frio controlado.', 60, 'R$ 300,00', 1, True),
            
            ('Radiofrequência', 'Estimula produção de colágeno, promove firmeza e reduz flacidez corporal e facial.', 45, 'R$ 180,00', 1, True),
            
            # Depilação
            ('Depilação Pernas Completas', 'Depilação a cera quente nas pernas completas. Inclui hidratação pós-depilação.', 45, 'R$ 60,00', 1, True),
            
            ('Depilação Virilha Completa', 'Depilação íntima completa com cera especializada. Técnica cuidadosa e higiênica.', 30, 'R$ 45,00', 1, True),
            
            # Unhas
            ('Manicure Completa', 'Cuidado completo das unhas das mãos com esmaltação. Inclui hidratação e massagem.', 45, 'R$ 35,00', 1, True),
            
            ('Pedicure Spa', 'Tratamento luxuoso para os pés com esfoliação, hidratação e esmaltação.', 60, 'R$ 45,00', 1, True),
            
            # Cabelo
            ('Corte Feminino', 'Corte personalizado de acordo com formato do rosto e estilo desejado. Inclui lavagem.', 60, 'R$ 80,00', 1, True),
            
            ('Escova Progressiva', 'Alisamento e redução de volume. Deixa cabelos lisos e sedosos por até 4 meses.', 180, 'R$ 250,00', 1, True),
            
            # Pacotes Promocionais
            ('Pacote Noiva', 'Preparação completa para o grande dia: facial, corporal, unhas e cabelo.', 240, 'R$ 450,00', 1, True),
            
            ('Day Spa Relax', 'Dia inteiro de relaxamento: massagem, facial, unhas e lanche saudável.', 300, 'R$ 280,00', 1, True)
        ]
        
        for service in services_data:
            await conn.execute('''
                INSERT INTO services (
                    name, description, duration_minutes, price, business_id, is_active,
                    created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, now(), now()
                )
            ''', *service)
        
        print(f"✅ {len(services_data)} serviços inseridos!")
        
        # ========================================
        # 4. ATUALIZAR HORÁRIOS DE FUNCIONAMENTO
        # ========================================
        print("\n🕐 Atualizando horários de funcionamento...")
        
        # Limpar e recriar horários mais detalhados
        await conn.execute("DELETE FROM business_hours")
        
        # Usar SQL direto para inserção com tipos TIME
        await conn.execute('''
            INSERT INTO business_hours (business_id, day_of_week, is_open, open_time, close_time, break_start_time, break_end_time, notes, created_at, updated_at) VALUES
            (1, 0, false, NULL, NULL, NULL, NULL, 'Fechado aos domingos', now(), now()),
            (1, 1, true, '09:00:00'::time, '18:00:00'::time, '12:00:00'::time, '13:00:00'::time, 'Segunda-feira - Almoço 12h às 13h', now(), now()),
            (1, 2, true, '09:00:00'::time, '18:00:00'::time, '12:00:00'::time, '13:00:00'::time, 'Terça-feira - Almoço 12h às 13h', now(), now()),
            (1, 3, true, '09:00:00'::time, '18:00:00'::time, '12:00:00'::time, '13:00:00'::time, 'Quarta-feira - Almoço 12h às 13h', now(), now()),
            (1, 4, true, '09:00:00'::time, '18:00:00'::time, '12:00:00'::time, '13:00:00'::time, 'Quinta-feira - Almoço 12h às 13h', now(), now()),
            (1, 5, true, '09:00:00'::time, '18:00:00'::time, '12:00:00'::time, '13:00:00'::time, 'Sexta-feira - Almoço 12h às 13h', now(), now()),
            (1, 6, true, '09:00:00'::time, '15:00:00'::time, NULL, NULL, 'Sábado - Expediente reduzido', now(), now())
        ''')
        
        print("✅ Horários de funcionamento atualizados!")
        
        # ========================================
        # 5. VERIFICAÇÃO FINAL
        # ========================================
        print("\n📊 VERIFICAÇÃO FINAL:")
        print("=" * 40)
        
        # Contar dados inseridos
        company_count = await conn.fetchval("SELECT COUNT(*) FROM company_info")
        business_count = await conn.fetchval("SELECT COUNT(*) FROM businesses") 
        services_count = await conn.fetchval("SELECT COUNT(*) FROM services")
        hours_count = await conn.fetchval("SELECT COUNT(*) FROM business_hours")
        payment_count = await conn.fetchval("SELECT COUNT(*) FROM payment_methods")
        policies_count = await conn.fetchval("SELECT COUNT(*) FROM business_policies")
        
        print(f"🏢 Informações da empresa: {company_count}")
        print(f"🏪 Negócios: {business_count}")
        print(f"💅 Serviços: {services_count}")
        print(f"🕐 Horários: {hours_count}")
        print(f"💳 Formas de pagamento: {payment_count}")
        print(f"📋 Políticas: {policies_count}")
        
        # Mostrar alguns serviços
        print(f"\n🛠️ SERVIÇOS CADASTRADOS:")
        services = await conn.fetch("SELECT name, price, duration FROM services ORDER BY price LIMIT 5")
        for service in services:
            print(f"  • {service['name']}: R$ {service['price']} ({service['duration']}min)")
        
        await conn.close()
        
        print(f"\n🎉 SUCESSO TOTAL!")
        print(f"✅ Banco populado com dados completos de teste")
        print(f"✅ Studio Beleza & Bem-Estar pronto para uso")
        print(f"✅ {services_count} serviços disponíveis")
        print(f"✅ Horários, políticas e pagamentos configurados")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao popular banco: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(populate_test_data())
    exit(0 if result else 1)

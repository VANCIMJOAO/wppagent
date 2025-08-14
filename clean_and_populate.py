#!/usr/bin/env python3
"""
Limpar e popular banco Railway com dados de teste completos
"""

import asyncio
import asyncpg

DATABASE_URL = 'postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway'

async def clean_and_populate():
    """Limpar e popular banco com dados completos"""
    print("🧹 LIMPANDO E POPULANDO BANCO")
    print("=" * 50)
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Conectado ao banco Railway!")
        
        # ========================================
        # 1. LIMPAR DADOS EXISTENTES (em ordem de dependências)
        # ========================================
        print("\n🧹 Limpando dados existentes...")
        
        await conn.execute("DELETE FROM company_info")
        await conn.execute("DELETE FROM services") 
        await conn.execute("DELETE FROM businesses")
        
        print("✅ Dados limpos!")
        
        # ========================================
        # 2. CRIAR BUSINESS E OBTER ID
        # ========================================
        print("\n🏪 Criando negócio...")
        
        business_id = await conn.fetchval('''
            INSERT INTO businesses (
                name, description, address, phone, email, business_hours,
                created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6::json, now(), now()
            ) RETURNING id
        ''', 
        'Studio Beleza & Bem-Estar',
        'Estúdio completo de beleza e estética especializado em tratamentos faciais, massagens, depilação e cuidados corporais.',
        'Rua das Flores, 123 - Centro, São Paulo - SP, CEP: 01234-567',
        '(11) 99999-8888',
        'contato@studiobeleza.com.br',
        '{"seg_sex": "09:00-18:00", "sab": "09:00-15:00", "dom": "fechado", "almoco": "12:00-13:00"}'
        )
        
        print(f"✅ Negócio criado com ID: {business_id}")
        
        # ========================================
        # 3. INFORMAÇÕES DA EMPRESA
        # ========================================
        print("\n🏢 Criando informações da empresa...")
        
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
        ''',
        business_id,  # Usar o ID real retornado
        'Studio Beleza & Bem-Estar',
        'Sua beleza é nossa paixão',
        'Há mais de 10 anos cuidando da sua beleza e bem-estar com carinho e profissionalismo. Nossa equipe especializada oferece os melhores tratamentos em um ambiente aconchegante e seguro.',
        '5511999998888',
        '(11) 3333-4444',
        'contato@studiobeleza.com.br',
        'https://studiobeleza.com.br',
        'Rua das Flores, 123 - Centro',
        'São Paulo',
        'SP',
        '01234-567',
        'Brasil',
        '@studiobelezasp',
        'StudioBelezaSP',
        'studio-beleza-sp',
        'Olá! 😊 Bem-vindo(a) ao Studio Beleza & Bem-Estar! Como posso ajudá-lo(a) hoje? Oferecemos diversos tratamentos de beleza e estética. Digite "menu" para ver nossos serviços ou "agendar" para marcar seu horário.',
        True,
        'Estúdio especializado em tratamentos estéticos, massagens relaxantes e cuidados com a beleza. Oferecemos serviços personalizados em um ambiente aconchegante com profissionais experientes e certificados.'
        )
        
        print("✅ Informações da empresa criadas!")
        
        # ========================================
        # 4. SERVIÇOS
        # ========================================
        print("\n💅 Criando serviços...")
        
        services_data = [
            # Tratamentos Faciais
            ('Limpeza de Pele Profunda', 'Limpeza completa com extração, tonificação e hidratação. Inclui esfoliação e máscara personalizada.', 90, 'R$ 80,00'),
            ('Hidrofacial Diamante', 'Tratamento premium com tecnologia de ponta. Limpeza, esfoliação e hidratação profunda.', 60, 'R$ 150,00'),
            ('Peeling Químico', 'Renovação celular com ácidos específicos. Remove manchas e melhora textura da pele.', 45, 'R$ 120,00'),
            
            # Massagens
            ('Massagem Relaxante', 'Massagem corporal completa com óleos aromáticos. Alívio do estresse e tensões.', 60, 'R$ 100,00'),
            ('Massagem Modeladora', 'Técnica específica para redução de medidas e celulite. Estimula circulação.', 75, 'R$ 120,00'),
            ('Drenagem Linfática', 'Massagem terapêutica para eliminação de toxinas e retenção de líquidos.', 60, 'R$ 90,00'),
            
            # Estética Corporal
            ('Criolipólise', 'Tratamento não invasivo para redução de gordura localizada através do frio controlado.', 60, 'R$ 300,00'),
            ('Radiofrequência', 'Estimula produção de colágeno, promove firmeza e reduz flacidez.', 45, 'R$ 180,00'),
            
            # Depilação
            ('Depilação Pernas Completas', 'Depilação a cera quente nas pernas completas. Inclui hidratação.', 45, 'R$ 60,00'),
            ('Depilação Virilha Completa', 'Depilação íntima completa com cera especializada.', 30, 'R$ 45,00'),
            
            # Unhas
            ('Manicure Completa', 'Cuidado completo das unhas das mãos com esmaltação.', 45, 'R$ 35,00'),
            ('Pedicure Spa', 'Tratamento luxuoso para os pés com esfoliação e hidratação.', 60, 'R$ 45,00'),
            
            # Cabelo
            ('Corte Feminino', 'Corte personalizado de acordo com formato do rosto.', 60, 'R$ 80,00'),
            ('Escova Progressiva', 'Alisamento e redução de volume. Dura até 4 meses.', 180, 'R$ 250,00'),
            
            # Pacotes
            ('Pacote Noiva', 'Preparação completa: facial, corporal, unhas e cabelo.', 240, 'R$ 450,00'),
            ('Day Spa Relax', 'Dia inteiro de relaxamento: massagem, facial e unhas.', 300, 'R$ 280,00')
        ]
        
        for name, description, duration_minutes, price in services_data:
            await conn.execute('''
                INSERT INTO services (
                    name, description, duration_minutes, price, business_id, is_active,
                    created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, true, now(), now()
                )
            ''', name, description, duration_minutes, price, business_id)
        
        print(f"✅ {len(services_data)} serviços criados!")
        
        # ========================================
        # 5. VERIFICAÇÃO FINAL
        # ========================================
        print("\n📊 VERIFICAÇÃO FINAL:")
        print("=" * 40)
        
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
        print(f"\n🛠️ SERVIÇOS POPULARES:")
        services = await conn.fetch("SELECT name, price, duration_minutes FROM services ORDER BY name LIMIT 8")
        for service in services:
            print(f"  • {service['name']}: {service['price']} ({service['duration_minutes']}min)")
        
        # Mostrar informações da empresa
        company = await conn.fetchrow("SELECT company_name, slogan, city FROM company_info LIMIT 1")
        if company:
            print(f"\n🏢 EMPRESA: {company['company_name']}")
            print(f"   Slogan: {company['slogan']}")
            print(f"   Local: {company['city']}")
        
        await conn.close()
        
        print(f"\n🎉 SUCESSO TOTAL!")
        print(f"✅ Banco populado com dados completos")
        print(f"✅ Studio Beleza & Bem-Estar configurado")
        print(f"✅ {services_count} serviços disponíveis")
        print(f"✅ Pronto para testes e uso em produção!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(clean_and_populate())
    exit(0 if result else 1)

import { NextRequest, NextResponse } from 'next/server';
import { executeQuery } from '@/lib/database';
import { debugLog } from '@/lib/debug';

export async function GET(request: NextRequest) {
  try {
    debugLog.info('⏰ Buscando configurações de horários...');

    const scheduleQuery = `
      SELECT
        id,
        business_id,
        day_of_week,
        is_open,
        open_time,
        close_time,
        break_start_time,
        break_end_time,
        notes,
        created_at,
        updated_at
      FROM business_hours
      ORDER BY day_of_week
    `;

    const schedules = await executeQuery(scheduleQuery);

    // Mapear dias da semana
    const dayMapping = {
      0: 'sunday',
      1: 'monday',
      2: 'tuesday',
      3: 'wednesday',
      4: 'thursday',
      5: 'friday',
      6: 'saturday'
    };

    // Inicializar configuração padrão
    const defaultSchedule = {
      workDays: [],
      startTime: '09:00',
      endTime: '18:00',
      lunchStart: '12:00',
      lunchEnd: '13:00',
      timezone: 'America/Sao_Paulo',
      business_hours: []
    };

    if (schedules.length === 0) {
      // Retornar configuração padrão
      return NextResponse.json({
        success: true,
        data: {
          ...defaultSchedule,
          workDays: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        }
      });
    }

    // Processar horários do banco
    const workDays: string[] = [];
    let startTime = '09:00';
    let endTime = '18:00';
    let lunchStart = '12:00';
    let lunchEnd = '13:00';

    schedules.forEach(schedule => {
      const dayName = dayMapping[schedule.day_of_week as keyof typeof dayMapping];
      
      if (schedule.is_open && dayName) {
        workDays.push(dayName);
        
        // Usar horários do primeiro dia de trabalho encontrado
        if (schedule.open_time) {
          startTime = schedule.open_time.substring(0, 5); // HH:MM
        }
        if (schedule.close_time) {
          endTime = schedule.close_time.substring(0, 5); // HH:MM
        }
        if (schedule.break_start_time) {
          lunchStart = schedule.break_start_time.substring(0, 5); // HH:MM
        }
        if (schedule.break_end_time) {
          lunchEnd = schedule.break_end_time.substring(0, 5); // HH:MM
        }
      }
    });

    const formattedSchedule = {
      workDays: workDays.length > 0 ? workDays : ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
      startTime,
      endTime,
      lunchStart,
      lunchEnd,
      timezone: 'America/Sao_Paulo',
      business_hours: schedules
    };

    debugLog.info(`✅ Configurações de horários carregadas: ${workDays.length} dias de trabalho`);

    return NextResponse.json({
      success: true,
      data: formattedSchedule
    });

  } catch (error) {
    debugLog.error('Erro ao buscar configurações de horários:', error);
    return NextResponse.json(
      {
        success: false,
        error: 'Erro interno do servidor',
        details: error instanceof Error ? error.message : 'Erro desconhecido'
      },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    debugLog.info('💾 Salvando configurações de horários...');

    const body = await request.json();
    const { workDays, startTime, endTime, lunchStart, lunchEnd, timezone } = body;

    if (!workDays || !Array.isArray(workDays)) {
      return NextResponse.json(
        {
          success: false,
          error: 'Dias de trabalho são obrigatórios'
        },
        { status: 400 }
      );
    }

    // Mapear dias da semana para números
    const dayMapping: { [key: string]: number } = {
      'sunday': 0,
      'monday': 1,
      'tuesday': 2,
      'wednesday': 3,
      'thursday': 4,
      'friday': 5,
      'saturday': 6
    };

    // Limpar horários existentes
    await executeQuery('DELETE FROM business_hours WHERE business_id = 1');

    // Inserir novos horários
    const insertPromises = [];
    
    for (let dayNum = 0; dayNum < 7; dayNum++) {
      const dayName = Object.keys(dayMapping).find(key => dayMapping[key] === dayNum);
      const isOpen = workDays.includes(dayName || '');
      
      const insertQuery = `
        INSERT INTO business_hours (
          business_id, day_of_week, is_open, open_time, close_time,
          break_start_time, break_end_time, notes, created_at, updated_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
      `;
      
      insertPromises.push(
        executeQuery(insertQuery, [
          1, // business_id
          dayNum,
          isOpen,
          isOpen ? startTime : null,
          isOpen ? endTime : null,
          isOpen ? lunchStart : null,
          isOpen ? lunchEnd : null,
          isOpen ? `Horário de funcionamento: ${startTime} - ${endTime}` : 'Fechado'
        ])
      );
    }

    await Promise.all(insertPromises);

    // Buscar horários salvos para retornar
    const savedSchedules = await executeQuery(`
      SELECT * FROM business_hours 
      WHERE business_id = 1 
      ORDER BY day_of_week
    `);

    debugLog.info(`✅ Configurações de horários salvas: ${workDays.length} dias de trabalho`);

    return NextResponse.json({
      success: true,
      data: {
        workDays,
        startTime,
        endTime,
        lunchStart,
        lunchEnd,
        timezone: timezone || 'America/Sao_Paulo',
        business_hours: savedSchedules
      },
      message: 'Configurações de horários salvas com sucesso'
    });

  } catch (error) {
    debugLog.error('Erro ao salvar configurações de horários:', error);
    return NextResponse.json(
      {
        success: false,
        error: 'Erro interno do servidor',
        details: error instanceof Error ? error.message : 'Erro desconhecido'
      },
      { status: 500 }
    );
  }
}

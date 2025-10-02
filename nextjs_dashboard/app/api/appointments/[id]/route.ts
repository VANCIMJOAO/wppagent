import { NextRequest, NextResponse } from 'next/server';
import { executeQuery } from '@/lib/database';

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const resolvedParams = await params;
    const appointmentId = resolvedParams.id;
    const body = await request.json();
    const { 
      user_id, 
      business_id, 
      service_id, 
      data_agendamento, 
      duracao_minutos, 
      valor, 
      observacoes, 
      status 
    } = body;

    console.log(`📅 Atualizando agendamento ${appointmentId}...`);

    // Verificar se o agendamento existe
    const checkQuery = 'SELECT id FROM appointments WHERE id = $1';
    const existingAppointment = await executeQuery(checkQuery, [appointmentId]);

    if (!existingAppointment || existingAppointment.length === 0) {
      return NextResponse.json(
        { success: false, error: 'Agendamento não encontrado' },
        { status: 404 }
      );
    }

    // Construir query de atualização dinamicamente
    const updateFields = [];
    const updateValues = [];
    let paramIndex = 1;

    if (user_id !== undefined) {
      updateFields.push(`user_id = $${paramIndex}`);
      updateValues.push(user_id);
      paramIndex++;
    }

    if (business_id !== undefined) {
      updateFields.push(`business_id = $${paramIndex}`);
      updateValues.push(business_id);
      paramIndex++;
    }

    if (service_id !== undefined) {
      updateFields.push(`service_id = $${paramIndex}`);
      updateValues.push(service_id);
      paramIndex++;
    }

    if (data_agendamento !== undefined) {
      updateFields.push(`date_time = $${paramIndex}`);
      updateValues.push(data_agendamento);
      paramIndex++;
    }

    if (duracao_minutos !== undefined) {
      updateFields.push(`duration_minutes = $${paramIndex}`);
      updateValues.push(duracao_minutos);
      paramIndex++;
    }

    if (valor !== undefined) {
      updateFields.push(`price = $${paramIndex}`);
      updateValues.push(valor);
      paramIndex++;
    }

    if (observacoes !== undefined) {
      updateFields.push(`notes = $${paramIndex}`);
      updateValues.push(observacoes);
      paramIndex++;
    }

    if (status !== undefined) {
      updateFields.push(`status = $${paramIndex}`);
      updateValues.push(status);
      paramIndex++;
    }

    if (updateFields.length === 0) {
      return NextResponse.json(
        { success: false, error: 'Nenhum campo para atualizar' },
        { status: 400 }
      );
    }

    // Adicionar updated_at e appointment_id
    updateFields.push(`updated_at = NOW()`);
    updateValues.push(appointmentId);

    const updateQuery = `
      UPDATE appointments 
      SET ${updateFields.join(', ')}
      WHERE id = $${paramIndex}
      RETURNING id, user_id, business_id, service_id, date_time, duration_minutes, status, notes, price, created_at, updated_at
    `;

    const updatedAppointment = await executeQuery(updateQuery, updateValues);

    console.log('✅ Agendamento atualizado:', updatedAppointment[0]);

    return NextResponse.json({
      success: true,
      data: updatedAppointment[0],
      message: 'Agendamento atualizado com sucesso'
    });

  } catch (error) {
    console.error('❌ Erro ao atualizar agendamento:', error);
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

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const resolvedParams = await params;
    const appointmentId = resolvedParams.id;

    console.log(`🗑️ Excluindo agendamento ${appointmentId}...`);

    // Verificar se o agendamento existe
    const checkQuery = 'SELECT id, status FROM appointments WHERE id = $1';
    const existingAppointment = await executeQuery(checkQuery, [appointmentId]);

    if (!existingAppointment || existingAppointment.length === 0) {
      return NextResponse.json(
        { success: false, error: 'Agendamento não encontrado' },
        { status: 404 }
      );
    }

    // Verificar se o agendamento pode ser excluído
    const appointment = existingAppointment[0];
    if (appointment.status === 'realizado') {
      return NextResponse.json(
        { success: false, error: 'Não é possível excluir um agendamento já realizado' },
        { status: 400 }
      );
    }

    // Excluir o agendamento
    const deleteQuery = 'DELETE FROM appointments WHERE id = $1 RETURNING id';
    const deletedAppointment = await executeQuery(deleteQuery, [appointmentId]);

    console.log('✅ Agendamento excluído:', deletedAppointment[0]);

    return NextResponse.json({
      success: true,
      data: deletedAppointment[0],
      message: 'Agendamento excluído com sucesso'
    });

  } catch (error) {
    console.error('❌ Erro ao excluir agendamento:', error);
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




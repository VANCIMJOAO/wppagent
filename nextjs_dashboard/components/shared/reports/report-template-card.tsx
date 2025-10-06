/**
 * 🚀 REPORT TEMPLATE CARD - FASE 3 REFATORAÇÃO
 * ==============================================
 * 
 * Card para exibir template de relatório.
 * Extraído do AutomatedReports para melhor organização.
 * 
 * Autor: Claude AI - Refatoração Auditoria
 * Data: 02/10/2025
 */

'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Calendar, 
  Clock, 
  Play, 
  Pause, 
  Edit3, 
  Trash2, 
  Mail, 
  MessageSquare 
} from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { ReportTemplateCardProps } from './types';

export function ReportTemplateCard({
  template,
  onEdit,
  onDelete,
  onToggle,
  onRunNow
}: ReportTemplateCardProps) {
  const getFrequencyLabel = (frequency: string) => {
    switch (frequency) {
      case 'daily': return 'Diário';
      case 'weekly': return 'Semanal';
      case 'monthly': return 'Mensal';
      case 'custom': return 'Personalizado';
      default: return frequency;
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'overview': return 'Overview';
      case 'performance': return 'Performance';
      case 'conversations': return 'Conversas';
      case 'custom': return 'Personalizado';
      default: return type;
    }
  };

  const getFormatLabel = (format: string) => {
    switch (format) {
      case 'pdf': return 'PDF';
      case 'excel': return 'Excel';
      case 'csv': return 'CSV';
      case 'html': return 'HTML';
      default: return format.toUpperCase();
    }
  };

  const getScheduleText = () => {
    const { frequency, schedule } = template;
    
    switch (frequency) {
      case 'daily':
        return `Todos os dias às ${schedule.time}`;
      case 'weekly':
        const days = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];
        return `Toda ${days[schedule.dayOfWeek || 1]} às ${schedule.time}`;
      case 'monthly':
        return `Todo dia ${schedule.dayOfMonth || 1} às ${schedule.time}`;
      case 'custom':
        return `Personalizado: ${schedule.customCron || 'Não configurado'}`;
      default:
        return 'Não configurado';
    }
  };

  const getNextRunText = () => {
    if (!template.nextRun) return 'Não agendado';
    return format(template.nextRun, 'dd/MM/yyyy HH:mm', { locale: ptBR });
  };

  const getLastRunText = () => {
    if (!template.lastRun) return 'Nunca executado';
    return format(template.lastRun, 'dd/MM/yyyy HH:mm', { locale: ptBR });
  };

  const totalRecipients = template.recipients.email.length + template.recipients.whatsapp.length;

  return (
    <Card className={`transition-all duration-200 ${template.active ? 'border-green-200 bg-green-50' : ''}`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg flex items-center gap-2">
              {template.name}
              <Badge variant={template.active ? 'default' : 'secondary'}>
                {template.active ? 'Ativo' : 'Inativo'}
              </Badge>
            </CardTitle>
            <CardDescription className="mt-1">
              {template.description}
            </CardDescription>
          </div>
          
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onToggle(template.id)}
              className="h-8 w-8 p-0"
            >
              {template.active ? (
                <Pause className="h-4 w-4" />
              ) : (
                <Play className="h-4 w-4" />
              )}
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onEdit(template)}
              className="h-8 w-8 p-0"
            >
              <Edit3 className="h-4 w-4" />
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onDelete(template.id)}
              className="h-8 w-8 p-0 text-red-600 hover:text-red-700"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Informações básicas */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="font-medium text-gray-600">Tipo:</span>
            <Badge variant="outline" className="ml-2">
              {getTypeLabel(template.type)}
            </Badge>
          </div>
          
          <div>
            <span className="font-medium text-gray-600">Frequência:</span>
            <Badge variant="outline" className="ml-2">
              {getFrequencyLabel(template.frequency)}
            </Badge>
          </div>
          
          <div>
            <span className="font-medium text-gray-600">Formato:</span>
            <Badge variant="outline" className="ml-2">
              {getFormatLabel(template.format)}
            </Badge>
          </div>
          
          <div>
            <span className="font-medium text-gray-600">Destinatários:</span>
            <span className="ml-2">{totalRecipients}</span>
          </div>
        </div>

        {/* Agendamento */}
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Calendar className="h-4 w-4" />
          <span className="font-medium">Agendamento:</span>
          <span>{getScheduleText()}</span>
        </div>

        {/* Próxima execução */}
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Clock className="h-4 w-4" />
          <span className="font-medium">Próxima execução:</span>
          <span>{getNextRunText()}</span>
        </div>

        {/* Última execução */}
        {template.lastRun && (
          <div className="text-sm text-gray-500">
            <span className="font-medium">Última execução:</span>
            <span className="ml-2">{getLastRunText()}</span>
          </div>
        )}

        {/* Destinatários */}
        {totalRecipients > 0 && (
          <div className="space-y-2">
            <span className="text-sm font-medium text-gray-600">Destinatários:</span>
            
            {template.recipients.email.length > 0 && (
              <div className="flex items-center gap-2 text-sm">
                <Mail className="h-4 w-4 text-blue-600" />
                <span>{template.recipients.email.length} email(s)</span>
                <div className="flex gap-1">
                  {template.recipients.email.slice(0, 2).map((email, index) => (
                    <Badge key={index} variant="outline" className="text-xs">
                      {email}
                    </Badge>
                  ))}
                  {template.recipients.email.length > 2 && (
                    <Badge variant="outline" className="text-xs">
                      +{template.recipients.email.length - 2}
                    </Badge>
                  )}
                </div>
              </div>
            )}
            
            {template.recipients.whatsapp.length > 0 && (
              <div className="flex items-center gap-2 text-sm">
                <MessageSquare className="h-4 w-4 text-green-600" />
                <span>{template.recipients.whatsapp.length} WhatsApp(s)</span>
                <div className="flex gap-1">
                  {template.recipients.whatsapp.slice(0, 2).map((phone, index) => (
                    <Badge key={index} variant="outline" className="text-xs">
                      {phone}
                    </Badge>
                  ))}
                  {template.recipients.whatsapp.length > 2 && (
                    <Badge variant="outline" className="text-xs">
                      +{template.recipients.whatsapp.length - 2}
                    </Badge>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Ações */}
        <div className="flex justify-between items-center pt-2 border-t">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onRunNow(template.id)}
            disabled={!template.active}
          >
            <Play className="h-4 w-4 mr-2" />
            Executar Agora
          </Button>
          
          <div className="text-xs text-gray-500">
            Criado em {format(template.createdAt, 'dd/MM/yyyy', { locale: ptBR })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

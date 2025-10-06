/**
 * 🚀 REPORT EXECUTION CARD - FASE 3 REFATORAÇÃO
 * ===============================================
 * 
 * Card para exibir execução de relatório.
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
  Download, 
  Send, 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  Clock,
  FileText
} from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { ReportExecutionCardProps } from './types';

export function ReportExecutionCard({
  execution,
  template,
  onDownload,
  onResend
}: ReportExecutionCardProps) {
  const getStatusIcon = () => {
    switch (execution.status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'running':
        return <Clock className="h-4 w-4 text-blue-600 animate-spin" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusLabel = () => {
    switch (execution.status) {
      case 'completed':
        return 'Concluído';
      case 'failed':
        return 'Falhou';
      case 'running':
        return 'Executando';
      default:
        return 'Desconhecido';
    }
  };

  const getStatusVariant = () => {
    switch (execution.status) {
      case 'completed':
        return 'default' as const;
      case 'failed':
        return 'destructive' as const;
      case 'running':
        return 'secondary' as const;
      default:
        return 'outline' as const;
    }
  };

  const getDuration = () => {
    if (!execution.endTime) return 'Em andamento';
    
    const duration = execution.endTime.getTime() - execution.startTime.getTime();
    const seconds = Math.floor(duration / 1000);
    const minutes = Math.floor(seconds / 60);
    
    if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    }
    return `${seconds}s`;
  };

  const getFileSize = () => {
    if (!execution.fileSize) return null;
    
    const sizeInMB = execution.fileSize / (1024 * 1024);
    if (sizeInMB < 1) {
      return `${Math.round(execution.fileSize / 1024)} KB`;
    }
    return `${sizeInMB.toFixed(1)} MB`;
  };

  const getRecipientsStatus = () => {
    const emailCount = Object.keys(execution.recipients.email).length;
    const whatsappCount = Object.keys(execution.recipients.whatsapp).length;
    const emailSuccess = Object.values(execution.recipients.email).filter(status => status === 'sent').length;
    const whatsappSuccess = Object.values(execution.recipients.whatsapp).filter(status => status === 'sent').length;
    
    return {
      total: emailCount + whatsappCount,
      successful: emailSuccess + whatsappSuccess,
      failed: (emailCount + whatsappCount) - (emailSuccess + whatsappSuccess)
    };
  };

  const recipientsStatus = getRecipientsStatus();

  return (
    <Card className="transition-all duration-200">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg flex items-center gap-2">
              {getStatusIcon()}
              {template?.name || 'Relatório'}
              <Badge variant={getStatusVariant()}>
                {getStatusLabel()}
              </Badge>
            </CardTitle>
            <CardDescription className="mt-1">
              {template?.description || 'Execução de relatório'}
            </CardDescription>
          </div>
          
          <div className="flex items-center gap-1">
            {execution.fileUrl && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onDownload(execution.id)}
                className="h-8 w-8 p-0"
              >
                <Download className="h-4 w-4" />
              </Button>
            )}
            
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onResend(execution.id)}
              className="h-8 w-8 p-0"
              disabled={execution.status === 'running'}
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Informações de execução */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="font-medium text-gray-600">Início:</span>
            <span className="ml-2">
              {format(execution.startTime, 'dd/MM/yyyy HH:mm:ss', { locale: ptBR })}
            </span>
          </div>
          
          {execution.endTime && (
            <div>
              <span className="font-medium text-gray-600">Fim:</span>
              <span className="ml-2">
                {format(execution.endTime, 'dd/MM/yyyy HH:mm:ss', { locale: ptBR })}
              </span>
            </div>
          )}
          
          <div>
            <span className="font-medium text-gray-600">Duração:</span>
            <span className="ml-2">{getDuration()}</span>
          </div>
          
          {execution.fileSize && (
            <div>
              <span className="font-medium text-gray-600">Tamanho:</span>
              <span className="ml-2">{getFileSize()}</span>
            </div>
          )}
        </div>

        {/* Status do arquivo */}
        {execution.fileUrl && (
          <div className="flex items-center gap-2 text-sm">
            <FileText className="h-4 w-4 text-blue-600" />
            <span className="font-medium text-gray-600">Arquivo:</span>
            <Badge variant="outline" className="text-xs">
              {template?.format?.toUpperCase() || 'PDF'}
            </Badge>
            {execution.fileSize && (
              <span className="text-gray-500">({getFileSize()})</span>
            )}
          </div>
        )}

        {/* Status dos destinatários */}
        {recipientsStatus.total > 0 && (
          <div className="space-y-2">
            <span className="text-sm font-medium text-gray-600">Destinatários:</span>
            
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span>{recipientsStatus.successful} enviado(s)</span>
              </div>
              
              {recipientsStatus.failed > 0 && (
                <div className="flex items-center gap-2">
                  <XCircle className="h-4 w-4 text-red-600" />
                  <span>{recipientsStatus.failed} falhou(ram)</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Progress bar para execução em andamento */}
        {execution.status === 'running' && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="font-medium text-gray-600">Progresso</span>
              <span className="text-gray-500">Gerando relatório...</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
            </div>
          </div>
        )}

        {/* Ações */}
        <div className="flex justify-between items-center pt-2 border-t">
          <div className="flex gap-2">
            {execution.fileUrl && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onDownload(execution.id)}
                className="flex items-center gap-2"
              >
                <Download className="h-4 w-4" />
                Baixar
              </Button>
            )}
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => onResend(execution.id)}
              disabled={execution.status === 'running'}
              className="flex items-center gap-2"
            >
              <Send className="h-4 w-4" />
              Reenviar
            </Button>
          </div>
          
          <div className="text-xs text-gray-500">
            ID: {execution.id.slice(-8)}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

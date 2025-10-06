/**
 * 🚀 ERROR FALLBACK COMPONENT - FASE 3 REFATORAÇÃO
 * =================================================
 * 
 * Componente de fallback para exibir erros de forma amigável.
 * Extraído do AdvancedErrorBoundary para melhor organização.
 * 
 * Autor: Claude AI - Refatoração Auditoria
 * Data: 02/10/2025
 */

'use client';

import React from 'react';
import { AlertTriangle, RefreshCw, Bug, Home, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from './collapsible';
import { ErrorFallbackProps } from './types';

export function ErrorFallback({
  error,
  errorInfo,
  errorId,
  retryCount,
  isRetrying,
  showErrorDetails,
  actions,
  level,
  context
}: ErrorFallbackProps) {
  const isPageLevel = level === 'page';
  const isSectionLevel = level === 'section';

  const renderErrorDetails = () => {
    if (!showErrorDetails) return null;

    return (
      <Collapsible>
        <CollapsibleTrigger className="text-sm text-gray-600 hover:text-gray-800 mb-4">
          <Bug size={16} />
          Detalhes Técnicos
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div className="space-y-4">
            <div>
              <h4 className="font-medium text-sm mb-2">Informações do Erro</h4>
              <div className="bg-gray-50 p-3 rounded text-xs font-mono">
                <div><strong>ID:</strong> {errorId}</div>
                <div><strong>Mensagem:</strong> {error.message}</div>
                <div><strong>Contexto:</strong> {context || 'Não especificado'}</div>
                <div><strong>Nível:</strong> {level}</div>
                <div><strong>Tentativas:</strong> {retryCount}</div>
              </div>
            </div>

            {error.stack && (
              <div>
                <h4 className="font-medium text-sm mb-2">Stack Trace</h4>
                <pre className="bg-gray-50 p-3 rounded text-xs font-mono overflow-auto max-h-40">
                  {error.stack}
                </pre>
              </div>
            )}

            {errorInfo?.componentStack && (
              <div>
                <h4 className="font-medium text-sm mb-2">Component Stack</h4>
                <pre className="bg-gray-50 p-3 rounded text-xs font-mono overflow-auto max-h-40">
                  {errorInfo.componentStack}
                </pre>
              </div>
            )}
          </div>
        </CollapsibleContent>
      </Collapsible>
    );
  };

  const renderActions = () => {
    if (isPageLevel) {
      return (
        <div className="flex flex-col sm:flex-row gap-3">
          <Button 
            onClick={actions.onRetry} 
            disabled={isRetrying}
            className="flex items-center gap-2"
          >
            <RefreshCw className={isRetrying ? 'animate-spin' : ''} size={16} />
            {isRetrying ? 'Tentando...' : 'Tentar Novamente'}
          </Button>
          <Button 
            variant="outline" 
            onClick={actions.onGoHome}
            className="flex items-center gap-2"
          >
            <Home size={16} />
            Ir para Início
          </Button>
          <Button 
            variant="outline" 
            onClick={actions.onReport}
            className="flex items-center gap-2"
          >
            <Bug size={16} />
            Reportar Erro
          </Button>
        </div>
      );
    }

    if (isSectionLevel) {
      return (
        <div className="flex gap-2">
          <Button 
            size="sm"
            onClick={actions.onRetry} 
            disabled={isRetrying}
            className="flex items-center gap-2"
          >
            <RefreshCw className={isRetrying ? 'animate-spin' : ''} size={14} />
            {isRetrying ? 'Tentando...' : 'Recarregar'}
          </Button>
          <Button 
            variant="outline" 
            size="sm"
            onClick={actions.onGoBack}
            className="flex items-center gap-2"
          >
            <ArrowLeft size={14} />
            Voltar
          </Button>
        </div>
      );
    }

    // Component level
    return (
      <Button 
        size="sm"
        variant="outline"
        onClick={actions.onRetry} 
        disabled={isRetrying}
        className="flex items-center gap-2"
      >
        <RefreshCw className={isRetrying ? 'animate-spin' : ''} size={14} />
        Recarregar
      </Button>
    );
  };

  const getErrorTitle = () => {
    switch (level) {
      case 'page':
        return 'Algo deu errado na página';
      case 'section':
        return 'Erro nesta seção';
      case 'component':
        return 'Erro no componente';
      default:
        return 'Algo deu errado';
    }
  };

  const getErrorDescription = () => {
    switch (level) {
      case 'page':
        return 'Encontramos um problema ao carregar esta página. Tente recarregar ou volte para a página inicial.';
      case 'section':
        return 'Esta seção não pôde ser carregada corretamente.';
      case 'component':
        return 'Este componente encontrou um erro inesperado.';
      default:
        return 'Um erro inesperado ocorreu.';
    }
  };

  if (isPageLevel) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <Card className="w-full max-w-2xl">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-red-600" />
            </div>
            <CardTitle className="text-xl">{getErrorTitle()}</CardTitle>
            <CardDescription>
              {getErrorDescription()}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Erro</AlertTitle>
              <AlertDescription>{error.message}</AlertDescription>
            </Alert>

            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Badge variant="outline">ID: {errorId}</Badge>
              {retryCount > 0 && (
                <Badge variant="secondary">Tentativa {retryCount}</Badge>
              )}
            </div>

            {renderErrorDetails()}

            {renderActions()}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (isSectionLevel) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-600" />
            <CardTitle className="text-lg">{getErrorTitle()}</CardTitle>
          </div>
          <CardDescription>{getErrorDescription()}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert variant="destructive">
            <AlertDescription>{error.message}</AlertDescription>
          </Alert>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Badge variant="outline" className="text-xs">ID: {errorId}</Badge>
              {retryCount > 0 && (
                <Badge variant="secondary" className="text-xs">Tentativa {retryCount}</Badge>
              )}
            </div>
            {renderActions()}
          </div>

          {renderErrorDetails()}
        </CardContent>
      </Card>
    );
  }

  // Component level
  return (
    <div className="p-4 border border-red-200 bg-red-50 rounded-lg">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-600" />
          <span className="text-sm font-medium text-red-800">{getErrorTitle()}</span>
        </div>
        {renderActions()}
      </div>
      <p className="text-sm text-red-700 mt-2">{error.message}</p>
      {showErrorDetails && renderErrorDetails()}
    </div>
  );
}

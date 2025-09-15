/**
 * Componente de Error Fallback para tratamento de erros
 * Usado em conjunto com loading states
 */

import { AlertTriangle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

interface ErrorFallbackProps {
  error: string | Error;
  retry?: () => void;
  title?: string;
  compact?: boolean;
}

export function ErrorFallback({
  error,
  retry,
  title = "Erro ao carregar dados",
  compact = false
}: ErrorFallbackProps) {
  const errorMessage = typeof error === 'string' ? error : error?.message || 'Erro desconhecido';

  if (compact) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center p-6">
          <div className="text-center">
            <AlertTriangle className="mx-auto h-6 w-6 text-red-500 mb-2" />
            <p className="text-sm text-muted-foreground mb-3">{errorMessage}</p>
            {retry && (
              <Button variant="outline" size="sm" onClick={retry}>
                <RefreshCw className="w-3 h-3 mr-1" />
                Tentar novamente
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-[200px]">
      <Card className="w-full max-w-md">
        <CardContent className="text-center p-6">
          <AlertTriangle className="mx-auto h-12 w-12 text-red-500 mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {title}
          </h3>
          <p className="text-gray-600 mb-6">
            {errorMessage}
          </p>
          {retry && (
            <Button onClick={retry} className="w-full">
              <RefreshCw className="w-4 h-4 mr-2" />
              Tentar novamente
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

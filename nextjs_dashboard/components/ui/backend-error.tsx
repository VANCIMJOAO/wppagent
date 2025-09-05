import { AlertTriangle, RefreshCw, Wifi } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface BackendErrorProps {
  error: string;
  onRetry?: () => void;
  showRetry?: boolean;
}

export default function BackendError({ error, onRetry, showRetry = true }: BackendErrorProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] p-8">
      <Card className="w-full max-w-md text-center">
        <CardHeader>
          <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
            <Wifi className="h-8 w-8 text-red-600" />
          </div>
          <CardTitle className="text-xl text-red-800">
            Problema de Conectividade
          </CardTitle>
          <CardDescription>
            Não foi possível conectar com o servidor
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-4">
          <Alert className="text-left">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription className="text-sm">
              {error}
            </AlertDescription>
          </Alert>
          
          <div className="text-sm text-gray-600 space-y-2">
            <p>Possíveis causas:</p>
            <ul className="list-disc list-inside space-y-1 text-left">
              <li>Servidor em manutenção</li>
              <li>Problema temporário de conexão</li>
              <li>Erro interno do servidor</li>
            </ul>
          </div>
          
          {showRetry && onRetry && (
            <Button 
              onClick={onRetry} 
              className="w-full"
              variant="outline"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Tentar Novamente
            </Button>
          )}
          
          <p className="text-xs text-gray-500">
            Se o problema persistir, entre em contato com o suporte
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

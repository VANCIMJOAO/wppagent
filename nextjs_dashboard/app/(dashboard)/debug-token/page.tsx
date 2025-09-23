'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';

export default function DebugTokenPage() {
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const testToken = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/debug-token');
      const data = await response.json();
      setResult(data);
    } catch (error) {
      setResult({ error: 'Erro ao testar token' });
    } finally {
      setLoading(false);
    }
  };

  const testConversations = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/conversations?limit=5');
      const data = await response.json();
      setResult({ conversationsTest: data });
    } catch (error) {
      setResult({ error: 'Erro ao testar conversas' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Debug Token</h1>
      
      <div className="space-y-4">
        <Button onClick={testToken} disabled={loading}>
          {loading ? 'Testando...' : 'Testar Token'}
        </Button>
        
        <Button onClick={testConversations} disabled={loading} variant="outline">
          {loading ? 'Testando...' : 'Testar Conversas'}
        </Button>
        
        {result && (
          <div className="mt-6">
            <h2 className="text-lg font-semibold mb-2">Resultado:</h2>
            <pre className="bg-gray-100 p-4 rounded text-sm overflow-auto max-h-96">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

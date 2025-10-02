"use client";

import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Shield,
  Download,
  Trash2,
  Eye,
  FileText,
  AlertTriangle,
  CheckCircle,
  Clock,
  User,
  MessageSquare,
  Calendar,
  Settings,
  Info,
  Lock,
  Database,
  ShieldCheck
} from 'lucide-react';
import { toast } from 'sonner';
import api from '@/lib/api-service';

interface PersonalData {
  user_identifier: string;
  data_access_date: string;
  legal_basis: string;
  data: {
    personal_data: any;
    conversations_count: number;
    appointments_count: number;
    data_categories: string[];
  };
  retention_info: {
    personal_data: string;
    conversations: string;
    appointments: string;
  };
  user_rights: {
    can_export: boolean;
    can_delete: boolean;
    can_correct: boolean;
    can_object: boolean;
  };
}

interface DataPortabilityRequest {
  request_id: string;
  status: string;
  estimated_completion?: string;
  format: string;
  encryption: {
    enabled: boolean;
    algorithm: string;
    key_delivery: string;
  };
  data_categories: string[];
  estimated_file_size?: string;
  retention_period: string;
  download_expires_at?: string;
}

interface UserRights {
  lgpd_rights: {
    [key: string]: {
      right: string;
      endpoint: string;
      description: string;
    };
  };
  how_to_exercise: {
    online: string;
    email: string;
    response_time: string;
  };
}

export default function LGPDPage() {
  const [activeTab, setActiveTab] = useState('meus-dados');
  const [loading, setLoading] = useState(true);
  const [personalData, setPersonalData] = useState<PersonalData | null>(null);
  const [portabilityRequest, setPortabilityRequest] = useState<DataPortabilityRequest | null>(null);
  const [userRights, setUserRights] = useState<UserRights | null>(null);
  const [deleteAccountDialog, setDeleteAccountDialog] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = useState('');
  const [deleting, setDeleting] = useState(false);

  // Load data on component mount
  useEffect(() => {
    loadPersonalData();
    loadUserRights();
  }, []);

  const loadPersonalData = async () => {
    try {
      setLoading(true);
      const response = await api.get('/lgpd/my-data');
      setPersonalData(response.data);
    } catch (error) {
      console.error('Erro ao carregar dados pessoais:', error);
      toast.error('Erro ao carregar dados pessoais');
    } finally {
      setLoading(false);
    }
  };

  const loadUserRights = async () => {
    try {
      const response = await api.get('/lgpd/user-rights');
      setUserRights(response.data);
    } catch (error) {
      console.error('Erro ao carregar direitos do usuário:', error);
    }
  };

  const requestDataPortability = async () => {
    try {
      const requestData = {
        format: 'JSON',
        data_categories: ['personal_info', 'appointments', 'conversations', 'preferences'],
        include_metadata: true,
        encryption_requested: true,
        delivery_method: 'download'
      };

      const response = await api.post('/lgpd/data-portability', requestData);
      setPortabilityRequest(response.data.data);
      toast.success('Solicitação de portabilidade enviada com sucesso!');
    } catch (error) {
      console.error('Erro ao solicitar portabilidade:', error);
      toast.error('Erro ao solicitar portabilidade de dados');
    }
  };

  const downloadDataExport = async (requestId: string) => {
    try {
      const response = await api.get(`/lgpd/data-portability/${requestId}/download`, {
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data], { type: 'application/zip' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `meus_dados_pessoais_${new Date().toISOString().split('T')[0]}.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success('Download iniciado com sucesso!');
    } catch (error) {
      console.error('Erro ao baixar dados:', error);
      toast.error('Erro ao baixar arquivo de dados');
    }
  };

  const deleteAccount = async () => {
    if (deleteConfirmation !== 'CONFIRMAR EXCLUSÃO') {
      toast.error('Por favor, digite exatamente "CONFIRMAR EXCLUSÃO"');
      return;
    }

    try {
      setDeleting(true);
      const response = await api.post('/lgpd/delete-account', {
        confirmation: deleteConfirmation,
        reason: 'User requested account deletion via LGPD interface'
      });
      
      toast.success('Solicitação de exclusão enviada com sucesso!');
      setDeleteAccountDialog(false);
      setDeleteConfirmation('');
    } catch (error) {
      console.error('Erro ao solicitar exclusão:', error);
      toast.error('Erro ao solicitar exclusão da conta');
    } finally {
      setDeleting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'processing':
        return <Badge variant="secondary" className="flex items-center gap-1"><Clock className="w-3 h-3" />Processando</Badge>;
      case 'completed':
        return <Badge variant="default" className="flex items-center gap-1"><CheckCircle className="w-3 h-3" />Concluído</Badge>;
      case 'failed':
        return <Badge variant="destructive" className="flex items-center gap-1"><AlertTriangle className="w-3 h-3" />Falhou</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">LGPD - Proteção de Dados</h1>
            <p className="text-muted-foreground">Gerencie seus dados pessoais e direitos conforme a LGPD</p>
          </div>
        </div>
        <div className="grid gap-6">
          <Skeleton className="h-32" />
          <Skeleton className="h-64" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Shield className="w-8 h-8 text-blue-600" />
            LGPD - Proteção de Dados
          </h1>
          <p className="text-muted-foreground">
            Gerencie seus dados pessoais e exerça seus direitos conforme a Lei Geral de Proteção de Dados
          </p>
        </div>
      </div>

      {/* Compliance Status Alert */}
      <Alert>
        <ShieldCheck className="h-4 w-4" />
        <AlertDescription>
          <strong>Sistema em conformidade com a LGPD:</strong> Todos os seus dados são tratados de acordo com a Lei Geral de Proteção de Dados (Lei nº 13.709/2018).
        </AlertDescription>
      </Alert>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="meus-dados" className="flex items-center gap-2">
            <Database className="w-4 h-4" />
            Meus Dados
          </TabsTrigger>
          <TabsTrigger value="portabilidade" className="flex items-center gap-2">
            <Download className="w-4 h-4" />
            Portabilidade
          </TabsTrigger>
          <TabsTrigger value="exclusao" className="flex items-center gap-2">
            <Trash2 className="w-4 h-4" />
            Exclusão
          </TabsTrigger>
          <TabsTrigger value="direitos" className="flex items-center gap-2">
            <Shield className="w-4 h-4" />
            Direitos
          </TabsTrigger>
          <TabsTrigger value="privacidade" className="flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Privacidade
          </TabsTrigger>
        </TabsList>

        {/* Meus Dados Tab */}
        <TabsContent value="meus-dados" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Eye className="w-5 h-5" />
                Seus Dados Pessoais
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {personalData ? (
                <>
                  {/* Data Summary */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="flex items-center gap-3 p-4 border rounded-lg">
                      <User className="w-8 h-8 text-blue-600" />
                      <div>
                        <p className="text-sm font-medium">Dados Pessoais</p>
                        <p className="text-2xl font-bold">{personalData.data.personal_data ? 'Disponível' : 'N/A'}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 p-4 border rounded-lg">
                      <MessageSquare className="w-8 h-8 text-green-600" />
                      <div>
                        <p className="text-sm font-medium">Conversas</p>
                        <p className="text-2xl font-bold">{personalData.data.conversations_count}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 p-4 border rounded-lg">
                      <Calendar className="w-8 h-8 text-purple-600" />
                      <div>
                        <p className="text-sm font-medium">Agendamentos</p>
                        <p className="text-2xl font-bold">{personalData.data.appointments_count}</p>
                      </div>
                    </div>
                  </div>

                  {/* Data Categories */}
                  <div>
                    <h3 className="text-lg font-semibold mb-3">Categorias de Dados</h3>
                    <div className="flex flex-wrap gap-2">
                      {personalData.data.data_categories.map((category, index) => (
                        <Badge key={index} variant="outline">
                          {category.replace('_', ' ').toUpperCase()}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  {/* Retention Information */}
                  <div>
                    <h3 className="text-lg font-semibold mb-3">Política de Retenção</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {Object.entries(personalData.retention_info).map(([key, value]) => (
                        <div key={key} className="p-3 border rounded-lg">
                          <p className="text-sm font-medium capitalize">{key.replace('_', ' ')}</p>
                          <p className="text-lg font-semibold text-blue-600">{value}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* User Rights Status */}
                  <div>
                    <h3 className="text-lg font-semibold mb-3">Seus Direitos</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      {Object.entries(personalData.user_rights).map(([right, available]) => (
                        <div key={right} className="flex items-center gap-2 p-2 border rounded">
                          {available ? (
                            <CheckCircle className="w-4 h-4 text-green-600" />
                          ) : (
                            <AlertTriangle className="w-4 h-4 text-orange-500" />
                          )}
                          <span className="text-sm capitalize">{right.replace('_', ' ')}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              ) : (
                <div className="text-center py-8">
                  <AlertTriangle className="w-12 h-12 text-orange-500 mx-auto mb-4" />
                  <p className="text-muted-foreground">Não foi possível carregar seus dados pessoais.</p>
                  <Button onClick={loadPersonalData} className="mt-4">
                    Tentar Novamente
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Portabilidade Tab */}
        <TabsContent value="portabilidade" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Download className="w-5 h-5" />
                Portabilidade de Dados
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="bg-blue-50 p-4 rounded-lg">
                <h3 className="font-semibold text-blue-900 mb-2">Sobre a Portabilidade</h3>
                <p className="text-blue-800 text-sm">
                  Você tem o direito de solicitar uma cópia de todos os seus dados pessoais em formato estruturado e legível por máquina. 
                  Os dados serão fornecidos em formato JSON dentro de um arquivo ZIP criptografado.
                </p>
              </div>

              {portabilityRequest ? (
                <div className="space-y-4">
                  <div className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold">Solicitação de Portabilidade</h4>
                      {getStatusBadge(portabilityRequest.status)}
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-muted-foreground">ID da Solicitação:</p>
                        <p className="font-mono">{portabilityRequest.request_id}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Formato:</p>
                        <p>{portabilityRequest.format}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Criptografia:</p>
                        <p className="flex items-center gap-1">
                          <Lock className="w-3 h-3" />
                          {portabilityRequest.encryption.algorithm}
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Período de Retenção:</p>
                        <p>{portabilityRequest.retention_period}</p>
                      </div>
                    </div>
                    
                    {portabilityRequest.status === 'completed' && (
                      <div className="mt-4">
                        <Button 
                          onClick={() => downloadDataExport(portabilityRequest.request_id)}
                          className="w-full"
                        >
                          <Download className="w-4 h-4 mr-2" />
                          Baixar Meus Dados
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <Database className="w-12 h-12 text-blue-500 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold mb-2">Solicitar Portabilidade de Dados</h3>
                  <p className="text-muted-foreground mb-4">
                    Clique no botão abaixo para solicitar uma cópia completa dos seus dados pessoais.
                  </p>
                  <Button onClick={requestDataPortability} size="lg">
                    <Download className="w-4 h-4 mr-2" />
                    Solicitar Portabilidade
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Exclusão Tab */}
        <TabsContent value="exclusao" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Trash2 className="w-5 h-5" />
                Exclusão de Conta
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="bg-red-50 p-4 rounded-lg">
                <h3 className="font-semibold text-red-900 mb-2">⚠️ Aviso Importante</h3>
                <p className="text-red-800 text-sm">
                  A exclusão da sua conta é <strong>irreversível</strong>. Todos os seus dados pessoais, 
                  conversas e agendamentos serão permanentemente removidos do sistema.
                </p>
              </div>

              <div className="space-y-4">
                <h4 className="font-semibold">O que será excluído:</h4>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li className="flex items-center gap-2">
                    <Trash2 className="w-4 h-4 text-red-500" />
                    Seus dados pessoais (nome, telefone, email)
                  </li>
                  <li className="flex items-center gap-2">
                    <Trash2 className="w-4 h-4 text-red-500" />
                    Histórico completo de conversas
                  </li>
                  <li className="flex items-center gap-2">
                    <Trash2 className="w-4 h-4 text-red-500" />
                    Todos os agendamentos
                  </li>
                  <li className="flex items-center gap-2">
                    <Trash2 className="w-4 h-4 text-red-500" />
                    Preferências e configurações
                  </li>
                </ul>
              </div>

              <Dialog open={deleteAccountDialog} onOpenChange={setDeleteAccountDialog}>
                <DialogTrigger asChild>
                  <Button variant="destructive" className="w-full">
                    <Trash2 className="w-4 h-4 mr-2" />
                    Solicitar Exclusão da Conta
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle className="flex items-center gap-2 text-red-600">
                      <AlertTriangle className="w-5 h-5" />
                      Confirmar Exclusão da Conta
                    </DialogTitle>
                    <DialogDescription>
                      Esta ação é <strong>irreversível</strong>. Digite exatamente "CONFIRMAR EXCLUSÃO" 
                      para prosseguir com a solicitação de exclusão da sua conta.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium">Confirmação:</label>
                      <input
                        type="text"
                        value={deleteConfirmation}
                        onChange={(e) => setDeleteConfirmation(e.target.value)}
                        placeholder="Digite: CONFIRMAR EXCLUSÃO"
                        className="w-full mt-1 px-3 py-2 border rounded-md"
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button 
                      variant="outline" 
                      onClick={() => setDeleteAccountDialog(false)}
                    >
                      Cancelar
                    </Button>
                    <Button 
                      variant="destructive" 
                      onClick={deleteAccount}
                      disabled={deleting || deleteConfirmation !== 'CONFIRMAR EXCLUSÃO'}
                    >
                      {deleting ? 'Processando...' : 'Confirmar Exclusão'}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Direitos Tab */}
        <TabsContent value="direitos" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Seus Direitos LGPD
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {userRights ? (
                <div className="space-y-6">
                  <div className="grid gap-4">
                    {Object.entries(userRights.lgpd_rights).map(([key, right]) => (
                      <div key={key} className="flex items-center justify-between p-4 border rounded-lg">
                        <div className="flex items-center gap-3">
                          {right.endpoint !== "Não implementado" ? (
                            <CheckCircle className="w-5 h-5 text-green-600" />
                          ) : (
                            <AlertTriangle className="w-5 h-5 text-orange-500" />
                          )}
                          <div>
                            <h4 className="font-semibold">{right.right}</h4>
                            <p className="text-sm text-muted-foreground">{right.description}</p>
                            <p className="text-xs text-blue-600 font-mono">{right.endpoint}</p>
                          </div>
                        </div>
                        <Badge variant={right.endpoint !== "Não implementado" ? "default" : "secondary"}>
                          {right.endpoint !== "Não implementado" ? "Disponível" : "Em Desenvolvimento"}
                        </Badge>
                      </div>
                    ))}
                  </div>

                  <div className="bg-blue-50 p-4 rounded-lg">
                    <h4 className="font-semibold text-blue-900 mb-2">Como Exercer Seus Direitos</h4>
                    <div className="space-y-2 text-sm text-blue-800">
                      <p><strong>Online:</strong> {userRights.how_to_exercise.online}</p>
                      <p><strong>Email:</strong> {userRights.how_to_exercise.email}</p>
                      <p><strong>Prazo de Resposta:</strong> {userRights.how_to_exercise.response_time}</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <Shield className="w-12 h-12 text-blue-500 mx-auto mb-4" />
                  <p className="text-muted-foreground">Carregando seus direitos...</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Privacidade Tab */}
        <TabsContent value="privacidade" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Política de Privacidade
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="prose max-w-none">
                <h3 className="text-lg font-semibold mb-4">Como Tratamos Seus Dados</h3>
                
                <div className="space-y-4">
                  <div>
                    <h4 className="font-semibold text-blue-600">1. Dados Coletados</h4>
                    <p className="text-sm text-muted-foreground">
                      Coletamos apenas os dados necessários para fornecer nossos serviços: 
                      nome, telefone, email, conversas e agendamentos.
                    </p>
                  </div>

                  <div>
                    <h4 className="font-semibold text-blue-600">2. Finalidade do Tratamento</h4>
                    <p className="text-sm text-muted-foreground">
                      Seus dados são utilizados exclusivamente para: atendimento via WhatsApp, 
                      agendamento de consultas e melhoria dos nossos serviços.
                    </p>
                  </div>

                  <div>
                    <h4 className="font-semibold text-blue-600">3. Base Legal</h4>
                    <p className="text-sm text-muted-foreground">
                      O tratamento é baseado no consentimento (Art. 7º, I, LGPD) e na 
                      execução de contrato (Art. 7º, V, LGPD).
                    </p>
                  </div>

                  <div>
                    <h4 className="font-semibold text-blue-600">4. Compartilhamento</h4>
                    <p className="text-sm text-muted-foreground">
                      Não compartilhamos seus dados pessoais com terceiros, exceto quando 
                      necessário para cumprimento de obrigação legal.
                    </p>
                  </div>

                  <div>
                    <h4 className="font-semibold text-blue-600">5. Segurança</h4>
                    <p className="text-sm text-muted-foreground">
                      Implementamos medidas técnicas e organizacionais adequadas para 
                      proteger seus dados contra acesso não autorizado.
                    </p>
                  </div>

                  <div>
                    <h4 className="font-semibold text-blue-600">6. Seus Direitos</h4>
                    <p className="text-sm text-muted-foreground">
                      Você tem direito a: acesso, correção, exclusão, portabilidade, 
                      oposição e revogação do consentimento.
                    </p>
                  </div>
                </div>

                <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-semibold mb-2">Contato do Encarregado de Dados (DPO)</h4>
                  <p className="text-sm text-muted-foreground">
                    Para exercer seus direitos ou esclarecer dúvidas sobre o tratamento de dados:
                  </p>
                  <p className="text-sm font-mono mt-2">
                    Email: dpo@empresa.com<br />
                    Telefone: (11) 99999-9999
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}


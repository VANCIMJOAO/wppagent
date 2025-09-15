"use client";

import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Settings,
  Building2,
  Bot,
  Clock,
  FileText,
  Shield,
  Save,
  AlertCircle,
  CheckCircle,
  Smartphone,
  Globe,
  MessageSquare,
  Zap,
  Users,
  Calendar
} from 'lucide-react';
import { toast } from 'sonner';
import api from '@/lib/api-service';

interface CompanyConfig {
  name: string;
  description: string;
  phone: string;
  email: string;
  website: string;
  address: string;
  logo?: string;
}

interface BotConfig {
  name: string;
  welcomeMessage: string;
  defaultResponse: string;
  aiEnabled: boolean;
  responseDelay: number;
  maxTokens: number;
  temperature: number;
}

interface ScheduleConfig {
  workDays: string[];
  startTime: string;
  endTime: string;
  lunchStart: string;
  lunchEnd: string;
  timezone: string;
}

interface NotificationConfig {
  emailNotifications: boolean;
  smsNotifications: boolean;
  pushNotifications: boolean;
  appointmentReminders: boolean;
  newMessageAlerts: boolean;
}

export default function ConfiguracoesPage() {
  const [activeTab, setActiveTab] = useState('empresa');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  // Company configuration
  const [companyConfig, setCompanyConfig] = useState<CompanyConfig>({
    name: '',
    description: '',
    phone: '',
    email: '',
    website: '',
    address: ''
  });

  // Bot configuration
  const [botConfig, setBotConfig] = useState<BotConfig>({
    name: '',
    welcomeMessage: '',
    defaultResponse: '',
    aiEnabled: false,
    responseDelay: 2,
    maxTokens: 150,
    temperature: 0.7
  });

  // Schedule configuration
  const [scheduleConfig, setScheduleConfig] = useState<ScheduleConfig>({
    workDays: [],
    startTime: '',
    endTime: '',
    lunchStart: '',
    lunchEnd: '',
    timezone: 'America/Sao_Paulo'
  });

  // Notification configuration
  const [notificationConfig, setNotificationConfig] = useState<NotificationConfig>({
    emailNotifications: false,
    smsNotifications: false,
    pushNotifications: false,
    appointmentReminders: false,
    newMessageAlerts: false
  });

  // Load configurations on component mount
  useEffect(() => {
    const loadConfigurations = async () => {
      try {
        setLoading(true);

        // In a real implementation, you would fetch from different API endpoints
        // For now, we'll use default values that simulate real data
        setCompanyConfig({
          name: 'WhatsApp Agent',
          description: 'Sistema de automação e agendamento para WhatsApp',
          phone: '+55 11 99999-9999',
          email: 'contato@whatsappagent.com',
          website: 'https://whatsappagent.com',
          address: 'São Paulo, SP, Brasil'
        });

        setBotConfig({
          name: 'Assistente Virtual',
          welcomeMessage: 'Olá! Como posso ajudar você hoje?',
          defaultResponse: 'Desculpe, não entendi sua mensagem. Pode reformular?',
          aiEnabled: true,
          responseDelay: 2,
          maxTokens: 150,
          temperature: 0.7
        });

        setScheduleConfig({
          workDays: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
          startTime: '09:00',
          endTime: '18:00',
          lunchStart: '12:00',
          lunchEnd: '13:00',
          timezone: 'America/Sao_Paulo'
        });

        setNotificationConfig({
          emailNotifications: true,
          smsNotifications: false,
          pushNotifications: true,
          appointmentReminders: true,
          newMessageAlerts: true
        });

      } catch (error) {
        console.error('Erro ao carregar configurações:', error);
        toast.error('Erro ao carregar configurações');
      } finally {
        setLoading(false);
      }
    };

    loadConfigurations();
  }, []);

  const handleSave = async (configType: string) => {
    try {
      setSaving(true);

      // In a real implementation, you would save to different API endpoints
      // For now, we'll simulate the API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Here you would make actual API calls based on configType:
      // switch (configType) {
      //   case 'empresa':
      //     await api.updateCompanyConfig(companyConfig);
      //     break;
      //   case 'bot':
      //     await api.updateBotConfig(botConfig);
      //     break;
      //   case 'horarios':
      //     await api.updateScheduleConfig(scheduleConfig);
      //     break;
      //   case 'notificacoes':
      //     await api.updateNotificationConfig(notificationConfig);
      //     break;
      // }

      toast.success('Configurações salvas com sucesso!');
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (error) {
      console.error('Erro ao salvar configurações:', error);
      toast.error('Erro ao salvar configurações');
    } finally {
      setSaving(false);
    }
  };

  const workDayLabels = {
    'monday': 'Segunda-feira',
    'tuesday': 'Terça-feira',
    'wednesday': 'Quarta-feira',
    'thursday': 'Quinta-feira',
    'friday': 'Sexta-feira',
    'saturday': 'Sábado',
    'sunday': 'Domingo'
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Configurações</h1>
          <p className="text-gray-600 mt-1">Configurações do sistema e personalização</p>
        </div>
        {saved && (
          <Alert className="w-auto">
            <CheckCircle className="h-4 w-4" />
            <AlertDescription>Configurações salvas com sucesso!</AlertDescription>
          </Alert>
        )}
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="empresa" className="flex items-center space-x-2">
            <Building2 className="h-4 w-4" />
            <span>Empresa</span>
          </TabsTrigger>
          <TabsTrigger value="bot" className="flex items-center space-x-2">
            <Bot className="h-4 w-4" />
            <span>Bot & IA</span>
          </TabsTrigger>
          <TabsTrigger value="horarios" className="flex items-center space-x-2">
            <Clock className="h-4 w-4" />
            <span>Horários</span>
          </TabsTrigger>
          <TabsTrigger value="notificacoes" className="flex items-center space-x-2">
            <MessageSquare className="h-4 w-4" />
            <span>Notificações</span>
          </TabsTrigger>
          <TabsTrigger value="seguranca" className="flex items-center space-x-2">
            <Shield className="h-4 w-4" />
            <span>Segurança</span>
          </TabsTrigger>
        </TabsList>

        {/* Empresa Tab */}
        <TabsContent value="empresa" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center space-x-2">
                <Building2 className="h-5 w-5 text-blue-600" />
                <CardTitle>Informações da Empresa</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="company-name">Nome da Empresa</Label>
                  {loading ? (
                    <Skeleton className="h-10 w-full" />
                  ) : (
                    <Input
                      id="company-name"
                      value={companyConfig.name}
                      onChange={(e) => setCompanyConfig({...companyConfig, name: e.target.value})}
                      placeholder="Nome da sua empresa"
                    />
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="company-phone">Telefone</Label>
                  {loading ? (
                    <Skeleton className="h-10 w-full" />
                  ) : (
                    <Input
                      id="company-phone"
                      value={companyConfig.phone}
                      onChange={(e) => setCompanyConfig({...companyConfig, phone: e.target.value})}
                      placeholder="+55 11 99999-9999"
                    />
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="company-email">Email</Label>
                  <Input
                    id="company-email"
                    type="email"
                    value={companyConfig.email}
                    onChange={(e) => setCompanyConfig({...companyConfig, email: e.target.value})}
                    placeholder="contato@empresa.com"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="company-website">Website</Label>
                  <Input
                    id="company-website"
                    value={companyConfig.website}
                    onChange={(e) => setCompanyConfig({...companyConfig, website: e.target.value})}
                    placeholder="https://empresa.com"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="company-description">Descrição</Label>
                <Textarea
                  id="company-description"
                  value={companyConfig.description}
                  onChange={(e) => setCompanyConfig({...companyConfig, description: e.target.value})}
                  placeholder="Descreva sua empresa e serviços"
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="company-address">Endereço</Label>
                <Input
                  id="company-address"
                  value={companyConfig.address}
                  onChange={(e) => setCompanyConfig({...companyConfig, address: e.target.value})}
                  placeholder="Endereço completo"
                />
              </div>

              <Button
                onClick={() => handleSave('empresa')}
                disabled={saving}
                className="w-full md:w-auto"
              >
                <Save className="h-4 w-4 mr-2" />
                {saving ? 'Salvando...' : 'Salvar Configurações'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Bot Tab */}
        <TabsContent value="bot" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center space-x-2">
                <Bot className="h-5 w-5 text-green-600" />
                <CardTitle>Configurações do Bot</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="bot-name">Nome do Bot</Label>
                  <Input
                    id="bot-name"
                    value={botConfig.name}
                    onChange={(e) => setBotConfig({...botConfig, name: e.target.value})}
                    placeholder="Assistente Virtual"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="response-delay">Delay de Resposta (segundos)</Label>
                  <Input
                    id="response-delay"
                    type="number"
                    min="0"
                    max="10"
                    value={botConfig.responseDelay}
                    onChange={(e) => setBotConfig({...botConfig, responseDelay: parseInt(e.target.value)})}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="welcome-message">Mensagem de Boas-vindas</Label>
                <Textarea
                  id="welcome-message"
                  value={botConfig.welcomeMessage}
                  onChange={(e) => setBotConfig({...botConfig, welcomeMessage: e.target.value})}
                  placeholder="Mensagem que será enviada quando o usuário iniciar conversa"
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="default-response">Resposta Padrão</Label>
                <Textarea
                  id="default-response"
                  value={botConfig.defaultResponse}
                  onChange={(e) => setBotConfig({...botConfig, defaultResponse: e.target.value})}
                  placeholder="Mensagem quando o bot não entender"
                  rows={2}
                />
              </div>

              <div className="space-y-4">
                <h3 className="text-lg font-semibold flex items-center">
                  <Zap className="h-5 w-5 mr-2 text-yellow-600" />
                  Configurações de IA
                </h3>

                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Label>IA Habilitada</Label>
                    <p className="text-sm text-gray-600">Permite respostas inteligentes automáticas</p>
                  </div>
                  <Switch
                    checked={botConfig.aiEnabled}
                    onCheckedChange={(checked) => setBotConfig({...botConfig, aiEnabled: checked})}
                  />
                </div>

                {botConfig.aiEnabled && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <Label htmlFor="max-tokens">Máximo de Tokens</Label>
                      <Input
                        id="max-tokens"
                        type="number"
                        min="50"
                        max="500"
                        value={botConfig.maxTokens}
                        onChange={(e) => setBotConfig({...botConfig, maxTokens: parseInt(e.target.value)})}
                      />
                      <p className="text-xs text-gray-600">Controla o tamanho das respostas</p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="temperature">Criatividade (Temperature)</Label>
                      <Input
                        id="temperature"
                        type="number"
                        min="0"
                        max="1"
                        step="0.1"
                        value={botConfig.temperature}
                        onChange={(e) => setBotConfig({...botConfig, temperature: parseFloat(e.target.value)})}
                      />
                      <p className="text-xs text-gray-600">0 = mais conservador, 1 = mais criativo</p>
                    </div>
                  </div>
                )}
              </div>

              <Button
                onClick={() => handleSave('bot')}
                disabled={saving}
                className="w-full md:w-auto"
              >
                <Save className="h-4 w-4 mr-2" />
                {saving ? 'Salvando...' : 'Salvar Configurações'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Horários Tab */}
        <TabsContent value="horarios" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center space-x-2">
                <Clock className="h-5 w-5 text-orange-600" />
                <CardTitle>Horários de Funcionamento</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Dias de Trabalho</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(workDayLabels).map(([day, label]) => (
                    <div key={day} className="flex items-center space-x-2">
                      <Switch
                        id={day}
                        checked={scheduleConfig.workDays.includes(day)}
                        onCheckedChange={(checked) => {
                          if (checked) {
                            setScheduleConfig({
                              ...scheduleConfig,
                              workDays: [...scheduleConfig.workDays, day]
                            });
                          } else {
                            setScheduleConfig({
                              ...scheduleConfig,
                              workDays: scheduleConfig.workDays.filter(d => d !== day)
                            });
                          }
                        }}
                      />
                      <Label htmlFor={day}>{label}</Label>
                    </div>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="start-time">Horário de Início</Label>
                  <Input
                    id="start-time"
                    type="time"
                    value={scheduleConfig.startTime}
                    onChange={(e) => setScheduleConfig({...scheduleConfig, startTime: e.target.value})}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="end-time">Horário de Término</Label>
                  <Input
                    id="end-time"
                    type="time"
                    value={scheduleConfig.endTime}
                    onChange={(e) => setScheduleConfig({...scheduleConfig, endTime: e.target.value})}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="lunch-start">Início do Almoço</Label>
                  <Input
                    id="lunch-start"
                    type="time"
                    value={scheduleConfig.lunchStart}
                    onChange={(e) => setScheduleConfig({...scheduleConfig, lunchStart: e.target.value})}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="lunch-end">Fim do Almoço</Label>
                  <Input
                    id="lunch-end"
                    type="time"
                    value={scheduleConfig.lunchEnd}
                    onChange={(e) => setScheduleConfig({...scheduleConfig, lunchEnd: e.target.value})}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="timezone">Fuso Horário</Label>
                <Select
                  value={scheduleConfig.timezone}
                  onValueChange={(value) => setScheduleConfig({...scheduleConfig, timezone: value})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione o fuso horário" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="America/Sao_Paulo">São Paulo (GMT-3)</SelectItem>
                    <SelectItem value="America/Rio_Branco">Rio Branco (GMT-5)</SelectItem>
                    <SelectItem value="America/Manaus">Manaus (GMT-4)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Button
                onClick={() => handleSave('horarios')}
                disabled={saving}
                className="w-full md:w-auto"
              >
                <Save className="h-4 w-4 mr-2" />
                {saving ? 'Salvando...' : 'Salvar Configurações'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notificações Tab */}
        <TabsContent value="notificacoes" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center space-x-2">
                <MessageSquare className="h-5 w-5 text-purple-600" />
                <CardTitle>Configurações de Notificações</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Label>Notificações por Email</Label>
                    <p className="text-sm text-gray-600">Receber notificações importantes por email</p>
                  </div>
                  <Switch
                    checked={notificationConfig.emailNotifications}
                    onCheckedChange={(checked) => setNotificationConfig({...notificationConfig, emailNotifications: checked})}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Label>Notificações SMS</Label>
                    <p className="text-sm text-gray-600">Receber alertas por SMS</p>
                  </div>
                  <Switch
                    checked={notificationConfig.smsNotifications}
                    onCheckedChange={(checked) => setNotificationConfig({...notificationConfig, smsNotifications: checked})}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Label>Notificações Push</Label>
                    <p className="text-sm text-gray-600">Notificações no navegador/app</p>
                  </div>
                  <Switch
                    checked={notificationConfig.pushNotifications}
                    onCheckedChange={(checked) => setNotificationConfig({...notificationConfig, pushNotifications: checked})}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Label>Lembretes de Agendamento</Label>
                    <p className="text-sm text-gray-600">Avisos sobre próximos agendamentos</p>
                  </div>
                  <Switch
                    checked={notificationConfig.appointmentReminders}
                    onCheckedChange={(checked) => setNotificationConfig({...notificationConfig, appointmentReminders: checked})}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Label>Alertas de Novas Mensagens</Label>
                    <p className="text-sm text-gray-600">Notificações quando receber mensagens</p>
                  </div>
                  <Switch
                    checked={notificationConfig.newMessageAlerts}
                    onCheckedChange={(checked) => setNotificationConfig({...notificationConfig, newMessageAlerts: checked})}
                  />
                </div>
              </div>

              <Button
                onClick={() => handleSave('notificacoes')}
                disabled={saving}
                className="w-full md:w-auto"
              >
                <Save className="h-4 w-4 mr-2" />
                {saving ? 'Salvando...' : 'Salvar Configurações'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Segurança Tab */}
        <TabsContent value="seguranca" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center space-x-2">
                <Shield className="h-5 w-5 text-red-600" />
                <CardTitle>Configurações de Segurança</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  As configurações de segurança são críticas. Alterações podem afetar o acesso ao sistema.
                </AlertDescription>
              </Alert>

              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Alterar Senha</Label>
                  <Input type="password" placeholder="Nova senha" />
                  <Input type="password" placeholder="Confirmar nova senha" />
                </div>

                <div className="space-y-2">
                  <Label>Configurações de Sessão</Label>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="session-timeout">Timeout da Sessão (minutos)</Label>
                      <Input id="session-timeout" type="number" defaultValue="30" />
                    </div>
                    <div>
                      <Label htmlFor="max-attempts">Máximo de Tentativas de Login</Label>
                      <Input id="max-attempts" type="number" defaultValue="5" />
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Label>Autenticação de Dois Fatores</Label>
                    <p className="text-sm text-gray-600">Adiciona uma camada extra de segurança</p>
                  </div>
                  <Switch />
                </div>
              </div>

              <Button
                onClick={() => handleSave('seguranca')}
                disabled={saving}
                variant="destructive"
                className="w-full md:w-auto"
              >
                <Save className="h-4 w-4 mr-2" />
                {saving ? 'Salvando...' : 'Salvar Configurações de Segurança'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

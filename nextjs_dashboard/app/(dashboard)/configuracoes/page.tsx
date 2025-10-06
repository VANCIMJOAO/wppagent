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
import { debugLog } from '@/lib/debug';

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

        // Carregar configurações da empresa
        const companyResponse = await fetch('/api/config/company');
        if (companyResponse.ok) {
          const companyData = await companyResponse.json();
          if (companyData.success) {
            setCompanyConfig({
              name: companyData.data.name || '',
              description: companyData.data.description || '',
              phone: companyData.data.phone || '',
              email: companyData.data.email || '',
              website: companyData.data.website || '',
              address: companyData.data.address || ''
            });
          }
        }

        // Carregar configurações do bot
        const botResponse = await fetch('/api/config/bot');
        if (botResponse.ok) {
          const botData = await botResponse.json();
          if (botData.success) {
            setBotConfig({
              name: botData.data.name || 'Assistente Virtual',
              welcomeMessage: botData.data.welcomeMessage || 'Olá! Como posso ajudar você hoje?',
              defaultResponse: botData.data.defaultResponse || 'Desculpe, não entendi sua mensagem. Pode reformular?',
              aiEnabled: botData.data.aiEnabled || false,
              responseDelay: botData.data.responseDelay || 2,
              maxTokens: botData.data.maxTokens || 150,
              temperature: botData.data.temperature || 0.7
            });
          }
        }

        // Carregar configurações de horários
        const scheduleResponse = await fetch('/api/config/schedule');
        if (scheduleResponse.ok) {
          const scheduleData = await scheduleResponse.json();
          if (scheduleData.success) {
            setScheduleConfig({
              workDays: scheduleData.data.workDays || ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
              startTime: scheduleData.data.startTime || '09:00',
              endTime: scheduleData.data.endTime || '18:00',
              lunchStart: scheduleData.data.lunchStart || '12:00',
              lunchEnd: scheduleData.data.lunchEnd || '13:00',
              timezone: scheduleData.data.timezone || 'America/Sao_Paulo'
            });
          }
        }

        // Carregar configurações de notificações
        const notificationResponse = await fetch('/api/config/notifications');
        if (notificationResponse.ok) {
          const notificationData = await notificationResponse.json();
          if (notificationData.success) {
            setNotificationConfig({
              emailNotifications: notificationData.data.emailNotifications || false,
              smsNotifications: notificationData.data.smsNotifications || false,
              pushNotifications: notificationData.data.pushNotifications || false,
              appointmentReminders: notificationData.data.appointmentReminders || false,
              newMessageAlerts: notificationData.data.newMessageAlerts || false
            });
          }
        }

      } catch (error) {
        debugLog.error('Erro ao carregar configurações:', error);
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

      let response;
      let endpoint = '';
      let data = {};

      // Determinar endpoint e dados baseado no tipo de configuração
      switch (configType) {
        case 'empresa':
          endpoint = '/api/config/company';
          data = companyConfig;
          break;
        case 'bot':
          endpoint = '/api/config/bot';
          data = botConfig;
          break;
        case 'horarios':
          endpoint = '/api/config/schedule';
          data = scheduleConfig;
          break;
        case 'notificacoes':
          endpoint = '/api/config/notifications';
          data = notificationConfig;
          break;
        case 'seguranca':
          endpoint = '/api/config/security';
          data = {
            sessionTimeout: 30,
            maxLoginAttempts: 5,
            twoFactorEnabled: false
          };
          break;
        default:
          throw new Error('Tipo de configuração inválido');
      }

      // Fazer requisição para a API
      response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Erro ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.error || 'Erro ao salvar configurações');
      }

      toast.success(result.message || 'Configurações salvas com sucesso!');
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (error) {
      debugLog.error('Erro ao salvar configurações:', error);
      toast.error(error instanceof Error ? error.message : 'Erro ao salvar configurações');
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
    <div className="space-y-8 p-6 bg-gradient-to-br from-gray-50 to-white min-h-screen">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-4xl font-bold text-gray-900 tracking-tight">Configurações</h1>
          <p className="text-gray-600 mt-2 text-lg">Configurações do sistema e personalização</p>
        </div>
        {saved && (
          <Alert className="w-auto border-green-200 bg-green-50">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-700 font-medium">
              Configurações salvas com sucesso!
            </AlertDescription>
          </Alert>
        )}
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-6 bg-white p-1.5 rounded-xl shadow-md">
          <TabsTrigger 
            value="empresa" 
            className="flex items-center gap-2 data-[state=active]:bg-gradient-to-r data-[state=active]:from-primary data-[state=active]:to-primary/90 data-[state=active]:text-white data-[state=active]:shadow-md transition-all duration-200 rounded-lg font-semibold"
          >
            <Building2 className="h-4 w-4" />
            <span>Empresa</span>
          </TabsTrigger>
          <TabsTrigger 
            value="bot" 
            className="flex items-center gap-2 data-[state=active]:bg-gradient-to-r data-[state=active]:from-primary data-[state=active]:to-primary/90 data-[state=active]:text-white data-[state=active]:shadow-md transition-all duration-200 rounded-lg font-semibold"
          >
            <Bot className="h-4 w-4" />
            <span>Bot & IA</span>
          </TabsTrigger>
          <TabsTrigger 
            value="horarios" 
            className="flex items-center gap-2 data-[state=active]:bg-gradient-to-r data-[state=active]:from-primary data-[state=active]:to-primary/90 data-[state=active]:text-white data-[state=active]:shadow-md transition-all duration-200 rounded-lg font-semibold"
          >
            <Clock className="h-4 w-4" />
            <span>Horários</span>
          </TabsTrigger>
          <TabsTrigger 
            value="notificacoes" 
            className="flex items-center gap-2 data-[state=active]:bg-gradient-to-r data-[state=active]:from-primary data-[state=active]:to-primary/90 data-[state=active]:text-white data-[state=active]:shadow-md transition-all duration-200 rounded-lg font-semibold"
          >
            <MessageSquare className="h-4 w-4" />
            <span>Notificações</span>
          </TabsTrigger>
          <TabsTrigger 
            value="seguranca" 
            className="flex items-center gap-2 data-[state=active]:bg-gradient-to-r data-[state=active]:from-primary data-[state=active]:to-primary/90 data-[state=active]:text-white data-[state=active]:shadow-md transition-all duration-200 rounded-lg font-semibold"
          >
            <Shield className="h-4 w-4" />
            <span>Segurança</span>
          </TabsTrigger>
          <TabsTrigger 
            value="lgpd" 
            className="flex items-center gap-2 data-[state=active]:bg-gradient-to-r data-[state=active]:from-primary data-[state=active]:to-primary/90 data-[state=active]:text-white data-[state=active]:shadow-md transition-all duration-200 rounded-lg font-semibold"
          >
            <FileText className="h-4 w-4" />
            <span>LGPD</span>
          </TabsTrigger>
        </TabsList>

        {/* Empresa Tab */}
        <TabsContent value="empresa" className="space-y-6 mt-6">
          <Card className="border-0 shadow-xl bg-gradient-to-br from-white to-gray-50">
            <CardHeader className="border-b bg-gradient-to-r from-gray-50 to-transparent pb-5">
              <CardTitle className="flex items-center gap-3 text-2xl font-bold">
                <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg">
                  <Building2 className="h-5 w-5 text-white" />
                </div>
                Informações da Empresa
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6 p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-3">
                  <Label htmlFor="company-name" className="font-semibold text-gray-700">Nome da Empresa</Label>
                  {loading ? (
                    <Skeleton className="h-11 w-full" />
                  ) : (
                    <Input
                      id="company-name"
                      value={companyConfig.name}
                      onChange={(e) => setCompanyConfig({...companyConfig, name: e.target.value})}
                      placeholder="Nome da sua empresa"
                      className="h-11 border-gray-300 focus:ring-2 focus:ring-primary/20"
                    />
                  )}
                </div>

                <div className="space-y-3">
                  <Label htmlFor="company-phone" className="font-semibold text-gray-700">Telefone</Label>
                  {loading ? (
                    <Skeleton className="h-11 w-full" />
                  ) : (
                    <Input
                      id="company-phone"
                      value={companyConfig.phone}
                      onChange={(e) => setCompanyConfig({...companyConfig, phone: e.target.value})}
                      placeholder="+55 11 99999-9999"
                      className="h-11 border-gray-300 focus:ring-2 focus:ring-primary/20"
                    />
                  )}
                </div>

                <div className="space-y-3">
                  <Label htmlFor="company-email" className="font-semibold text-gray-700">Email</Label>
                  <Input
                    id="company-email"
                    type="email"
                    value={companyConfig.email}
                    onChange={(e) => setCompanyConfig({...companyConfig, email: e.target.value})}
                    placeholder="contato@whatsappagent.com"
                    className="h-11 border-gray-300 focus:ring-2 focus:ring-primary/20"
                  />
                </div>

                <div className="space-y-3">
                  <Label htmlFor="company-website" className="font-semibold text-gray-700">Website</Label>
                  <Input
                    id="company-website"
                    value={companyConfig.website}
                    onChange={(e) => setCompanyConfig({...companyConfig, website: e.target.value})}
                    placeholder="https://empresa.com"
                    className="h-11 border-gray-300 focus:ring-2 focus:ring-primary/20"
                  />
                </div>
              </div>

              <div className="space-y-3">
                <Label htmlFor="company-description" className="font-semibold text-gray-700">Descrição</Label>
                <Textarea
                  id="company-description"
                  value={companyConfig.description}
                  onChange={(e) => setCompanyConfig({...companyConfig, description: e.target.value})}
                  placeholder="Sistema de automação e agendamento para WhatsApp - Teste"
                  rows={4}
                  className="border-gray-300 focus:ring-2 focus:ring-primary/20 resize-none"
                />
              </div>

              <div className="space-y-3">
                <Label htmlFor="company-address" className="font-semibold text-gray-700">Endereço</Label>
                <Input
                  id="company-address"
                  value={companyConfig.address}
                  onChange={(e) => setCompanyConfig({...companyConfig, address: e.target.value})}
                  placeholder="São Paulo, SP, Brasil"
                  className="h-11 border-gray-300 focus:ring-2 focus:ring-primary/20"
                />
              </div>

              <Button
                onClick={() => handleSave('empresa')}
                disabled={saving}
                className="h-11 px-6 bg-gradient-to-r from-primary to-primary/90 shadow-md hover:shadow-lg transition-all hover:scale-105 font-semibold"
              >
                <Save className="h-4 w-4 mr-2" />
                {saving ? 'Salvando...' : 'Salvar Configurações'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Bot Tab */}
        <TabsContent value="bot" className="space-y-6 mt-6">
          <Card className="border-0 shadow-xl bg-gradient-to-br from-white to-gray-50">
            <CardHeader className="border-b bg-gradient-to-r from-gray-50 to-transparent pb-5">
              <CardTitle className="flex items-center gap-3 text-2xl font-bold">
                <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-green-500 to-emerald-600 shadow-lg">
                  <Bot className="h-5 w-5 text-white" />
                </div>
                Configurações do Bot
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6 p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-3">
                  <Label htmlFor="bot-name" className="font-semibold text-gray-700">Nome do Bot</Label>
                  <Input
                    id="bot-name"
                    value={botConfig.name}
                    onChange={(e) => setBotConfig({...botConfig, name: e.target.value})}
                    placeholder="Assistente Virtual"
                    className="h-11 border-gray-300 focus:ring-2 focus:ring-primary/20"
                  />
                </div>

                <div className="space-y-3">
                  <Label htmlFor="response-delay" className="font-semibold text-gray-700">Delay de Resposta (segundos)</Label>
                  <Input
                    id="response-delay"
                    type="number"
                    min="0"
                    max="10"
                    value={botConfig.responseDelay}
                    onChange={(e) => setBotConfig({...botConfig, responseDelay: parseInt(e.target.value)})}
                    className="h-11 border-gray-300 focus:ring-2 focus:ring-primary/20"
                  />
                </div>
              </div>

              <div className="space-y-3">
                <Label htmlFor="welcome-message" className="font-semibold text-gray-700">Mensagem de Boas-vindas</Label>
                <Textarea
                  id="welcome-message"
                  value={botConfig.welcomeMessage}
                  onChange={(e) => setBotConfig({...botConfig, welcomeMessage: e.target.value})}
                  placeholder="Mensagem que será enviada quando o usuário iniciar conversa"
                  rows={3}
                  className="border-gray-300 focus:ring-2 focus:ring-primary/20 resize-none"
                />
              </div>

              <div className="space-y-3">
                <Label htmlFor="default-response" className="font-semibold text-gray-700">Resposta Padrão</Label>
                <Textarea
                  id="default-response"
                  value={botConfig.defaultResponse}
                  onChange={(e) => setBotConfig({...botConfig, defaultResponse: e.target.value})}
                  placeholder="Mensagem quando o bot não entender"
                  rows={3}
                  className="border-gray-300 focus:ring-2 focus:ring-primary/20 resize-none"
                />
              </div>

              <div className="space-y-6 pt-4 border-t">
                <h3 className="text-xl font-bold flex items-center gap-2">
                  <Zap className="h-6 w-6 text-yellow-600" />
                  Configurações de IA
                </h3>

                <div className="flex items-center justify-between p-5 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-200">
                  <div className="space-y-1">
                    <Label className="font-bold text-gray-900">IA Habilitada</Label>
                    <p className="text-sm text-gray-600 font-medium">Permite respostas inteligentes automáticas</p>
                  </div>
                  <Switch
                    checked={botConfig.aiEnabled}
                    onCheckedChange={(checked) => setBotConfig({...botConfig, aiEnabled: checked})}
                  />
                </div>

                {botConfig.aiEnabled && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-3">
                      <Label htmlFor="max-tokens" className="font-semibold text-gray-700">Máximo de Tokens</Label>
                      <Input
                        id="max-tokens"
                        type="number"
                        min="50"
                        max="500"
                        value={botConfig.maxTokens}
                        onChange={(e) => setBotConfig({...botConfig, maxTokens: parseInt(e.target.value)})}
                        className="h-11 border-gray-300 focus:ring-2 focus:ring-primary/20"
                      />
                      <p className="text-xs text-gray-600 font-medium">Controla o tamanho das respostas</p>
                    </div>

                    <div className="space-y-3">
                      <Label htmlFor="temperature" className="font-semibold text-gray-700">Criatividade (Temperature)</Label>
                      <Input
                        id="temperature"
                        type="number"
                        min="0"
                        max="1"
                        step="0.1"
                        value={botConfig.temperature}
                        onChange={(e) => setBotConfig({...botConfig, temperature: parseFloat(e.target.value)})}
                        className="h-11 border-gray-300 focus:ring-2 focus:ring-primary/20"
                      />
                      <p className="text-xs text-gray-600 font-medium">0 = mais conservador, 1 = mais criativo</p>
                    </div>
                  </div>
                )}
              </div>

              <Button
                onClick={() => handleSave('bot')}
                disabled={saving}
                className="h-11 px-6 bg-gradient-to-r from-primary to-primary/90 shadow-md hover:shadow-lg transition-all hover:scale-105 font-semibold"
              >
                <Save className="h-4 w-4 mr-2" />
                {saving ? 'Salvando...' : 'Salvar Configurações'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Horários Tab */}
        <TabsContent value="horarios" className="space-y-6 mt-6">
          <Card className="border-0 shadow-xl bg-gradient-to-br from-white to-gray-50">
            <CardHeader className="border-b bg-gradient-to-r from-gray-50 to-transparent pb-5">
              <CardTitle className="flex items-center gap-3 text-2xl font-bold">
                <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-orange-500 to-red-600 shadow-lg">
                  <Clock className="h-5 w-5 text-white" />
                </div>
                Horários de Funcionamento
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6 p-6">
              <div className="space-y-5">
                <h3 className="text-xl font-bold text-gray-900">Dias de Trabalho</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(workDayLabels).map(([day, label]) => (
                    <div key={day} className="flex items-center gap-3 p-4 rounded-lg bg-gradient-to-r from-gray-50 to-white border hover:border-primary/50 transition-all">
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
                      <Label htmlFor={day} className="font-semibold text-gray-700 cursor-pointer">{label}</Label>
                    </div>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-3">
                  <Label htmlFor="start-time" className="font-semibold text-gray-700">Horário de Início</Label>
                  <Input
                    id="start-time"
                    type="time"
                    value={scheduleConfig.startTime}
                    onChange={(e) => setScheduleConfig({...scheduleConfig, startTime: e.target.value})}
                    className="h-11 border-gray-300 focus:ring-2 focus:ring-primary/20"
                  />
                </div>

                <div className="space-y-3">
                  <Label htmlFor="end-time" className="font-semibold text-gray-700">Horário de Término</Label>
                  <Input
                    id="end-time"
                    type="time"
                    value={scheduleConfig.endTime}
                    onChange={(e) => setScheduleConfig({...scheduleConfig, endTime: e.target.value})}
                    className="h-11 border-gray-300 focus:ring-2 focus:ring-primary/20"
                  />
                </div>

                <div className="space-y-3">
                  <Label htmlFor="lunch-start" className="font-semibold text-gray-700">Início do Almoço</Label>
                  <Input
                    id="lunch-start"
                    type="time"
                    value={scheduleConfig.lunchStart}
                    onChange={(e) => setScheduleConfig({...scheduleConfig, lunchStart: e.target.value})}
                    className="h-11 border-gray-300 focus:ring-2 focus:ring-primary/20"
                  />
                </div>

                <div className="space-y-3">
                  <Label htmlFor="lunch-end" className="font-semibold text-gray-700">Fim do Almoço</Label>
                  <Input
                    id="lunch-end"
                    type="time"
                    value={scheduleConfig.lunchEnd}
                    onChange={(e) => setScheduleConfig({...scheduleConfig, lunchEnd: e.target.value})}
                    className="h-11 border-gray-300 focus:ring-2 focus:ring-primary/20"
                  />
                </div>
              </div>

              <div className="space-y-3">
                <Label htmlFor="timezone" className="font-semibold text-gray-700">Fuso Horário</Label>
                <Select
                  value={scheduleConfig.timezone}
                  onValueChange={(value) => setScheduleConfig({...scheduleConfig, timezone: value})}
                >
                  <SelectTrigger className="h-11 border-gray-300">
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
                className="h-11 px-6 bg-gradient-to-r from-primary to-primary/90 shadow-md hover:shadow-lg transition-all hover:scale-105 font-semibold"
              >
                <Save className="h-4 w-4 mr-2" />
                {saving ? 'Salvando...' : 'Salvar Configurações'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notificações Tab */}
        <TabsContent value="notificacoes" className="space-y-6 mt-6">
          <Card className="border-0 shadow-xl bg-gradient-to-br from-white to-gray-50">
            <CardHeader className="border-b bg-gradient-to-r from-gray-50 to-transparent pb-5">
              <CardTitle className="flex items-center gap-3 text-2xl font-bold">
                <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-pink-600 shadow-lg">
                  <MessageSquare className="h-5 w-5 text-white" />
                </div>
                Configurações de Notificações
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6 p-6">
              <div className="space-y-5">
                <div className="flex items-center justify-between p-5 rounded-xl bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200">
                  <div className="space-y-1">
                    <Label className="font-bold text-gray-900">Notificações por Email</Label>
                    <p className="text-sm text-gray-600 font-medium">Receber notificações importantes por email</p>
                  </div>
                  <Switch
                    checked={notificationConfig.emailNotifications}
                    onCheckedChange={(checked) => setNotificationConfig({...notificationConfig, emailNotifications: checked})}
                  />
                </div>

                <div className="flex items-center justify-between p-5 rounded-xl bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200">
                  <div className="space-y-1">
                    <Label className="font-bold text-gray-900">Notificações SMS</Label>
                    <p className="text-sm text-gray-600 font-medium">Receber alertas por SMS</p>
                  </div>
                  <Switch
                    checked={notificationConfig.smsNotifications}
                    onCheckedChange={(checked) => setNotificationConfig({...notificationConfig, smsNotifications: checked})}
                  />
                </div>

                <div className="flex items-center justify-between p-5 rounded-xl bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200">
                  <div className="space-y-1">
                    <Label className="font-bold text-gray-900">Notificações Push</Label>
                    <p className="text-sm text-gray-600 font-medium">Notificações no navegador/app</p>
                  </div>
                  <Switch
                    checked={notificationConfig.pushNotifications}
                    onCheckedChange={(checked) => setNotificationConfig({...notificationConfig, pushNotifications: checked})}
                  />
                </div>

                <div className="flex items-center justify-between p-5 rounded-xl bg-gradient-to-r from-orange-50 to-red-50 border border-orange-200">
                  <div className="space-y-1">
                    <Label className="font-bold text-gray-900">Lembretes de Agendamento</Label>
                    <p className="text-sm text-gray-600 font-medium">Avisos sobre próximos agendamentos</p>
                  </div>
                  <Switch
                    checked={notificationConfig.appointmentReminders}
                    onCheckedChange={(checked) => setNotificationConfig({...notificationConfig, appointmentReminders: checked})}
                  />
                </div>

                <div className="flex items-center justify-between p-5 rounded-xl bg-gradient-to-r from-yellow-50 to-amber-50 border border-yellow-200">
                  <div className="space-y-1">
                    <Label className="font-bold text-gray-900">Alertas de Novas Mensagens</Label>
                    <p className="text-sm text-gray-600 font-medium">Notificações quando receber mensagens</p>
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
                className="h-11 px-6 bg-gradient-to-r from-primary to-primary/90 shadow-md hover:shadow-lg transition-all hover:scale-105 font-semibold"
              >
                <Save className="h-4 w-4 mr-2" />
                {saving ? 'Salvando...' : 'Salvar Configurações'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Segurança Tab */}
        <TabsContent value="seguranca" className="space-y-6 mt-6">
          <Card className="border-0 shadow-xl bg-gradient-to-br from-white to-gray-50">
            <CardHeader className="border-b bg-gradient-to-r from-gray-50 to-transparent pb-5">
              <CardTitle className="flex items-center gap-3 text-2xl font-bold">
                <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-red-500 to-red-600 shadow-lg">
                  <Shield className="h-5 w-5 text-white" />
                </div>
                Configurações de Segurança
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6 p-6">
              <Alert className="border-red-200 bg-red-50">
                <AlertCircle className="h-5 w-5 text-red-600" />
                <AlertDescription className="text-red-700 font-medium">
                  As configurações de segurança são críticas. Alterações podem afetar o acesso ao sistema.
                </AlertDescription>
              </Alert>

              <div className="space-y-6">
                <div className="space-y-4">
                  <Label className="font-bold text-gray-900 text-lg">Alterar Senha</Label>
                  <Input type="password" placeholder="Nova senha" className="h-11 border-gray-300 focus:ring-2 focus:ring-primary/20" />
                  <Input type="password" placeholder="Confirmar nova senha" className="h-11 border-gray-300 focus:ring-2 focus:ring-primary/20" />
                </div>

                <div className="space-y-4">
                  <Label className="font-bold text-gray-900 text-lg">Configurações de Sessão</Label>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-3">
                      <Label htmlFor="session-timeout" className="font-semibold text-gray-700">Timeout da Sessão (minutos)</Label>
                      <Input 
                        id="session-timeout" 
                        type="number" 
                        defaultValue="30" 
                        className="h-11 border-gray-300 focus:ring-2 focus:ring-primary/20"
                      />
                    </div>
                    <div className="space-y-3">
                      <Label htmlFor="max-attempts" className="font-semibold text-gray-700">Máximo de Tentativas de Login</Label>
                      <Input 
                        id="max-attempts" 
                        type="number" 
                        defaultValue="5" 
                        className="h-11 border-gray-300 focus:ring-2 focus:ring-primary/20"
                      />
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between p-5 rounded-xl bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200">
                  <div className="space-y-1">
                    <Label className="font-bold text-gray-900">Autenticação de Dois Fatores</Label>
                    <p className="text-sm text-gray-600 font-medium">Adiciona uma camada extra de segurança</p>
                  </div>
                  <Switch />
                </div>
              </div>

              <Button
                onClick={() => handleSave('seguranca')}
                disabled={saving}
                className="h-11 px-6 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 shadow-md hover:shadow-lg transition-all hover:scale-105 font-semibold"
              >
                <Shield className="h-4 w-4 mr-2" />
                {saving ? 'Salvando...' : 'Salvar Configurações de Segurança'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* LGPD Tab */}
        <TabsContent value="lgpd" className="space-y-6 mt-6">
          <Card className="border-0 shadow-xl bg-gradient-to-br from-white to-gray-50">
            <CardHeader className="border-b bg-gradient-to-r from-gray-50 to-transparent pb-5">
              <CardTitle className="flex items-center gap-3 text-2xl font-bold">
                <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg">
                  <Shield className="h-5 w-5 text-white" />
                </div>
                LGPD - Proteção de Dados
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-8 p-6">
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-200">
                <h3 className="font-bold text-blue-900 mb-3 text-lg flex items-center gap-2">
                  <CheckCircle className="h-5 w-5" />
                  Sistema em Conformidade com a LGPD
                </h3>
                <p className="text-blue-800 font-medium leading-relaxed">
                  Nosso sistema está em conformidade com a Lei Geral de Proteção de Dados (Lei nº 13.709/2018). 
                  Você pode exercer seus direitos através da interface dedicada.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] bg-gradient-to-br from-white to-blue-50/30">
                  <CardContent className="p-6">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg">
                        <Shield className="w-6 h-6 text-white" />
                      </div>
                      <h4 className="font-bold text-gray-900 text-lg">Seus Direitos</h4>
                    </div>
                    <p className="text-sm text-gray-600 mb-5 font-medium leading-relaxed">
                      Acesse, exporte, corrija ou exclua seus dados pessoais conforme a LGPD.
                    </p>
                    <Button 
                      variant="outline" 
                      className="w-full h-11 hover:bg-blue-50 hover:text-blue-600 hover:border-blue-300 transition-all font-semibold"
                      onClick={() => window.location.href = '/configuracoes/lgpd'}
                    >
                      Acessar Interface LGPD
                    </Button>
                  </CardContent>
                </Card>

                <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] bg-gradient-to-br from-white to-green-50/30">
                  <CardContent className="p-6">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-gradient-to-br from-green-500 to-emerald-600 shadow-lg">
                        <FileText className="w-6 h-6 text-white" />
                      </div>
                      <h4 className="font-bold text-gray-900 text-lg">Política de Privacidade</h4>
                    </div>
                    <p className="text-sm text-gray-600 mb-5 font-medium leading-relaxed">
                      Consulte nossa política de privacidade e termos de uso.
                    </p>
                    <Button 
                      variant="outline" 
                      className="w-full h-11 hover:bg-green-50 hover:text-green-600 hover:border-green-300 transition-all font-semibold"
                      onClick={() => window.location.href = '/configuracoes/lgpd?tab=privacidade'}
                    >
                      Ver Política
                    </Button>
                  </CardContent>
                </Card>
              </div>

              <div className="bg-gradient-to-r from-gray-50 to-white p-6 rounded-xl border border-gray-200">
                <h4 className="font-bold mb-4 text-gray-900 text-lg">Funcionalidades Disponíveis</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
                    <span className="text-sm font-medium text-gray-700">Visualização de dados pessoais</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
                    <span className="text-sm font-medium text-gray-700">Portabilidade de dados (export)</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
                    <span className="text-sm font-medium text-gray-700">Exclusão de conta</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
                    <span className="text-sm font-medium text-gray-700">Informações sobre direitos</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

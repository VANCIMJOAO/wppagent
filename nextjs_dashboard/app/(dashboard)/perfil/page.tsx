"use client";

import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import {
  User,
  Mail,
  Phone,
  MapPin,
  Calendar,
  Shield,
  Bell,
  Lock,
  Camera,
  Save,
  Eye,
  EyeOff,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import { toast } from 'sonner';
import api from '@/lib/api-service';

interface UserProfile {
  id: string;
  name: string;
  email: string;
  phone: string;
  avatar?: string;
  role: string;
  company: string;
  address: string;
  joinedAt: string;
  lastActive: string;
  stats: {
    totalConversations: number;
    totalMessages: number;
    responseTime: string;
    customerSatisfaction: number;
  };
  preferences: {
    emailNotifications: boolean;
    pushNotifications: boolean;
    soundNotifications: boolean;
    autoReply: boolean;
    workingHours: {
      enabled: boolean;
      start: string;
      end: string;
    };
  };
}

const mockUser: UserProfile = {
  id: '1',
  name: 'João Silva',
  email: 'joao.silva@empresa.com',
  phone: '+55 11 99999-9999',
  role: 'Atendente',
  company: 'Empresa XYZ',
  address: 'São Paulo, SP',
  joinedAt: '2023-01-15',
  lastActive: '2024-01-20 14:30:00',
  stats: {
    totalConversations: 1250,
    totalMessages: 8430,
    responseTime: '2.5 min',
    customerSatisfaction: 4.8
  },
  preferences: {
    emailNotifications: true,
    pushNotifications: true,
    soundNotifications: false,
    autoReply: true,
    workingHours: {
      enabled: true,
      start: '09:00',
      end: '18:00'
    }
  }
};

export default function ProfilePage() {
  const [user, setUser] = useState<UserProfile>(mockUser);
  const [isEditing, setIsEditing] = useState(false);
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const [formData, setFormData] = useState({
    name: user.name,
    email: user.email,
    phone: user.phone,
    company: user.company,
    address: user.address
  });

  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handlePasswordChange = (field: string, value: string) => {
    setPasswordData(prev => ({ ...prev, [field]: value }));
  };

  const handlePreferenceChange = (field: string, value: boolean) => {
    setUser(prev => ({
      ...prev,
      preferences: { ...prev.preferences, [field]: value }
    }));
  };

  const handleWorkingHoursChange = (field: string, value: string | boolean) => {
    setUser(prev => ({
      ...prev,
      preferences: {
        ...prev.preferences,
        workingHours: { ...prev.preferences.workingHours, [field]: value }
      }
    }));
  };

  const saveProfile = () => {
    setUser(prev => ({ ...prev, ...formData }));
    setIsEditing(false);
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 3000);
  };

  const changePassword = () => {
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      alert('As senhas não coincidem!');
      return;
    }
    alert('Senha alterada com sucesso!');
    setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-purple-50/20">
      <div className="max-w-7xl mx-auto p-6 lg:p-8 space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent mb-3">
              Meu Perfil
            </h1>
            <p className="text-gray-600 text-lg">Gerencie suas informações pessoais e preferências</p>
          </div>
          <Badge 
            variant="outline" 
            className="text-green-700 bg-gradient-to-r from-green-50 to-emerald-50 border-green-300 px-4 py-2 text-base shadow-sm"
          >
            <CheckCircle className="w-4 h-4 mr-2" />
            Conta Ativa
          </Badge>
        </div>

        {saveSuccess && (
          <Alert className="bg-gradient-to-r from-green-50 to-emerald-50 border-green-300 shadow-lg">
            <CheckCircle className="h-5 w-5 text-green-600" />
            <AlertDescription className="text-green-800 text-base ml-2">
              Perfil atualizado com sucesso!
            </AlertDescription>
          </Alert>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="space-y-8">
            {/* Profile Card */}
            <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm hover:shadow-xl transition-all">
              <CardContent className="pt-8">
                <div className="flex flex-col items-center text-center">
                  <div className="relative">
                    <Avatar className="w-28 h-28 ring-4 ring-blue-100 shadow-lg">
                      <AvatarImage src={user.avatar} />
                      <AvatarFallback className="text-xl font-bold bg-gradient-to-br from-blue-500 to-purple-600 text-white">
                        {user.name.split(' ').map(n => n[0]).join('')}
                      </AvatarFallback>
                    </Avatar>
                    <Button
                      size="sm"
                      variant="outline"
                      className="absolute -bottom-3 left-1/2 transform -translate-x-1/2 rounded-full p-2.5 bg-white shadow-md hover:shadow-lg hover:scale-110 transition-all border-2"
                    >
                      <Camera className="w-4 h-4" />
                    </Button>
                  </div>

                  <h3 className="text-xl font-bold mt-6 mb-2">{user.name}</h3>
                  <p className="text-gray-600 text-base mb-3">{user.email}</p>
                  <Badge 
                    variant="secondary" 
                    className="bg-gradient-to-r from-blue-100 to-purple-100 text-blue-700 px-4 py-1.5 text-sm font-medium"
                  >
                    {user.role}
                  </Badge>
                </div>

                <div className="mt-8 space-y-4 text-base">
                  <div className="flex items-center text-gray-600 p-3 rounded-lg bg-gradient-to-r from-slate-50 to-gray-50 hover:shadow-sm transition-all">
                    <MapPin className="w-5 h-5 mr-3 text-blue-600" />
                    {user.address}
                  </div>
                  <div className="flex items-center text-gray-600 p-3 rounded-lg bg-gradient-to-r from-slate-50 to-gray-50 hover:shadow-sm transition-all">
                    <Calendar className="w-5 h-5 mr-3 text-purple-600" />
                    Membro desde {new Date(user.joinedAt).toLocaleDateString('pt-BR')}
                  </div>
                  <div className="flex items-center text-gray-600 p-3 rounded-lg bg-gradient-to-r from-slate-50 to-gray-50 hover:shadow-sm transition-all">
                    <Shield className="w-5 h-5 mr-3 text-green-600" />
                    Última atividade: {new Date(user.lastActive).toLocaleString('pt-BR')}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Statistics Card */}
            <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm hover:shadow-xl transition-all">
              <CardHeader className="bg-gradient-to-r from-blue-50 to-purple-50 pb-4">
                <CardTitle className="text-xl font-bold text-gray-900">Estatísticas</CardTitle>
              </CardHeader>
              <CardContent className="space-y-5 pt-6">
                <div className="flex justify-between items-center p-3 rounded-lg bg-gradient-to-r from-blue-50 to-cyan-50 hover:shadow-md transition-all group">
                  <span className="text-gray-700 font-medium text-base">Conversas</span>
                  <span className="font-bold text-lg text-blue-700 group-hover:scale-110 transition-transform">
                    {user.stats.totalConversations.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between items-center p-3 rounded-lg bg-gradient-to-r from-purple-50 to-pink-50 hover:shadow-md transition-all group">
                  <span className="text-gray-700 font-medium text-base">Mensagens</span>
                  <span className="font-bold text-lg text-purple-700 group-hover:scale-110 transition-transform">
                    {user.stats.totalMessages.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between items-center p-3 rounded-lg bg-gradient-to-r from-green-50 to-emerald-50 hover:shadow-md transition-all group">
                  <span className="text-gray-700 font-medium text-base">Tempo Resposta</span>
                  <span className="font-bold text-lg text-green-700 group-hover:scale-110 transition-transform">
                    {user.stats.responseTime}
                  </span>
                </div>
                <div className="flex justify-between items-center p-3 rounded-lg bg-gradient-to-r from-yellow-50 to-amber-50 hover:shadow-md transition-all group">
                  <span className="text-gray-700 font-medium text-base">Satisfação</span>
                  <div className="flex items-center">
                    <span className="font-bold text-lg text-yellow-700 group-hover:scale-110 transition-transform">
                      {user.stats.customerSatisfaction}
                    </span>
                    <span className="text-yellow-500 ml-2 text-lg">⭐</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="lg:col-span-2">
            <Tabs defaultValue="profile" className="space-y-8">
              <TabsList className="grid w-full grid-cols-3 p-1.5 bg-white/60 backdrop-blur-sm shadow-md h-14">
                <TabsTrigger 
                  value="profile"
                  className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-purple-600 data-[state=active]:text-white data-[state=active]:shadow-lg transition-all text-base font-medium"
                >
                  <User className="w-5 h-5 mr-2" />
                  Informações Pessoais
                </TabsTrigger>
                <TabsTrigger 
                  value="security"
                  className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-purple-600 data-[state=active]:text-white data-[state=active]:shadow-lg transition-all text-base font-medium"
                >
                  <Lock className="w-5 h-5 mr-2" />
                  Segurança
                </TabsTrigger>
                <TabsTrigger 
                  value="preferences"
                  className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-purple-600 data-[state=active]:text-white data-[state=active]:shadow-lg transition-all text-base font-medium"
                >
                  <Bell className="w-5 h-5 mr-2" />
                  Preferências
                </TabsTrigger>
              </TabsList>

              <TabsContent value="profile">
                <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
                  <CardHeader className="bg-gradient-to-r from-blue-50 to-purple-50 pb-5">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-xl font-bold text-gray-900">Informações Pessoais</CardTitle>
                      <Button
                        variant={isEditing ? "default" : "outline"}
                        onClick={() => isEditing ? saveProfile() : setIsEditing(true)}
                        className={isEditing ? "bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 shadow-md h-11 px-6 text-base" : "h-11 px-6 text-base"}
                      >
                        {isEditing ? (
                          <>
                            <Save className="w-5 h-5 mr-2" />
                            Salvar
                          </>
                        ) : (
                          'Editar'
                        )}
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-6 pt-8">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-2.5">
                        <Label htmlFor="name" className="text-base font-medium text-gray-700">Nome Completo</Label>
                        <Input
                          id="name"
                          value={formData.name}
                          onChange={(e) => handleInputChange('name', e.target.value)}
                          disabled={!isEditing}
                          className="h-12 text-base border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                        />
                      </div>

                      <div className="space-y-2.5">
                        <Label htmlFor="email" className="text-base font-medium text-gray-700">Email</Label>
                        <Input
                          id="email"
                          type="email"
                          value={formData.email}
                          onChange={(e) => handleInputChange('email', e.target.value)}
                          disabled={!isEditing}
                          className="h-12 text-base border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                        />
                      </div>

                      <div className="space-y-2.5">
                        <Label htmlFor="phone" className="text-base font-medium text-gray-700">Telefone</Label>
                        <Input
                          id="phone"
                          value={formData.phone}
                          onChange={(e) => handleInputChange('phone', e.target.value)}
                          disabled={!isEditing}
                          className="h-12 text-base border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                        />
                      </div>

                      <div className="space-y-2.5">
                        <Label htmlFor="company" className="text-base font-medium text-gray-700">Empresa</Label>
                        <Input
                          id="company"
                          value={formData.company}
                          onChange={(e) => handleInputChange('company', e.target.value)}
                          disabled={!isEditing}
                          className="h-12 text-base border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                        />
                      </div>

                      <div className="md:col-span-2 space-y-2.5">
                        <Label htmlFor="address" className="text-base font-medium text-gray-700">Endereço</Label>
                        <Input
                          id="address"
                          value={formData.address}
                          onChange={(e) => handleInputChange('address', e.target.value)}
                          disabled={!isEditing}
                          className="h-12 text-base border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="security">
                <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
                  <CardHeader className="bg-gradient-to-r from-blue-50 to-purple-50 pb-5">
                    <CardTitle className="text-xl font-bold text-gray-900 flex items-center">
                      <Shield className="w-6 h-6 mr-3 text-blue-600" />
                      Segurança da Conta
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-6 pt-8">
                    <div className="space-y-2.5">
                      <Label htmlFor="currentPassword" className="text-base font-medium text-gray-700">Senha Atual</Label>
                      <div className="relative">
                        <Input
                          id="currentPassword"
                          type={showCurrentPassword ? "text" : "password"}
                          value={passwordData.currentPassword}
                          onChange={(e) => handlePasswordChange('currentPassword', e.target.value)}
                          placeholder="Digite sua senha atual"
                          className="h-12 text-base border-gray-300 focus:border-blue-500 focus:ring-blue-500 pr-12"
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="absolute right-2 top-1/2 transform -translate-y-1/2 h-8 w-8 p-0 hover:bg-gray-100"
                          onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                        >
                          {showCurrentPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                        </Button>
                      </div>
                    </div>

                    <div className="space-y-2.5">
                      <Label htmlFor="newPassword" className="text-base font-medium text-gray-700">Nova Senha</Label>
                      <div className="relative">
                        <Input
                          id="newPassword"
                          type={showNewPassword ? "text" : "password"}
                          value={passwordData.newPassword}
                          onChange={(e) => handlePasswordChange('newPassword', e.target.value)}
                          placeholder="Digite uma nova senha"
                          className="h-12 text-base border-gray-300 focus:border-blue-500 focus:ring-blue-500 pr-12"
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="absolute right-2 top-1/2 transform -translate-y-1/2 h-8 w-8 p-0 hover:bg-gray-100"
                          onClick={() => setShowNewPassword(!showNewPassword)}
                        >
                          {showNewPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                        </Button>
                      </div>
                    </div>

                    <div className="space-y-2.5">
                      <Label htmlFor="confirmPassword" className="text-base font-medium text-gray-700">Confirmar Nova Senha</Label>
                      <div className="relative">
                        <Input
                          id="confirmPassword"
                          type={showConfirmPassword ? "text" : "password"}
                          value={passwordData.confirmPassword}
                          onChange={(e) => handlePasswordChange('confirmPassword', e.target.value)}
                          placeholder="Confirme a nova senha"
                          className="h-12 text-base border-gray-300 focus:border-blue-500 focus:ring-blue-500 pr-12"
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="absolute right-2 top-1/2 transform -translate-y-1/2 h-8 w-8 p-0 hover:bg-gray-100"
                          onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        >
                          {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                        </Button>
                      </div>
                    </div>

                    <Button
                      onClick={changePassword}
                      className="w-full md:w-auto bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 shadow-md h-12 px-8 text-base font-medium"
                      disabled={!passwordData.currentPassword || !passwordData.newPassword || !passwordData.confirmPassword}
                    >
                      <Lock className="w-5 h-5 mr-2" />
                      Alterar Senha
                    </Button>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="preferences" className="space-y-8">
                <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
                  <CardHeader className="bg-gradient-to-r from-blue-50 to-purple-50 pb-5">
                    <CardTitle className="text-xl font-bold text-gray-900 flex items-center">
                      <Bell className="w-6 h-6 mr-3 text-blue-600" />
                      Preferências de Notificação
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-8 pt-8">
                    <div className="flex items-center justify-between p-4 rounded-xl bg-gradient-to-r from-blue-50/50 to-cyan-50/50 hover:shadow-md transition-all">
                      <div className="space-y-1">
                        <Label className="text-base font-semibold text-gray-900">Notificações por Email</Label>
                        <p className="text-sm text-gray-600">Receber notificações no email</p>
                      </div>
                      <Switch
                        checked={user.preferences.emailNotifications}
                        onCheckedChange={(value) => handlePreferenceChange('emailNotifications', value)}
                        className="data-[state=checked]:bg-gradient-to-r data-[state=checked]:from-blue-600 data-[state=checked]:to-purple-600"
                      />
                    </div>

                    <div className="flex items-center justify-between p-4 rounded-xl bg-gradient-to-r from-purple-50/50 to-pink-50/50 hover:shadow-md transition-all">
                      <div className="space-y-1">
                        <Label className="text-base font-semibold text-gray-900">Notificações Push</Label>
                        <p className="text-sm text-gray-600">Receber notificações no navegador</p>
                      </div>
                      <Switch
                        checked={user.preferences.pushNotifications}
                        onCheckedChange={(value) => handlePreferenceChange('pushNotifications', value)}
                        className="data-[state=checked]:bg-gradient-to-r data-[state=checked]:from-blue-600 data-[state=checked]:to-purple-600"
                      />
                    </div>

                    <div className="flex items-center justify-between p-4 rounded-xl bg-gradient-to-r from-green-50/50 to-emerald-50/50 hover:shadow-md transition-all">
                      <div className="space-y-1">
                        <Label className="text-base font-semibold text-gray-900">Sons de Notificação</Label>
                        <p className="text-sm text-gray-600">Reproduzir sons para novas mensagens</p>
                      </div>
                      <Switch
                        checked={user.preferences.soundNotifications}
                        onCheckedChange={(value) => handlePreferenceChange('soundNotifications', value)}
                        className="data-[state=checked]:bg-gradient-to-r data-[state=checked]:from-blue-600 data-[state=checked]:to-purple-600"
                      />
                    </div>

                    <div className="flex items-center justify-between p-4 rounded-xl bg-gradient-to-r from-yellow-50/50 to-amber-50/50 hover:shadow-md transition-all">
                      <div className="space-y-1">
                        <Label className="text-base font-semibold text-gray-900">Resposta Automática</Label>
                        <p className="text-sm text-gray-600">Enviar respostas automáticas quando ausente</p>
                      </div>
                      <Switch
                        checked={user.preferences.autoReply}
                        onCheckedChange={(value) => handlePreferenceChange('autoReply', value)}
                        className="data-[state=checked]:bg-gradient-to-r data-[state=checked]:from-blue-600 data-[state=checked]:to-purple-600"
                      />
                    </div>
                  </CardContent>
                </Card>

                <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
                  <CardHeader className="bg-gradient-to-r from-blue-50 to-purple-50 pb-5">
                    <CardTitle className="text-xl font-bold text-gray-900 flex items-center">
                      <Calendar className="w-6 h-6 mr-3 text-blue-600" />
                      Horário de Trabalho
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-6 pt-8">
                    <div className="flex items-center justify-between p-4 rounded-xl bg-gradient-to-r from-blue-50/50 to-purple-50/50 hover:shadow-md transition-all">
                      <div className="space-y-1">
                        <Label className="text-base font-semibold text-gray-900">Ativar Horário de Trabalho</Label>
                        <p className="text-sm text-gray-600">Definir horários específicos para atendimento</p>
                      </div>
                      <Switch
                        checked={user.preferences.workingHours.enabled}
                        onCheckedChange={(value) => handleWorkingHoursChange('enabled', value)}
                        className="data-[state=checked]:bg-gradient-to-r data-[state=checked]:from-blue-600 data-[state=checked]:to-purple-600"
                      />
                    </div>

                    {user.preferences.workingHours.enabled && (
                      <div className="grid grid-cols-2 gap-6 p-4 rounded-xl bg-gradient-to-r from-slate-50 to-gray-50">
                        <div className="space-y-2.5">
                          <Label htmlFor="startTime" className="text-base font-medium text-gray-700">Início</Label>
                          <Input
                            id="startTime"
                            type="time"
                            value={user.preferences.workingHours.start}
                            onChange={(e) => handleWorkingHoursChange('start', e.target.value)}
                            className="h-12 text-base border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                          />
                        </div>
                        <div className="space-y-2.5">
                          <Label htmlFor="endTime" className="text-base font-medium text-gray-700">Fim</Label>
                          <Input
                            id="endTime"
                            type="time"
                            value={user.preferences.workingHours.end}
                            onChange={(e) => handleWorkingHoursChange('end', e.target.value)}
                            className="h-12 text-base border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                          />
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    </div>
  );
}

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
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Meu Perfil</h1>
          <p className="text-gray-600">Gerencie suas informações pessoais e preferências</p>
        </div>
        <Badge variant="outline" className="text-green-700 bg-green-50 border-green-200">
          <CheckCircle className="w-3 h-3 mr-1" />
          Conta Ativa
        </Badge>
      </div>

      {saveSuccess && (
        <Alert className="bg-green-50 border-green-200">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">
            Perfil atualizado com sucesso!
          </AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="space-y-6">
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col items-center text-center">
                <div className="relative">
                  <Avatar className="w-24 h-24">
                    <AvatarImage src={user.avatar} />
                    <AvatarFallback className="text-lg">
                      {user.name.split(' ').map(n => n[0]).join('')}
                    </AvatarFallback>
                  </Avatar>
                  <Button
                    size="sm"
                    variant="outline"
                    className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 rounded-full p-2"
                  >
                    <Camera className="w-3 h-3" />
                  </Button>
                </div>

                <h3 className="text-lg font-semibold mt-3">{user.name}</h3>
                <p className="text-gray-600">{user.email}</p>
                <Badge variant="secondary" className="mt-2">{user.role}</Badge>
              </div>

              <div className="mt-6 space-y-2 text-sm">
                <div className="flex items-center text-gray-600">
                  <MapPin className="w-4 h-4 mr-2" />
                  {user.address}
                </div>
                <div className="flex items-center text-gray-600">
                  <Calendar className="w-4 h-4 mr-2" />
                  Membro desde {new Date(user.joinedAt).toLocaleDateString('pt-BR')}
                </div>
                <div className="flex items-center text-gray-600">
                  <Shield className="w-4 h-4 mr-2" />
                  Última atividade: {new Date(user.lastActive).toLocaleString('pt-BR')}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Estatísticas</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between">
                <span className="text-gray-600">Conversas</span>
                <span className="font-semibold">{user.stats.totalConversations.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Mensagens</span>
                <span className="font-semibold">{user.stats.totalMessages.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Tempo Resposta</span>
                <span className="font-semibold text-green-600">{user.stats.responseTime}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Satisfação</span>
                <div className="flex items-center">
                  <span className="font-semibold text-yellow-600">{user.stats.customerSatisfaction}</span>
                  <span className="text-yellow-500 ml-1">⭐</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="lg:col-span-2">
          <Tabs defaultValue="profile" className="space-y-6">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="profile">Informações Pessoais</TabsTrigger>
              <TabsTrigger value="security">Segurança</TabsTrigger>
              <TabsTrigger value="preferences">Preferências</TabsTrigger>
            </TabsList>

            <TabsContent value="profile">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>Informações Pessoais</CardTitle>
                    <Button
                      variant={isEditing ? "default" : "outline"}
                      onClick={() => isEditing ? saveProfile() : setIsEditing(true)}
                    >
                      {isEditing ? (
                        <>
                          <Save className="w-4 h-4 mr-2" />
                          Salvar
                        </>
                      ) : (
                        'Editar'
                      )}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="name">Nome Completo</Label>
                      <Input
                        id="name"
                        value={formData.name}
                        onChange={(e) => handleInputChange('name', e.target.value)}
                        disabled={!isEditing}
                      />
                    </div>

                    <div>
                      <Label htmlFor="email">Email</Label>
                      <Input
                        id="email"
                        type="email"
                        value={formData.email}
                        onChange={(e) => handleInputChange('email', e.target.value)}
                        disabled={!isEditing}
                      />
                    </div>

                    <div>
                      <Label htmlFor="phone">Telefone</Label>
                      <Input
                        id="phone"
                        value={formData.phone}
                        onChange={(e) => handleInputChange('phone', e.target.value)}
                        disabled={!isEditing}
                      />
                    </div>

                    <div>
                      <Label htmlFor="company">Empresa</Label>
                      <Input
                        id="company"
                        value={formData.company}
                        onChange={(e) => handleInputChange('company', e.target.value)}
                        disabled={!isEditing}
                      />
                    </div>

                    <div className="md:col-span-2">
                      <Label htmlFor="address">Endereço</Label>
                      <Input
                        id="address"
                        value={formData.address}
                        onChange={(e) => handleInputChange('address', e.target.value)}
                        disabled={!isEditing}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="security">
              <Card>
                <CardHeader>
                  <CardTitle>Segurança da Conta</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label htmlFor="currentPassword">Senha Atual</Label>
                    <div className="relative">
                      <Input
                        id="currentPassword"
                        type={showCurrentPassword ? "text" : "password"}
                        value={passwordData.currentPassword}
                        onChange={(e) => handlePasswordChange('currentPassword', e.target.value)}
                        placeholder="Digite sua senha atual"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-2 top-1/2 transform -translate-y-1/2"
                        onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                      >
                        {showCurrentPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </Button>
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="newPassword">Nova Senha</Label>
                    <div className="relative">
                      <Input
                        id="newPassword"
                        type={showNewPassword ? "text" : "password"}
                        value={passwordData.newPassword}
                        onChange={(e) => handlePasswordChange('newPassword', e.target.value)}
                        placeholder="Digite uma nova senha"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-2 top-1/2 transform -translate-y-1/2"
                        onClick={() => setShowNewPassword(!showNewPassword)}
                      >
                        {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </Button>
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="confirmPassword">Confirmar Nova Senha</Label>
                    <div className="relative">
                      <Input
                        id="confirmPassword"
                        type={showConfirmPassword ? "text" : "password"}
                        value={passwordData.confirmPassword}
                        onChange={(e) => handlePasswordChange('confirmPassword', e.target.value)}
                        placeholder="Confirme a nova senha"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-2 top-1/2 transform -translate-y-1/2"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      >
                        {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </Button>
                    </div>
                  </div>

                  <Button
                    onClick={changePassword}
                    className="w-full md:w-auto"
                    disabled={!passwordData.currentPassword || !passwordData.newPassword || !passwordData.confirmPassword}
                  >
                    <Lock className="w-4 h-4 mr-2" />
                    Alterar Senha
                  </Button>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="preferences">
              <Card>
                <CardHeader>
                  <CardTitle>Preferências de Notificação</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Notificações por Email</Label>
                      <p className="text-sm text-gray-600">Receber notificações no email</p>
                    </div>
                    <Switch
                      checked={user.preferences.emailNotifications}
                      onCheckedChange={(value) => handlePreferenceChange('emailNotifications', value)}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Notificações Push</Label>
                      <p className="text-sm text-gray-600">Receber notificações no navegador</p>
                    </div>
                    <Switch
                      checked={user.preferences.pushNotifications}
                      onCheckedChange={(value) => handlePreferenceChange('pushNotifications', value)}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Sons de Notificação</Label>
                      <p className="text-sm text-gray-600">Reproduzir sons para novas mensagens</p>
                    </div>
                    <Switch
                      checked={user.preferences.soundNotifications}
                      onCheckedChange={(value) => handlePreferenceChange('soundNotifications', value)}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Resposta Automática</Label>
                      <p className="text-sm text-gray-600">Enviar respostas automáticas quando ausente</p>
                    </div>
                    <Switch
                      checked={user.preferences.autoReply}
                      onCheckedChange={(value) => handlePreferenceChange('autoReply', value)}
                    />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Horário de Trabalho</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Ativar Horário de Trabalho</Label>
                      <p className="text-sm text-gray-600">Definir horários específicos para atendimento</p>
                    </div>
                    <Switch
                      checked={user.preferences.workingHours.enabled}
                      onCheckedChange={(value) => handleWorkingHoursChange('enabled', value)}
                    />
                  </div>

                  {user.preferences.workingHours.enabled && (
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="startTime">Início</Label>
                        <Input
                          id="startTime"
                          type="time"
                          value={user.preferences.workingHours.start}
                          onChange={(e) => handleWorkingHoursChange('start', e.target.value)}
                        />
                      </div>
                      <div>
                        <Label htmlFor="endTime">Fim</Label>
                        <Input
                          id="endTime"
                          type="time"
                          value={user.preferences.workingHours.end}
                          onChange={(e) => handleWorkingHoursChange('end', e.target.value)}
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
  );
}

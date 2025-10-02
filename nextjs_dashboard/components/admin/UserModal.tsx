'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle 
} from '@/components/ui/dialog';
import { Switch } from '@/components/ui/switch';
import { 
  Eye, 
  EyeOff, 
  RefreshCw, 
  CheckCircle, 
  XCircle,
  Shield,
  User,
  Eye as EyeIcon
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface User {
  id: number;
  nome: string;
  email: string;
  role: 'admin' | 'atendente' | 'visualizador';
  status: 'ativo' | 'inativo';
  ultima_atividade: string;
  created_at: string;
  updated_at?: string;
}

interface UserModalProps {
  user?: User | null;
  isEdit: boolean;
  onClose: () => void;
  onSave: (user: User) => void;
}

const roleOptions = [
  { value: 'admin', label: 'Administrador', icon: Shield, description: 'Acesso total ao sistema' },
  { value: 'atendente', label: 'Atendente', icon: User, description: 'Gerenciar conversas e agendamentos' },
  { value: 'visualizador', label: 'Visualizador', icon: EyeIcon, description: 'Apenas visualização de dados' }
];

const passwordRequirements = [
  { text: 'Pelo menos 8 caracteres', test: (pwd: string) => pwd.length >= 8 },
  { text: 'Pelo menos 1 letra maiúscula', test: (pwd: string) => /[A-Z]/.test(pwd) },
  { text: 'Pelo menos 1 letra minúscula', test: (pwd: string) => /[a-z]/.test(pwd) },
  { text: 'Pelo menos 1 número', test: (pwd: string) => /\d/.test(pwd) },
  { text: 'Pelo menos 1 caractere especial', test: (pwd: string) => /[!@#$%^&*(),.?":{}|<>]/.test(pwd) }
];

export function UserModal({ user, isEdit, onClose, onSave }: UserModalProps) {
  const [formData, setFormData] = useState({
    nome: '',
    email: '',
    senha: '',
    confirmarSenha: '',
    role: 'atendente' as 'admin' | 'atendente' | 'visualizador',
    status: 'ativo' as 'ativo' | 'inativo'
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isGeneratingPassword, setIsGeneratingPassword] = useState(false);
  const { toast } = useToast();

  // Carregar dados do usuário se estiver editando
  useEffect(() => {
    if (isEdit && user) {
      setFormData({
        nome: user.nome,
        email: user.email,
        senha: '',
        confirmarSenha: '',
        role: user.role,
        status: user.status
      });
    }
  }, [isEdit, user]);

  // Gerar senha aleatória
  const generatePassword = () => {
    setIsGeneratingPassword(true);
    
    // Simular delay
    setTimeout(() => {
      const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*';
      let password = '';
      
      // Garantir pelo menos um de cada tipo
      password += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[Math.floor(Math.random() * 26)];
      password += 'abcdefghijklmnopqrstuvwxyz'[Math.floor(Math.random() * 26)];
      password += '0123456789'[Math.floor(Math.random() * 10)];
      password += '!@#$%^&*'[Math.floor(Math.random() * 8)];
      
      // Adicionar caracteres aleatórios até ter 12 caracteres
      for (let i = 4; i < 12; i++) {
        password += chars[Math.floor(Math.random() * chars.length)];
      }
      
      // Embaralhar a senha
      password = password.split('').sort(() => Math.random() - 0.5).join('');
      
      setFormData(prev => ({ ...prev, senha: password, confirmarSenha: password }));
      setIsGeneratingPassword(false);
      
      toast({
        title: 'Senha Gerada',
        description: 'Uma nova senha forte foi gerada automaticamente'
      });
    }, 1000);
  };

  // Validar formulário
  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.nome.trim()) {
      newErrors.nome = 'Nome é obrigatório';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email é obrigatório';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Email inválido';
    }

    if (!isEdit || formData.senha) {
      if (!formData.senha) {
        newErrors.senha = 'Senha é obrigatória';
      } else {
        // Verificar requisitos de senha
        passwordRequirements.forEach(req => {
          if (!req.test(formData.senha)) {
            newErrors.senha = 'Senha não atende aos requisitos';
          }
        });
      }

      if (formData.senha !== formData.confirmarSenha) {
        newErrors.confirmarSenha = 'Senhas não coincidem';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Salvar usuário
  const handleSave = () => {
    if (!validateForm()) {
      return;
    }

    const userData: User = {
      id: user?.id || Date.now(), // Gerar ID temporário para novos usuários
      nome: formData.nome.trim(),
      email: formData.email.trim(),
      role: formData.role,
      status: formData.status,
      ultima_atividade: user?.ultima_atividade || new Date().toISOString(),
      created_at: user?.created_at || new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    onSave(userData);
  };

  // Verificar se a senha atende aos requisitos
  const getPasswordStrength = () => {
    if (!formData.senha) return 0;
    return passwordRequirements.filter(req => req.test(formData.senha)).length;
  };

  const passwordStrength = getPasswordStrength();
  const isPasswordStrong = passwordStrength === passwordRequirements.length;

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isEdit ? 'Editar Usuário' : 'Novo Usuário'}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Nome */}
          <div className="space-y-2">
            <Label htmlFor="nome">Nome *</Label>
            <Input
              id="nome"
              value={formData.nome}
              onChange={(e) => setFormData(prev => ({ ...prev, nome: e.target.value }))}
              placeholder="Nome completo do usuário"
              className={errors.nome ? 'border-red-500' : ''}
            />
            {errors.nome && (
              <p className="text-sm text-red-500">{errors.nome}</p>
            )}
          </div>

          {/* Email */}
          <div className="space-y-2">
            <Label htmlFor="email">Email *</Label>
            <Input
              id="email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
              placeholder="email@empresa.com"
              className={errors.email ? 'border-red-500' : ''}
              disabled={isEdit} // Email não pode ser alterado na edição
            />
            {errors.email && (
              <p className="text-sm text-red-500">{errors.email}</p>
            )}
            {isEdit && (
              <p className="text-sm text-muted-foreground">
                Email não pode ser alterado após a criação
              </p>
            )}
          </div>

          {/* Senha */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="senha">
                Senha {isEdit ? '(deixe em branco para manter a atual)' : '*'}
              </Label>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={generatePassword}
                disabled={isGeneratingPassword}
              >
                {isGeneratingPassword ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
                Gerar Senha
              </Button>
            </div>
            
            <div className="relative">
              <Input
                id="senha"
                type={showPassword ? 'text' : 'password'}
                value={formData.senha}
                onChange={(e) => setFormData(prev => ({ ...prev, senha: e.target.value }))}
                placeholder="Digite a senha"
                className={errors.senha ? 'border-red-500' : ''}
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-0 top-0 h-full px-3"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </Button>
            </div>

            {/* Indicador de força da senha */}
            {formData.senha && (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full transition-all ${
                        passwordStrength <= 2 ? 'bg-red-500' :
                        passwordStrength <= 3 ? 'bg-yellow-500' :
                        'bg-green-500'
                      }`}
                      style={{ width: `${(passwordStrength / passwordRequirements.length) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm text-muted-foreground">
                    {passwordStrength}/{passwordRequirements.length}
                  </span>
                </div>

                <div className="space-y-1">
                  {passwordRequirements.map((req, index) => (
                    <div key={index} className="flex items-center gap-2 text-sm">
                      {req.test(formData.senha) ? (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      ) : (
                        <XCircle className="h-4 w-4 text-red-500" />
                      )}
                      <span className={req.test(formData.senha) ? 'text-green-700' : 'text-red-700'}>
                        {req.text}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {errors.senha && (
              <p className="text-sm text-red-500">{errors.senha}</p>
            )}
          </div>

          {/* Confirmar Senha */}
          {(!isEdit || formData.senha) && (
            <div className="space-y-2">
              <Label htmlFor="confirmarSenha">Confirmar Senha *</Label>
              <div className="relative">
                <Input
                  id="confirmarSenha"
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={formData.confirmarSenha}
                  onChange={(e) => setFormData(prev => ({ ...prev, confirmarSenha: e.target.value }))}
                  placeholder="Confirme a senha"
                  className={errors.confirmarSenha ? 'border-red-500' : ''}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                >
                  {showConfirmPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </Button>
              </div>
              {errors.confirmarSenha && (
                <p className="text-sm text-red-500">{errors.confirmarSenha}</p>
              )}
            </div>
          )}

          {/* Role */}
          <div className="space-y-2">
            <Label>Role *</Label>
            <Select
              value={formData.role}
              onValueChange={(value: 'admin' | 'atendente' | 'visualizador') => 
                setFormData(prev => ({ ...prev, role: value }))
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {roleOptions.map((option) => {
                  const Icon = option.icon;
                  return (
                    <SelectItem key={option.value} value={option.value}>
                      <div className="flex items-center gap-2">
                        <Icon className="h-4 w-4" />
                        <div>
                          <div className="font-medium">{option.label}</div>
                          <div className="text-sm text-muted-foreground">
                            {option.description}
                          </div>
                        </div>
                      </div>
                    </SelectItem>
                  );
                })}
              </SelectContent>
            </Select>
          </div>

          {/* Status */}
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Status</Label>
              <p className="text-sm text-muted-foreground">
                Usuário ativo pode fazer login no sistema
              </p>
            </div>
            <Switch
              checked={formData.status === 'ativo'}
              onCheckedChange={(checked) => 
                setFormData(prev => ({ 
                  ...prev, 
                  status: checked ? 'ativo' : 'inativo' 
                }))
              }
            />
          </div>
        </div>

        {/* Botões */}
        <div className="flex justify-end gap-3 pt-6 border-t">
          <Button variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button onClick={handleSave}>
            {isEdit ? 'Salvar Alterações' : 'Criar Usuário'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

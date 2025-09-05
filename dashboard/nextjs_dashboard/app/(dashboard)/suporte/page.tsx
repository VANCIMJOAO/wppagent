'use client'

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
// import { Textarea } from "@/components/ui/textarea"
import TextareaAutosize from "react-textarea-autosize"
import { Badge } from "@/components/ui/badge"
import { 
  HelpCircle, 
  MessageCircle, 
  CheckCircle,
  AlertCircle,
  XCircle,
  FileText,
  Mail,
  Phone,
  Clock,
  Send,
  BookOpen,
  Settings,
  Users,
  Zap
} from "lucide-react"
import { Textarea } from "@/components/ui/textarea"

interface FAQ {
  id: number;
  question: string;
  answer: string;
  category: 'geral' | 'tecnico' | 'conta' | 'cobranca';
}

interface SystemStatus {
  service: string;
  status: 'online' | 'warning' | 'offline';
  uptime: string;
}

export default function SuportePage() {
  const [selectedCategory, setSelectedCategory] = useState('geral');
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    category: '',
    priority: '',
    subject: '',
    message: ''
  });

  // FAQs por categoria
  const faqs: FAQ[] = [
    {
      id: 1,
      question: "Como funciona o sistema de agendamentos?",
      answer: "O sistema permite que clientes agendem serviços através do WhatsApp. As mensagens são processadas automaticamente e os horários disponíveis são apresentados ao cliente.",
      category: 'geral'
    },
    {
      id: 2,
      question: "Posso integrar com meu sistema atual?",
      answer: "Sim! Oferecemos APIs REST e webhooks para integração com sistemas terceiros. Entre em contato para discutir sua integração específica.",
      category: 'tecnico'
    },
    {
      id: 3,
      question: "Como alterar minha senha de acesso?",
      answer: "Acesse seu perfil no menu superior direito, vá em 'Configurações' e clique em 'Alterar Senha'. Você receberá um email de confirmação.",
      category: 'conta'
    },
    {
      id: 4,
      question: "Como funciona a cobrança do sistema?",
      answer: "A cobrança é mensal, baseada no número de conversas ativas e recursos utilizados. Consulte nossos planos na seção de configurações.",
      category: 'cobranca'
    },
    {
      id: 5,
      question: "O sistema funciona 24/7?",
      answer: "Sim! Nosso sistema opera 24 horas por dia, 7 dias por semana. Monitoramos constantemente para garantir alta disponibilidade.",
      category: 'geral'
    },
    {
      id: 6,
      question: "Como configurar mensagens automáticas?",
      answer: "Vá em Configurações > Bot > Mensagens Automáticas. Você pode criar respostas personalizadas para diferentes situações.",
      category: 'tecnico'
    }
  ];

  // Status dos sistemas
  const systemStatus: SystemStatus[] = [
    { service: "WhatsApp API", status: "online", uptime: "99.9%" },
    { service: "Dashboard Web", status: "online", uptime: "99.8%" },
    { service: "Base de Dados", status: "online", uptime: "99.9%" },
    { service: "Sistema de Backup", status: "online", uptime: "99.7%" },
    { service: "Notificações", status: "warning", uptime: "98.5%" }
  ];

  // Filtrar FAQs por categoria
  const filteredFAQs = faqs.filter(faq => faq.category === selectedCategory);

  // Categorias para filtro
  const categories = [
    { id: 'geral', label: 'Geral', icon: HelpCircle, color: 'blue' },
    { id: 'tecnico', label: 'Técnico', icon: Settings, color: 'orange' },
    { id: 'conta', label: 'Conta', icon: Users, color: 'green' },
    { id: 'cobranca', label: 'Cobrança', icon: FileText, color: 'purple' }
  ];

  // Status icon and color helper
  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'online':
        return { icon: CheckCircle, color: 'text-green-600', bgColor: 'bg-green-100', label: 'Operacional' };
      case 'warning':
        return { icon: AlertCircle, color: 'text-yellow-600', bgColor: 'bg-yellow-100', label: 'Degradado' };
      case 'offline':
        return { icon: XCircle, color: 'text-red-600', bgColor: 'bg-red-100', label: 'Indisponível' };
      default:
        return { icon: CheckCircle, color: 'text-green-600', bgColor: 'bg-green-100', label: 'Operacional' };
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Implementar envio do formulário
    console.log('Formulário enviado:', formData);
    alert('Ticket criado com sucesso! Responderemos em breve.');
    setFormData({ name: '', email: '', category: '', priority: '', subject: '', message: '' });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-700 text-white rounded-lg p-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold mb-2">Central de Suporte</h1>
            <p className="text-blue-100 opacity-90">
              Encontre respostas, abra tickets e acompanhe o status dos sistemas
            </p>
          </div>
          <div className="bg-white/20 backdrop-blur-sm rounded-lg p-3">
            <MessageCircle className="h-6 w-6" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Coluna principal */}
        <div className="lg:col-span-2 space-y-6">
          {/* Status do Sistema */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center text-xl">
                <Zap className="h-6 w-6 mr-2 text-green-600" />
                Status do Sistema
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {systemStatus.map((system, index) => {
                const config = getStatusConfig(system.status);
                const StatusIcon = config.icon;
                
                return (
                  <div key={index} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 rounded-full ${config.bgColor}`}>
                        <StatusIcon className={`h-4 w-4 ${config.color}`} />
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">{system.service}</p>
                        <p className="text-sm text-gray-500">{config.label}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`text-sm font-semibold ${config.color}`}>{system.uptime}</p>
                      <p className="text-xs text-gray-500">uptime</p>
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>

          {/* FAQ */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center text-xl">
                <BookOpen className="h-6 w-6 mr-2 text-blue-600" />
                Perguntas Frequentes
              </CardTitle>
            </CardHeader>
            <CardContent>
              {/* Filtros de categoria */}
              <div className="flex flex-wrap gap-2 mb-6">
                {categories.map((category) => {
                  const CategoryIcon = category.icon;
                  return (
                    <Button
                      key={category.id}
                      variant={selectedCategory === category.id ? "default" : "outline"}
                      onClick={() => setSelectedCategory(category.id)}
                      className="flex items-center space-x-2"
                    >
                      <CategoryIcon className="h-4 w-4" />
                      <span>{category.label}</span>
                    </Button>
                  );
                })}
              </div>

              {/* Lista de FAQs */}
              <div className="space-y-4">
                {filteredFAQs.map((faq) => (
                  <div key={faq.id} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                    <div className="flex items-start space-x-3 mb-2">
                      <HelpCircle className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
                      <h3 className="font-semibold text-gray-900">{faq.question}</h3>
                    </div>
                    <p className="text-gray-600 text-sm pl-8">{faq.answer}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Contato rápido */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Contato Rápido</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center space-x-3 p-3 bg-blue-50 rounded-lg">
                <Mail className="h-5 w-5 text-blue-600" />
                <div>
                  <p className="font-medium text-blue-900">Email</p>
                  <p className="text-sm text-blue-700">suporte@wppagent.com</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
                <Phone className="h-5 w-5 text-green-600" />
                <div>
                  <p className="font-medium text-green-900">WhatsApp</p>
                  <p className="text-sm text-green-700">+55 (11) 9999-9999</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-3 p-3 bg-orange-50 rounded-lg">
                <Clock className="h-5 w-5 text-orange-600" />
                <div>
                  <p className="font-medium text-orange-900">Horário</p>
                  <p className="text-sm text-orange-700">Seg-Sex: 8h-18h</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Formulário de ticket */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Abrir Ticket</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <Input
                    placeholder="Seu nome"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    required
                  />
                </div>
                
                <div>
                  <Input
                    type="email"
                    placeholder="seu@email.com"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    required
                  />
                </div>

                <div>
                  <select
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    value={formData.category}
                    onChange={(e) => setFormData({...formData, category: e.target.value})}
                    required
                  >
                    <option value="">Selecione a categoria</option>
                    <option value="bug">🐛 Bug/Erro</option>
                    <option value="feature">💡 Sugestão</option>
                    <option value="account">👤 Problema de conta</option>
                    <option value="billing">💳 Questões de cobrança</option>
                    <option value="integration">🔌 Integração</option>
                    <option value="other">❓ Outros</option>
                  </select>
                </div>

                <div>
                  <select
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    value={formData.priority}
                    onChange={(e) => setFormData({...formData, priority: e.target.value})}
                    required
                  >
                    <option value="">Prioridade</option>
                    <option value="low">🟢 Baixa</option>
                    <option value="medium">🟡 Média</option>
                    <option value="high">🟠 Alta</option>
                    <option value="urgent">🔴 Urgente</option>
                  </select>
                </div>

                <div>
                  <Input
                    placeholder="Assunto do ticket"
                    value={formData.subject}
                    onChange={(e) => setFormData({...formData, subject: e.target.value})}
                    required
                  />
                </div>

                <div>
                  <Textarea
                    placeholder="Descreva seu problema em detalhes..."
                    rows={4}
                    value={formData.message}
                    onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setFormData({...formData, message: e.target.value})}
                    required
                  />
                </div>

                <Button type="submit" className="w-full flex items-center justify-center space-x-2">
                  <Send className="h-4 w-4" />
                  <span>Enviar Ticket</span>
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

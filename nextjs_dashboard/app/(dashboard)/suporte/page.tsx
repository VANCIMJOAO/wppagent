'use client'

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
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
  Zap,
  RefreshCw,
  AlertTriangle
} from "lucide-react"
import { Textarea } from "@/components/ui/textarea"

interface FAQ {
  id: number;
  question: string;
  answer: string;
  category: 'geral' | 'tecnico' | 'conta' | 'cobranca';
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

interface SystemStatus {
  service: string;
  status: 'online' | 'warning' | 'offline';
  uptime: string;
  details: string;
}

interface SystemStatusResponse {
  overall_status: string;
  services: SystemStatus[];
  metrics: {
    total_users: number;
    total_conversations: number;
    total_appointments: number;
    total_messages: number;
  };
  last_check: string;
  uptime_percentage: number;
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
  const [faqs, setFaqs] = useState<FAQ[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Carregar dados reais
  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Carregar FAQs
      const faqsResponse = await fetch('/api/support/faqs');
      const faqsData = await faqsResponse.json();

      if (faqsData.success) {
        setFaqs(faqsData.data || faqsData.faqs || []);
      } else {
        console.error('Erro ao carregar FAQs:', faqsData.error);
      }

      // Carregar status do sistema
      const statusResponse = await fetch('/api/support/system-status');
      const statusData = await statusResponse.json();

      if (statusData.success) {
        setSystemStatus(statusData.data);
      } else {
        console.error('Erro ao carregar status:', statusData.error);
      }

    } catch (err) {
      console.error('Erro ao carregar dados:', err);
      setError(err instanceof Error ? err.message : 'Erro de rede ou servidor');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      setSubmitting(true);
      
      const response = await fetch('/api/support/tickets', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const result = await response.json();

      if (result.success) {
        alert('Ticket criado com sucesso! Responderemos em breve.');
        setFormData({ name: '', email: '', category: '', priority: '', subject: '', message: '' });
      } else {
        alert(`Erro ao criar ticket: ${result.error}`);
      }
    } catch (error) {
      console.error('Erro ao enviar ticket:', error);
      alert('Erro ao enviar ticket. Tente novamente.');
    } finally {
      setSubmitting(false);
    }
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
            {systemStatus && (
              <div className="mt-2 flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${
                  systemStatus.overall_status === 'online' ? 'bg-green-400' :
                  systemStatus.overall_status === 'warning' ? 'bg-yellow-400' : 'bg-red-400'
                }`}></div>
                <span className="text-sm text-blue-100">
                  Sistema {systemStatus.overall_status === 'online' ? 'Operacional' : 
                          systemStatus.overall_status === 'warning' ? 'Degradado' : 'Indisponível'} 
                  ({systemStatus.uptime_percentage}% uptime)
                </span>
              </div>
            )}
          </div>
          <div className="flex items-center space-x-3">
            <Button
              variant="outline"
              onClick={loadData}
              disabled={loading}
              className="bg-white/20 border-white/30 text-white hover:bg-white/30"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Atualizar
            </Button>
            <div className="bg-white/20 backdrop-blur-sm rounded-lg p-3">
              <MessageCircle className="h-6 w-6" />
            </div>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4">
            <div className="flex items-center space-x-2 text-red-800">
              <AlertTriangle className="h-5 w-5" />
              <span className="font-medium">Erro ao carregar dados:</span>
              <span>{error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Coluna principal */}
        <div className="lg:col-span-2 space-y-6">
          {/* Status do Sistema */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center text-xl">
                <Zap className="h-6 w-6 mr-2 text-green-600" />
                Status do Sistema
                {systemStatus && (
                  <Badge className={`ml-2 ${
                    systemStatus.overall_status === 'online' ? 'bg-green-100 text-green-800' :
                    systemStatus.overall_status === 'warning' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {systemStatus.overall_status === 'online' ? 'Operacional' : 
                     systemStatus.overall_status === 'warning' ? 'Degradado' : 'Indisponível'}
                  </Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {loading ? (
                <div className="flex justify-center items-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <span className="ml-3 text-gray-600">Carregando status...</span>
                </div>
              ) : systemStatus ? (
                <>
                  {systemStatus.services.map((system, index) => {
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
                            <p className="text-sm text-gray-500">{system.details}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className={`text-sm font-semibold ${config.color}`}>{system.uptime}</p>
                          <p className="text-xs text-gray-500">uptime</p>
                        </div>
                      </div>
                    );
                  })}
                  
                  {/* Métricas do sistema */}
                  {systemStatus.metrics && (
                    <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                      <h4 className="font-semibold text-gray-900 mb-3">Métricas do Sistema</h4>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="text-center">
                          <p className="text-2xl font-bold text-blue-600">{systemStatus.metrics.total_users}</p>
                          <p className="text-sm text-gray-600">Usuários</p>
                        </div>
                        <div className="text-center">
                          <p className="text-2xl font-bold text-green-600">{systemStatus.metrics.total_conversations}</p>
                          <p className="text-sm text-gray-600">Conversas</p>
                        </div>
                        <div className="text-center">
                          <p className="text-2xl font-bold text-purple-600">{systemStatus.metrics.total_appointments}</p>
                          <p className="text-sm text-gray-600">Agendamentos</p>
                        </div>
                        <div className="text-center">
                          <p className="text-2xl font-bold text-orange-600">{systemStatus.metrics.total_messages}</p>
                          <p className="text-sm text-gray-600">Mensagens</p>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <p>Não foi possível carregar o status do sistema</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* FAQ */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center text-xl">
                <BookOpen className="h-6 w-6 mr-2 text-blue-600" />
                Perguntas Frequentes
                <Badge className="ml-2 bg-blue-100 text-blue-800">
                  {filteredFAQs.length} perguntas
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {/* Filtros de categoria */}
              <div className="flex flex-wrap gap-2 mb-6">
                {categories.map((category) => {
                  const CategoryIcon = category.icon;
                  const categoryCount = faqs.filter(faq => faq.category === category.id).length;
                  return (
                    <Button
                      key={category.id}
                      variant={selectedCategory === category.id ? "default" : "outline"}
                      onClick={() => setSelectedCategory(category.id)}
                      className="flex items-center space-x-2"
                    >
                      <CategoryIcon className="h-4 w-4" />
                      <span>{category.label}</span>
                      <Badge variant="secondary" className="ml-1">
                        {categoryCount}
                      </Badge>
                    </Button>
                  );
                })}
              </div>

              {/* Lista de FAQs */}
              {loading ? (
                <div className="flex justify-center items-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <span className="ml-3 text-gray-600">Carregando FAQs...</span>
                </div>
              ) : filteredFAQs.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <BookOpen className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <p>Nenhuma pergunta encontrada nesta categoria</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {filteredFAQs.map((faq) => (
                    <div key={faq.id} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                      <div className="flex items-start space-x-3 mb-2">
                        <HelpCircle className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
                        <h3 className="font-semibold text-gray-900">{faq.question}</h3>
                      </div>
                      <p className="text-gray-600 text-sm pl-8 mb-2">{faq.answer}</p>
                      <div className="pl-8 text-xs text-gray-400">
                        Atualizado em {new Date(faq.updated_at).toLocaleDateString('pt-BR')}
                      </div>
                    </div>
                  ))}
                </div>
              )}
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

                <Button 
                  type="submit" 
                  disabled={submitting}
                  className="w-full flex items-center justify-center space-x-2"
                >
                  {submitting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Enviando...</span>
                    </>
                  ) : (
                    <>
                      <Send className="h-4 w-4" />
                      <span>Enviar Ticket</span>
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

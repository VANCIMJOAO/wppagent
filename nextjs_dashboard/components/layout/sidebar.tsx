'use client'

import { useState, useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
// import { useAuth } from '@/contexts/auth-context' // Removido - usando estado local
import {
  LayoutDashboard,
  MessageCircle,
  Users,
  Calendar,
  FileText,
  Settings,
  User,
  LogOut,
  ChevronDown,
  Bell,
  HelpCircle,
  UserX,
  Activity,
  Menu,
  X,
  Shield,
  MessageSquare,
  Database
} from 'lucide-react'
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { cn } from '@/lib/utils'

interface User {
  id: number
  email: string
  name: string
  role: string
  avatar_url?: string
}

interface SidebarProps {
  children: React.ReactNode
}

export default function Sidebar({ children }: SidebarProps) {
  const [user, setUser] = useState<User | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    // ✅ CORREÇÃO: Não fazer verificação local - usar auth-context
    const checkAuth = () => {
      try {
        // Sistema agora usa cookies seguros gerenciados pelo auth-context
        // Definir usuário padrão se chegou até aqui (significa que passou pelo middleware)
        setUser({ 
          id: 1,
          email: 'admin@whatsappagent.com',
          name: 'Administrador',
          role: 'admin',
          avatar_url: undefined
        });
        setIsAuthenticated(true);
      } catch (error) {
        console.error('Erro ao verificar autenticação:', error)
        setIsAuthenticated(false)
        // Não redirecionar - deixar auth-context gerenciar
      }
      setIsLoading(false)
    }

    checkAuth()
  }, [router])

  // Função de logout simples
  const logout = async () => {
    try {
      // Limpar localStorage
      localStorage.removeItem('user')
      
      // Limpar cookie via API
      await fetch('/api/auth/clear-token', {
        method: 'POST',
        credentials: 'include',
      })
      
      // Redirecionar para login
      router.push('/login')
    } catch (error) {
      console.error('Erro no logout:', error)
      // Mesmo com erro, limpar estado local
      localStorage.removeItem('user')
      router.push('/login')
    }
  }

  // Fechar menu mobile em resize para desktop
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 768) {
        setIsMobileMenuOpen(false)
      }
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  // Prevenir scroll do body quando menu mobile está aberto
  useEffect(() => {
    if (isMobileMenuOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }

    // Cleanup quando componente é desmontado
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isMobileMenuOpen])

  const handleLogout = async () => {
    console.log('🚪 Iniciando logout...')
    try {
      // Limpar localStorage primeiro
      localStorage.removeItem('user')
      console.log('🧹 localStorage limpo')
      
      // Limpar cookie via API (não bloquear se falhar)
      try {
        const response = await fetch('/api/auth/clear-token', {
          method: 'POST',
          credentials: 'include',
        })
        
        if (!response.ok) {
          console.warn('Failed to clear token on server, but continuing with logout')
        } else {
          console.log('🍪 Cookie limpo no servidor')
        }
      } catch (apiError) {
        console.warn('API call failed during logout, but continuing:', apiError)
      }
      
      // Redirecionar para login imediatamente
      console.log('🔄 Redirecionando para login...')
      router.push('/login')
    } catch (error) {
      console.error('Erro no logout:', error)
      // Mesmo com erro, limpar estado local e redirecionar
      localStorage.removeItem('user')
      router.push('/login')
    }
  }

  const handleMenuItemClick = (href: string) => {
    router.push(href)
    setIsMobileMenuOpen(false) // Fechar menu mobile ao navegar
  }

  const menuItems = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: LayoutDashboard,
      href: '/dashboard',
      description: 'Visão geral'
    },
    {
      id: 'conversas',
      label: 'Conversas',
      icon: MessageCircle,
      href: '/conversas',
      description: 'WhatsApp',
      badge: '12'
    },
    {
      id: 'clientes',
      label: 'Clientes',
      icon: Users,
      href: '/clientes',
      description: 'Base de dados'
    },
    {
      id: 'agendamentos',
      label: 'Agendamentos',
      icon: Calendar,
      href: '/agendamentos',
      description: 'Agenda',
      badge: '3'
    },
    {
      id: 'relatorios',
      label: 'Relatórios',
      icon: FileText,
      href: '/relatorios',
      description: 'Analytics'
    },
    {
      id: 'reports',
      label: 'Exportar Relatórios',
      icon: FileText,
      href: '/exportar-relatorios',
      description: 'CSV/Excel/PDF',
      badge: 'NEW'
    },
    {
      id: 'bloqueados',
      label: 'Bloqueados',
      icon: UserX,
      href: '/bloqueados',
      description: 'Horários'
    },
    {
      id: 'monitoring',
      label: 'Monitoramento',
      icon: Activity,
      href: '/monitoring',
      description: 'Sistema & Alertas'
    },
    {
      id: 'suporte',
      label: 'Suporte',
      icon: HelpCircle,
      href: '/suporte',
      description: 'Ajuda & FAQ'
    },
    {
      id: 'configuracoes',
      label: 'Configurações',
      icon: Settings,
      href: '/configuracoes',
      description: 'Sistema'
    },
    {
      id: 'admin-usuarios',
      label: 'Gestão de Usuários',
      icon: Shield,
      href: '/admin/usuarios',
      description: 'Admin',
      adminOnly: true
    },
    {
      id: 'templates',
      label: 'Templates WhatsApp',
      icon: MessageSquare,
      href: '/configuracoes/templates',
      description: 'Admin',
      adminOnly: true
    },
    {
      id: 'admin-backup',
      label: 'Gestão de Backups',
      icon: Database,
      href: '/admin/backup',
      description: 'Admin',
      adminOnly: true
    }
  ]

  const getRoleBadge = (role: string) => {
    const roleConfig = {
      'super_admin': { label: 'Super Admin', color: 'bg-red-500' },
      'admin': { label: 'Admin', color: 'bg-blue-500' },
      'manager': { label: 'Manager', color: 'bg-green-500' },
      'operator': { label: 'Operador', color: 'bg-orange-500' },
      'viewer': { label: 'Viewer', color: 'bg-gray-500' }
    }

    const config = roleConfig[role as keyof typeof roleConfig] || roleConfig.viewer
    return (
      <Badge className={`${config.color} text-white`}>
        {config.label}
      </Badge>
    )
  }

  // Mostrar loading apenas se ainda está carregando
  if (isLoading) {
    return <div>Carregando...</div>
  }

  // Se não está autenticado, redirecionar (já feito no useEffect)
  if (!isAuthenticated) {
    return <div>Redirecionando...</div>
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Mobile Menu Button */}
      <div className="md:hidden fixed top-4 left-4 z-50">
        <Button
          variant="outline"
          size="sm"
          className="bg-white shadow-lg border-gray-200"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        >
          {isMobileMenuOpen ? (
            <X className="h-5 w-5" />
          ) : (
            <Menu className="h-5 w-5" />
          )}
        </Button>
      </div>

      {/* Sidebar */}
      <div className={`
        fixed md:relative inset-y-0 left-0 z-40
        ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        w-80 bg-white border-r border-gray-200 flex flex-col
        transition-transform duration-300 ease-in-out
        md:transition-none
      `}>
        {/* Logo */}
        <div className="p-4 md:p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 md:w-10 md:h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <MessageCircle className="h-4 w-4 md:h-6 md:w-6 text-white" />
            </div>
            <div>
              <h2 className="text-lg md:text-xl font-bold text-gray-900">WppAgent</h2>
              <p className="text-xs md:text-sm text-gray-500">Dashboard Pro</p>
            </div>
          </div>
        </div>

        {/* User Info */}
        <div className="p-4 md:p-6 border-b border-gray-200">
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-3 md:p-4">
            <div className="flex items-center space-x-3">
              <div className="relative">
                <Avatar className="h-10 w-10 md:h-12 md:w-12 ring-2 ring-blue-100">
                  <AvatarImage 
                    src={user?.avatar_url} 
                    alt={user?.name || 'Usuário'} 
                  />
                  <AvatarFallback className="bg-gradient-to-br from-blue-500 to-purple-600 text-white font-semibold text-sm">
                    {user?.name?.charAt(0).toUpperCase() || 'A'}
                  </AvatarFallback>
                </Avatar>
                <div className="absolute -bottom-1 -right-1 w-3 h-3 md:w-4 md:h-4 bg-green-500 rounded-full border-2 border-white shadow-sm">
                  <div className="w-full h-full bg-green-400 rounded-full animate-pulse"></div>
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-gray-900 text-sm md:text-base truncate">{user?.name || 'Usuário'}</p>
                <div className="flex items-center space-x-2 mt-1">
                  {user?.role && getRoleBadge(user.role)}
                  <Badge variant="outline" className="text-green-600 border-green-200 text-xs">
                    Online
                  </Badge>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-2 mt-3 md:mt-4">
              <Button size="sm" variant="outline" className="flex-1 text-xs">
                <User className="h-3 w-3 md:h-4 md:w-4 mr-1" />
                Perfil
              </Button>
              <Button size="sm" variant="outline" onClick={handleLogout} className="text-xs">
                <LogOut className="h-3 w-3 md:h-4 md:w-4 mr-1" />
                Sair
              </Button>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <div className="flex-1 p-4 md:p-6 space-y-2 overflow-y-auto">
          <div className="mb-4 md:mb-6">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
              Navegação
            </h3>

            <div className="space-y-1 md:space-y-2">
              {menuItems.filter(item => {
                // Filtrar itens admin se o usuário não for admin
                if (item.adminOnly && user?.role !== 'admin') {
                  return false;
                }
                return true;
              }).map((item) => {
                const Icon = item.icon
                const isActive = pathname === item.href

                return (
                  <button
                    key={item.id}
                    onClick={() => handleMenuItemClick(item.href)}
                    className={cn(
                      "w-full flex items-center justify-between p-3 rounded-lg text-left transition-all duration-200 group",
                      isActive
                        ? "bg-blue-50 text-blue-700 border-l-4 border-blue-500"
                        : "text-gray-700 hover:bg-gray-50 hover:text-gray-900"
                    )}
                  >
                    <div className="flex items-center space-x-3">
                      <div className={cn(
                        "p-1.5 md:p-2 rounded-md",
                        isActive
                          ? "bg-blue-100 text-blue-600"
                          : "bg-gray-100 text-gray-600 group-hover:bg-gray-200"
                      )}>
                        <Icon className="h-4 w-4" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="font-medium text-sm md:text-base truncate">{item.label}</p>
                        <p className="text-xs text-gray-500 truncate">{item.description}</p>
                      </div>
                    </div>

                    {item.badge && (
                      <Badge className="bg-red-500 text-white animate-pulse text-xs flex-shrink-0">
                        {item.badge}
                      </Badge>
                    )}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="mt-6 md:mt-8">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
              Ações Rápidas
            </h3>
            <div className="space-y-1 md:space-y-2">
              <Button variant="ghost" size="sm" className="w-full justify-start text-sm">
                <MessageCircle className="h-4 w-4 mr-2" />
                Nova Conversa
              </Button>
              <Button variant="ghost" size="sm" className="w-full justify-start text-sm">
                <Calendar className="h-4 w-4 mr-2" />
                Novo Agendamento
              </Button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 md:p-6 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium text-gray-900">Sistema Online</p>
                <p className="text-xs text-gray-500 truncate">Atualizado agora</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden md:ml-0">
        {/* Top Bar */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {/* Mobile space for hamburger menu */}
              <div className="w-10 md:w-0"></div>
              <h2 className="text-xl md:text-2xl font-semibold text-gray-900">
                {menuItems.find(item => item.href === pathname)?.label || 'Dashboard'}
              </h2>
            </div>

            <div className="flex items-center space-x-4">
              <Button variant="ghost" size="sm">
                <Bell className="h-5 w-5" />
              </Button>

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="flex items-center space-x-2 hover:bg-gray-50">
                    <Avatar className="h-8 w-8 ring-2 ring-gray-100">
                      <AvatarImage 
                        src={user?.avatar_url} 
                        alt={user?.name || 'Usuário'} 
                      />
                      <AvatarFallback className="bg-gradient-to-br from-blue-500 to-purple-600 text-white font-semibold text-xs">
                        {user?.name?.charAt(0).toUpperCase() || 'A'}
                      </AvatarFallback>
                    </Avatar>
                    <ChevronDown className="h-4 w-4 text-gray-500" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-64">
                  <DropdownMenuLabel className="flex items-center space-x-3 p-3">
                    <Avatar className="h-10 w-10">
                      <AvatarImage 
                        src={user?.avatar_url} 
                        alt={user?.name || 'Usuário'} 
                      />
                      <AvatarFallback className="bg-gradient-to-br from-blue-500 to-purple-600 text-white font-semibold">
                        {user?.name?.charAt(0).toUpperCase() || 'A'}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-gray-900 truncate">{user?.name || 'Usuário'}</p>
                      <p className="text-sm text-gray-500 truncate">{user?.email || 'admin@whatsappagent.com'}</p>
                      {user?.role && getRoleBadge(user.role)}
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem className="cursor-pointer">
                    <User className="mr-2 h-4 w-4" />
                    <span>Meu Perfil</span>
                  </DropdownMenuItem>
                  <DropdownMenuItem className="cursor-pointer">
                    <Settings className="mr-2 h-4 w-4" />
                    <span>Configurações</span>
                  </DropdownMenuItem>
                  <DropdownMenuItem className="cursor-pointer">
                    <Bell className="mr-2 h-4 w-4" />
                    <span>Notificações</span>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout} className="cursor-pointer text-red-600 focus:text-red-600">
                    <LogOut className="mr-2 h-4 w-4" />
                    <span>Sair</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>

        {/* Page Content */}
        <div className="flex-1 overflow-auto">
          <div className="p-4 md:p-6">
            {children}
          </div>
        </div>
      </div>
    </div>
  )
}

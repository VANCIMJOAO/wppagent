'use client'

import { useState, useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import useAuth from '@/hooks/useAuth'
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
  X
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
  const { user, isAuthenticated, logout } = useAuth()
  const [isLoading, setIsLoading] = useState(true)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    // Verificar se está autenticado
    const checkAuth = async () => {
      if (!isAuthenticated) {
        router.push('/login')
      } else {
        setIsLoading(false)
      }
    }

    checkAuth()
    setIsLoading(false)
  }, [router])

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
    await logout()
    router.push('/login')
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
      href: '/reports',
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
      id: 'diagnostic',
      label: '🔍 Diagnóstico',
      icon: HelpCircle,
      href: '/diagnostic',
      description: 'Backend Status'
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

  if (isLoading || !user) {
    return <div>Carregando...</div>
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
                <Avatar className="h-10 w-10 md:h-12 md:w-12">
                  <AvatarImage src="" />
                  <AvatarFallback className="bg-blue-500 text-white">
                    {user?.username?.charAt(0).toUpperCase() || 'U'}
                  </AvatarFallback>
                </Avatar>
                <div className="absolute -bottom-1 -right-1 w-3 h-3 md:w-4 md:h-4 bg-green-500 rounded-full border-2 border-white"></div>
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-gray-900 text-sm md:text-base truncate">{user?.username || 'Usuário'}</p>
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
              {menuItems.map((item) => {
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
              <h1 className="text-xl md:text-2xl font-semibold text-gray-900">
                {menuItems.find(item => item.href === pathname)?.label || 'Dashboard'}
              </h1>
            </div>

            <div className="flex items-center space-x-4">
              <Button variant="ghost" size="sm">
                <Bell className="h-5 w-5" />
              </Button>

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="flex items-center space-x-2">
                    <Avatar className="h-8 w-8">
                      <AvatarImage src="" />
                      <AvatarFallback>{user?.username?.charAt(0) || 'U'}</AvatarFallback>
                    </Avatar>
                    <ChevronDown className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel>{user?.username || 'Usuário'}</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem>
                    <User className="mr-2 h-4 w-4" />
                    Perfil
                  </DropdownMenuItem>
                  <DropdownMenuItem>
                    <Settings className="mr-2 h-4 w-4" />
                    Configurações
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout}>
                    <LogOut className="mr-2 h-4 w-4" />
                    Sair
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

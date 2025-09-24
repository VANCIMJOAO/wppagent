'use client'

import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { useState, useEffect } from 'react'
import { createQueryClient } from '@/lib/react-query'
import dynamic from 'next/dynamic'

interface ReactQueryProviderProps {
  children: React.ReactNode
}

// Carregar Devtools dinamicamente apenas no cliente
const DevTools = dynamic(
  () => import('@tanstack/react-query-devtools').then((d) => ({
    default: d.ReactQueryDevtools,
  })),
  { ssr: false }
)

export function ReactQueryProvider({ children }: ReactQueryProviderProps) {
  // Usar useState para garantir que o queryClient seja estável
  const [client] = useState(() => createQueryClient())
  const [isClient, setIsClient] = useState(false)

  // Garantir que o componente só renderize no cliente
  useEffect(() => {
    setIsClient(true)
  }, [])

  return (
    <QueryClientProvider client={client}>
      {children}
      {/* Devtools apenas em desenvolvimento e no cliente */}
      {isClient && process.env.NODE_ENV === 'development' && (
        <DevTools
          initialIsOpen={false}
          position="bottom"
        />
      )}
    </QueryClientProvider>
  )
}

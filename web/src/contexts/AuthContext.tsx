import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { User, AuthTokens, LoginCredentials, RegisterData, authApi, authStorage, setupAuthInterceptor } from '../lib/auth'

interface AuthContextType {
  user: User | null
  tokens: AuthTokens | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (credentials: LoginCredentials) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => Promise<void>
  error: string | null
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [tokens, setTokens] = useState<AuthTokens | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Configurar interceptor de auth al montar el componente
  useEffect(() => {
    setupAuthInterceptor()
  }, [])

  // Verificar si hay tokens almacenados al cargar la aplicación
  useEffect(() => {
    const initializeAuth = async () => {
      const storedTokens = authStorage.getTokens()
      if (storedTokens) {
        setTokens(storedTokens)
        try {
          const currentUser = await authApi.getCurrentUser()
          setUser(currentUser)
        } catch (err) {
          // Token inválido, limpiar almacenamiento
          authStorage.clearTokens()
          setTokens(null)
        }
      }
      setIsLoading(false)
    }

    initializeAuth()
  }, [])

  const login = async (credentials: LoginCredentials) => {
    setIsLoading(true)
    setError(null)
    try {
      const authTokens = await authApi.login(credentials)
      authStorage.setTokens(authTokens)
      setTokens(authTokens)

      // Obtener información del usuario
      const currentUser = await authApi.getCurrentUser()
      setUser(currentUser)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al iniciar sesión')
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  const register = async (data: RegisterData) => {
    setIsLoading(true)
    setError(null)
    try {
      const authTokens = await authApi.register(data)
      authStorage.setTokens(authTokens)
      setTokens(authTokens)

      // Obtener información del usuario
      const currentUser = await authApi.getCurrentUser()
      setUser(currentUser)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al registrarse')
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    setIsLoading(true)
    try {
      await authApi.logout()
      setUser(null)
      setTokens(null)
    } catch (err) {
      console.error('Error during logout:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const value: AuthContextType = {
    user,
    tokens,
    isLoading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    error
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

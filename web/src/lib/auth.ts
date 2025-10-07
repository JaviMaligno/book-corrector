import { api } from './api'

export interface User {
  id: string
  email: string
}

export interface AuthTokens {
  access_token: string
  token_type: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
}

// Almacenar tokens en localStorage
const TOKEN_KEY = 'auth_tokens'

export const authStorage = {
  getTokens(): AuthTokens | null {
    try {
      const tokens = localStorage.getItem(TOKEN_KEY)
      return tokens ? JSON.parse(tokens) : null
    } catch {
      return null
    }
  },

  setTokens(tokens: AuthTokens): void {
    localStorage.setItem(TOKEN_KEY, JSON.stringify(tokens))
  },

  clearTokens(): void {
    localStorage.removeItem(TOKEN_KEY)
  },

  getAuthHeader(): string | null {
    const tokens = this.getTokens()
    return tokens ? `${tokens.token_type} ${tokens.access_token}` : null
  }
}

// Configurar axios para incluir el token de autorización automáticamente
export const setupAuthInterceptor = () => {
  api.interceptors.request.use((config) => {
    const authHeader = authStorage.getAuthHeader()
    if (authHeader) {
      config.headers.Authorization = authHeader
    }
    return config
  })
}

// Funciones de autenticación
export const authApi = {
  async register(data: RegisterData): Promise<AuthTokens> {
    const response = await api.post<AuthTokens>('/auth/register', data)
    return response.data
  },

  async login(credentials: LoginCredentials): Promise<AuthTokens> {
    const response = await api.post<AuthTokens>('/auth/login', credentials)
    return response.data
  },

  async logout(): Promise<void> {
    authStorage.clearTokens()
  },

  async getCurrentUser(): Promise<User | null> {
    try {
      const response = await api.get<User>('/auth/me')
      return response.data
    } catch {
      return null
    }
  }
}

import apiClient from './client'

export interface User {
  id: number
  email: string
  full_name: string
  is_active: boolean
  created_at: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  full_name: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export const authApi = {
  login: async (credentials: LoginCredentials): Promise<TokenResponse> => {
    const formData = new FormData()
    formData.append('username', credentials.email)
    formData.append('password', credentials.password)

    const response = await apiClient.post('/api/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
    return response.data
  },

  register: async (data: RegisterData): Promise<User> => {
    const response = await apiClient.post('/api/auth/register', data)
    return response.data
  },

  logout: async (): Promise<void> => {
    await apiClient.post('/api/auth/logout')
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get('/api/users/me')
    return response.data
  },
}

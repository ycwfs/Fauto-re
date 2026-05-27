import apiClient from './client'

export interface Paper {
  id: number
  arxiv_id: string
  title: string
  authors: string
  abstract: string
  categories: string
  published_date: string
  pdf_url: string
  created_at: string
}

export interface PaperListResponse {
  items: Paper[]
  total: number
  page: number
  size: number
  pages: number
}

export interface PaperStats {
  total_papers: number
  papers_this_week: number
  papers_this_month: number
  categories: Record<string, number>
}

export const papersApi = {
  listPapers: async (page: number = 1, size: number = 20): Promise<PaperListResponse> => {
    const response = await apiClient.get('/api/papers/', {
      params: { page, size }
    })
    return response.data
  },

  getPaper: async (paperId: number): Promise<Paper> => {
    const response = await apiClient.get(`/api/papers/${paperId}`)
    return response.data
  },

  fetchPapers: async (): Promise<{ status: string; task_id: string }> => {
    const response = await apiClient.post('/api/papers/fetch')
    return response.data
  },

  getStats: async (): Promise<PaperStats> => {
    const response = await apiClient.get('/api/papers/stats')
    return response.data
  },
}

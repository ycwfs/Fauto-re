import apiClient from './client'

export interface Paper {
  id: number
  arxiv_id: string
  title: string
  authors: string[]
  abstract?: string
  categories: string[]
  published_date?: string
  pdf_url?: string
  fetched_at: string
}

export interface PaperListResponse {
  papers: Paper[]
  total: number
  page: number
  page_size: number
}

export interface PaperStats {
  total_papers: number
  categories: Record<string, number>
}

export const papersApi = {
  listPapers: async (page: number = 1, pageSize: number = 20, category?: string): Promise<PaperListResponse> => {
    const params: any = { page, page_size: pageSize }
    if (category) params.category = category
    const response = await apiClient.get('/api/papers/', { params })
    return response.data
  },

  getPaper: async (paperId: number): Promise<Paper> => {
    const response = await apiClient.get(`/api/papers/${paperId}`)
    return response.data
  },

  fetchPapers: async (): Promise<{ message: string; task_id: string }> => {
    const response = await apiClient.post('/api/papers/fetch')
    return response.data
  },

  getStats: async (): Promise<PaperStats> => {
    const response = await apiClient.get('/api/papers/stats/summary')
    return response.data
  },
}

import { useQuery } from '@tanstack/react-query'
import { papersApi } from '../../api/papers'
import { useAuthStore } from '../../store/auth'
import { useNavigate } from 'react-router-dom'
import { useState } from 'react'

export default function DashboardPage() {
  const navigate = useNavigate()
  const { user, clearAuth } = useAuthStore()
  const [page, setPage] = useState(1)

  const { data: stats } = useQuery({
    queryKey: ['paper-stats'],
    queryFn: () => papersApi.getStats(),
  })

  const { data: papersData, isLoading } = useQuery({
    queryKey: ['papers', page],
    queryFn: () => papersApi.listPapers(page, 10),
  })

  const handleLogout = () => {
    clearAuth()
    navigate('/login')
  }

  const handleFetchPapers = async () => {
    try {
      await papersApi.fetchPapers()
      alert('Paper fetching started! Check back in a few minutes.')
    } catch (err) {
      alert('Failed to start paper fetching')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Full-Auto-Research</h1>
          <div className="flex items-center gap-4">
            <span className="text-gray-700">Welcome, {user?.username}</span>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Total Papers</h3>
            <p className="text-3xl font-bold text-blue-600">{stats?.total_papers || 0}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Categories</h3>
            <p className="text-3xl font-bold text-green-600">
              {stats ? Object.keys(stats.categories).length : 0}
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Actions</h3>
            <button
              onClick={handleFetchPapers}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Fetch New Papers
            </button>
          </div>
        </div>

        {/* Papers List */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-bold text-gray-900">Recent Papers</h2>
          </div>

          {isLoading ? (
            <div className="p-6 text-center text-gray-500">Loading papers...</div>
          ) : papersData?.papers.length === 0 ? (
            <div className="p-6 text-center text-gray-500">
              No papers yet. Click "Fetch New Papers" to get started!
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {papersData?.papers.map((paper) => (
                <div key={paper.id} className="p-6 hover:bg-gray-50">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {paper.title}
                  </h3>
                  <p className="text-sm text-gray-600 mb-2">
                    {paper.authors.join(', ')}
                  </p>
                  <p className="text-sm text-gray-700 mb-3 line-clamp-3">
                    {paper.abstract}
                  </p>
                  <div className="flex gap-2 flex-wrap">
                    {paper.categories.map((cat) => (
                      <span
                        key={cat}
                        className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded"
                      >
                        {cat}
                      </span>
                    ))}
                  </div>
                  {paper.pdf_url && (
                    <a
                      href={paper.pdf_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-3 inline-block text-blue-600 hover:underline text-sm"
                    >
                      View PDF →
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {papersData && papersData.total > 10 && (
            <div className="px-6 py-4 border-t border-gray-200 flex justify-between items-center">
              <button
                onClick={() => setPage(page - 1)}
                disabled={page === 1}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <span className="text-gray-700">
                Page {page} of {Math.ceil(papersData.total / 10)}
              </span>
              <button
                onClick={() => setPage(page + 1)}
                disabled={page >= Math.ceil(papersData.total / 10)}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

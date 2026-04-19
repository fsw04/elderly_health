import axios from 'axios'

export const http = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 10000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('eh_admin_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem('eh_admin_token')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)

export async function adminLogin(username: string, password: string) {
  const { data } = await http.post('/admin/login', { username, password })
  return data
}

export async function getUsers(params: Record<string, string | number>) {
  const { data } = await http.get('/admin/users', { params })
  return data
}

export async function createUser(payload: Record<string, unknown>) {
  const { data } = await http.post('/admin/users', payload)
  return data
}

export async function updateUser(id: number, payload: Record<string, unknown>) {
  const { data } = await http.put(`/admin/users/${id}`, payload)
  return data
}

export async function deleteUser(id: number) {
  const { data } = await http.delete(`/admin/users/${id}`)
  return data
}

export async function getUserDetail(id: number) {
  const { data } = await http.get(`/admin/users/${id}`)
  return data
}

export async function getUserSessions(id: number, params: Record<string, string | number>) {
  const { data } = await http.get(`/admin/users/${id}/sessions`, { params })
  return data
}

export async function getUserReports(id: number, params: Record<string, string | number>) {
  const { data } = await http.get(`/admin/users/${id}/reports`, { params })
  return data
}

export async function getUserReminders(id: number, params: Record<string, string | number>) {
  const { data } = await http.get(`/admin/users/${id}/reminders`, { params })
  return data
}

export async function getReports(params: Record<string, string | number>) {
  const { data } = await http.get('/admin/reports', { params })
  return data
}

export async function getReportDetail(reportId: string) {
  const { data } = await http.get(`/admin/reports/${reportId}`)
  return data
}

export async function updateReportDoctorSummary(reportId: string, payload: Record<string, unknown>) {
  const { data } = await http.put(`/admin/reports/${reportId}/doctor-summary`, payload)
  return data
}

export async function getReminders(params: Record<string, string | number>) {
  const { data } = await http.get('/admin/reminder-tasks', { params })
  return data
}

export async function handleReminder(taskId: number, payload: { action: string; channel: string; note: string }) {
  const { data } = await http.post(`/admin/reminder-tasks/${taskId}/handle`, payload)
  return data
}

export async function getAudit(params: Record<string, string | number>) {
  const { data } = await http.get('/admin/audit', { params })
  return data
}

import { request } from './request';

export const mpApi = {
  login: (code: string) => request('/mp/login', 'POST', { code }),
  bindPhone: (phone: string, smsCode: string) => request('/mp/bind-phone', 'POST', { phone, smsCode }),
  sendSms: (phone: string) => request('/mp/sms/send', 'POST', { phone, scene: 'BIND_PHONE' }),
  home: () => request('/mp/home'),
  me: () => request('/mp/me'),
  updateMe: (payload: any) => request('/mp/me', 'PUT', payload),
  reports: (params: any) => request(`/mp/reports?page=${params.page}&pageSize=${params.pageSize}&onlyAbnormal=${params.onlyAbnormal || 0}`),
  reportDetail: (id: string) => request(`/mp/reports/${id}`),
  notifications: (params: any) => request(`/mp/notifications?page=${params.page}&pageSize=${params.pageSize}&onlyUnread=${params.onlyUnread || 0}`),
  readNotification: (id: number) => request(`/mp/notifications/${id}/read`, 'POST'),
  familyRequests: (role = 'target', status = '', page = 1, pageSize = 20) =>
    request(`/mp/family-link-requests?role=${role}&status=${status}&page=${page}&pageSize=${pageSize}`),
  approveFamilyRequest: (requestId: number) => request(`/mp/family-link-requests/${requestId}/approve`, 'POST'),
  rejectFamilyRequest: (requestId: number, note = '') => request(`/mp/family-link-requests/${requestId}/reject`, 'POST', { note }),
  cancelFamilyRequest: (requestId: number) => request(`/mp/family-link-requests/${requestId}/cancel`, 'POST'),
  familyLinks: (page = 1, pageSize = 20) => request(`/mp/family-links?page=${page}&pageSize=${pageSize}`),
  removeFamilyLink: (linkId: number) => request(`/mp/family-links/${linkId}`, 'DELETE'),
  createFamilyRequest: (targetPhone: string, relationType = 'child') => request('/mp/family-link-requests', 'POST', { targetPhone, relationType }),
};

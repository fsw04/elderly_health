const { request } = require('./request');

const mpApi = {
  login: (code) => request('/mp/login', 'POST', { code }),
  bindPhone: (phone, smsCode) => request('/mp/bind-phone', 'POST', { phone, smsCode }),
  sendSms: (phone) => request('/mp/sms/send', 'POST', { phone, scene: 'BIND_PHONE' }),
  home: () => request('/mp/home'),
  me: () => request('/mp/me'),
  updateMe: (payload) => request('/mp/me', 'PUT', payload),
  reports: (params) => request(`/mp/reports?page=${params.page}&pageSize=${params.pageSize}&onlyAbnormal=${params.onlyAbnormal || 0}`),
  reportDetail: (id) => request(`/mp/reports/${id}`),
  notifications: (params) => request(`/mp/notifications?page=${params.page}&pageSize=${params.pageSize}&onlyUnread=${params.onlyUnread || 0}`),
  readNotification: (id) => request(`/mp/notifications/${id}/read`, 'POST'),
  familyRequests: (role = 'target', status = '', page = 1, pageSize = 20) =>
    request(`/mp/family-link-requests?role=${role}&status=${status}&page=${page}&pageSize=${pageSize}`),
  approveFamilyRequest: (requestId) => request(`/mp/family-link-requests/${requestId}/approve`, 'POST'),
  rejectFamilyRequest: (requestId, note = '') => request(`/mp/family-link-requests/${requestId}/reject`, 'POST', { note }),
  cancelFamilyRequest: (requestId) => request(`/mp/family-link-requests/${requestId}/cancel`, 'POST'),
  familyLinks: (page = 1, pageSize = 20) => request(`/mp/family-links?page=${page}&pageSize=${pageSize}`),
  removeFamilyLink: (linkId) => request(`/mp/family-links/${linkId}`, 'DELETE'),
  createFamilyRequest: (targetPhone, relationType = 'child') => request('/mp/family-link-requests', 'POST', { targetPhone, relationType }),
};

module.exports = {
  mpApi,
};

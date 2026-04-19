function getBaseUrl() {
  return wx.getStorageSync('eh_base_url') || 'http://localhost:8000/api';
}

export function request<T = any>(url: string, method: WechatMiniprogram.RequestOption['method'] = 'GET', data?: any): Promise<T> {
  const token = wx.getStorageSync('eh_token') || '';
  const baseUrl = getBaseUrl();
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${baseUrl}${url}`,
      method,
      data,
      timeout: 10000,
      header: {
        Authorization: token ? `Bearer ${token}` : '',
      },
      success: (res) => {
        if (res.statusCode === 401) {
          wx.removeStorageSync('eh_token');
          wx.showToast({ title: '登录已失效', icon: 'none' });
          reject(new Error('401'));
          return;
        }
        if (res.statusCode && res.statusCode >= 400) {
          reject(new Error(String((res.data as any)?.detail || 'request_failed')));
          return;
        }
        resolve(res.data as T);
      },
      fail: reject,
    });
  });
}

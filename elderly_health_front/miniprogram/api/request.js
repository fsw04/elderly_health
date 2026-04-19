function getBaseUrl() {
  return wx.getStorageSync('eh_base_url') || 'http://localhost:8000/api';
}

function request(url, method, data) {
  const m = method || 'GET';
  const token = wx.getStorageSync('eh_token') || '';
  const baseUrl = getBaseUrl();
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${baseUrl}${url}`,
      method: m,
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
          const detail = (res.data && res.data.detail) || 'request_failed';
          reject(new Error(String(detail)));
          return;
        }
        resolve(res.data);
      },
      fail: reject,
    });
  });
}

module.exports = {
  request,
};

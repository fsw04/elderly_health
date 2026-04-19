function getSafeApp() {
  try {
    return getApp() || { globalData: {} };
  } catch (e) {
    return { globalData: {} };
  }
}

function getBaseUrl(app) {
  return (app.globalData && app.globalData.baseUrl) || wx.getStorageSync('eh_base_url') || 'http://localhost:8000/api';
}

function isValidPhone(phone) {
  return /^1\d{10}$/.test((phone || '').trim());
}

Page({
  data: { phone: '', loading: false },
  onShow() {
    const app = getSafeApp();
    if (app.globalData && app.globalData.token) {
      wx.switchTab({ url: '/pages/index/index' });
    }
  },
  onPhoneInput(e) {
    this.setData({ phone: e.detail.value || '' });
  },
  doLogin() {
    if (this.data.loading) return;
    const phone = (this.data.phone || '').trim();
    if (!isValidPhone(phone)) {
      wx.showToast({ title: '请输入11位手机号', icon: 'none' });
      return;
    }
    this.setData({ loading: true });
    const app = getSafeApp();
    const baseUrl = getBaseUrl(app);
    wx.request({
      url: `${baseUrl}/mp/account/login`,
      method: 'POST',
      data: { phone },
      success: (resp) => {
        try {
          if (resp.statusCode === 404) {
            wx.showToast({ title: '账号不存在，请先注册', icon: 'none' });
            setTimeout(() => {
              wx.navigateTo({ url: `/pages/auth/register/index?phone=${phone}` });
            }, 500);
            return;
          }
          const data = resp.data || {};
          if (resp.statusCode >= 400 || !data.token) {
            wx.showToast({ title: '登录失败', icon: 'none' });
            return;
          }
          wx.setStorageSync('eh_token', data.token);
          wx.setStorageSync('eh_base_url', baseUrl);
          if (app.globalData) app.globalData.token = data.token;
          wx.switchTab({ url: '/pages/index/index' });
        } finally {
          this.setData({ loading: false });
        }
      },
      fail: () => {
        this.setData({ loading: false });
        wx.showToast({ title: '网络错误', icon: 'none' });
      }
    });
  },
  goRegister() {
    const phone = encodeURIComponent((this.data.phone || '').trim());
    wx.navigateTo({ url: `/pages/auth/register/index?phone=${phone}` });
  }
});

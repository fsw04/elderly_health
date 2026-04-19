function isValidPhone(phone: string) {
  return /^1\d{10}$/.test((phone || '').trim());
}

Page({
  data: { phone: '', loading: false },
  onShow() {
    const app = getApp<IAppOption>();
    if (app.globalData.token) {
      wx.switchTab({ url: '/pages/index/index' });
    }
  },
  onPhoneInput(e: any) {
    this.setData({ phone: e.detail.value || '' });
  },
  async doLogin() {
    if (this.data.loading) return;
    const phone = (this.data.phone || '').trim();
    if (!isValidPhone(phone)) {
      wx.showToast({ title: '请输入11位手机号', icon: 'none' });
      return;
    }
    this.setData({ loading: true });
    try {
      const { request } = require('../../../api/request');
      const res = await request('/mp/account/login', 'POST', { phone });
      wx.setStorageSync('eh_token', res.token);
      const app = getApp<IAppOption>();
      app.globalData.token = res.token;
      wx.switchTab({ url: '/pages/index/index' });
    } catch (e: any) {
      wx.showToast({ title: e?.message || '登录失败', icon: 'none' });
    } finally {
      this.setData({ loading: false });
    }
  },
  goRegister() {
    const phone = encodeURIComponent((this.data.phone || '').trim());
    wx.navigateTo({ url: `/pages/auth/register/index?phone=${phone}` });
  }
});

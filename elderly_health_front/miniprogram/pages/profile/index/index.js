function normalizeBirthDate(value) {
  return String(value || '').replace(/-/g, '');
}

function isValidBirthDate(value) {
  if (!value) return true;
  return /^\d{8}$/.test(value);
}

function isValidIdCard(value) {
  if (!value) return true;
  return /^(?:\d{15}|\d{17}[\dXx])$/.test(value);
}

Page({
  data: { form: {} },
  onShow() { this.loadData(); },
  loadData() {
    const app = getApp() || {};
    const baseUrl = (app.globalData && app.globalData.baseUrl) || wx.getStorageSync('eh_base_url') || 'http://localhost:8000/api';
    const token = wx.getStorageSync('eh_token') || '';
    wx.request({
      url: `${baseUrl}/mp/me`,
      method: 'GET',
      header: { Authorization: token ? `Bearer ${token}` : '' },
      success: (res) => {
        const raw = res.data || {};
        const form = {
          ...raw,
          age: raw.age,
          birthDate: normalizeBirthDate(raw.birthDate || raw.birth_date || ''),
          idCard: raw.idCard || raw.id_card || '',
          currentAddress: raw.currentAddress || raw.current_address || ''
        };
        this.setData({ form });
      },
    });
  },
  onInput(e) {
    const field = e.currentTarget.dataset.field;
    this.setData({ ['form.' + field]: e.detail.value });
  },
  save() {
    const payload = {
      name: this.data.form.name || '',
      birthDate: normalizeBirthDate(this.data.form.birthDate || ''),
      idCard: (this.data.form.idCard || '').trim(),
      currentAddress: (this.data.form.currentAddress || '').trim(),
    };
    if (!isValidBirthDate(payload.birthDate)) {
      wx.showToast({ title: '生日格式应为YYYYMMDD', icon: 'none' });
      return;
    }
    if (!isValidIdCard(payload.idCard)) {
      wx.showToast({ title: '证件号格式不正确', icon: 'none' });
      return;
    }

    const app = getApp() || {};
    const baseUrl = (app.globalData && app.globalData.baseUrl) || wx.getStorageSync('eh_base_url') || 'http://localhost:8000/api';
    const token = wx.getStorageSync('eh_token') || '';
    wx.request({
      url: `${baseUrl}/mp/me`,
      method: 'PUT',
      data: payload,
      header: { Authorization: token ? `Bearer ${token}` : '' },
      success: () => wx.showToast({ title: '已保存', icon: 'none' }),
      fail: () => wx.showToast({ title: '保存失败', icon: 'none' }),
    });
  },
  logout() {
    wx.showModal({
      title: '确认退出',
      content: '是否退出当前账号？',
      success: (res) => {
        if (!res.confirm) return;
        wx.removeStorageSync('eh_token');
        const app = getApp();
        if (app && app.globalData) app.globalData.token = '';
        wx.reLaunch({ url: '/pages/auth/login/index' });
      }
    });
  }
});

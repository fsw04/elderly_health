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

function isValidBirthDate(v) {
  const value = (v || '').trim();
  if (!/^\d{8}$/.test(value)) return false;
  const y = Number(value.slice(0, 4));
  const m = Number(value.slice(4, 6));
  const d = Number(value.slice(6, 8));
  const dt = new Date(y, m - 1, d);
  return dt.getFullYear() === y && dt.getMonth() + 1 === m && dt.getDate() === d;
}

const GENDER_VALUES = ['M', 'F', 'U'];

Page({
  data: {
    name: '',
    birthDate: '',
    phone: '',
    genderIndex: 0,
    genderOptions: ['男', '女', '未知'],
    submitLoading: false
  },
  onLoad(query) {
    if (query && query.phone) {
      this.setData({ phone: decodeURIComponent(query.phone) });
    }
  },
  onName(e) {
    this.setData({ name: e.detail.value || '' });
  },
  onBirthDate(e) {
    this.setData({ birthDate: e.detail.value || '' });
  },
  onPhone(e) {
    this.setData({ phone: e.detail.value || '' });
  },
  onGenderChange(e) {
    this.setData({ genderIndex: Number(e.detail.value || 0) });
  },
  submit() {
    if (this.data.submitLoading) return;
    const name = (this.data.name || '').trim();
    const birthDate = (this.data.birthDate || '').trim();
    const phone = (this.data.phone || '').trim();
    const gender = GENDER_VALUES[this.data.genderIndex] || 'M';

    if (!name) {
      wx.showToast({ title: '请输入姓名', icon: 'none' });
      return;
    }
    if (!isValidBirthDate(birthDate)) {
      wx.showToast({ title: '生日格式应为YYYYMMDD', icon: 'none' });
      return;
    }
    if (!isValidPhone(phone)) {
      wx.showToast({ title: '请输入11位手机号', icon: 'none' });
      return;
    }

    const app = getSafeApp();
    const baseUrl = getBaseUrl(app);
    this.setData({ submitLoading: true });
    wx.request({
      url: `${baseUrl}/mp/account/register`,
      method: 'POST',
      data: { phone, name, birthDate, gender },
      success: (resp) => {
        const data = resp.data || {};
        if (resp.statusCode === 409) {
          wx.showToast({ title: '手机号已注册，请直接登录', icon: 'none' });
          setTimeout(() => {
            wx.reLaunch({ url: '/pages/auth/login/index' });
          }, 500);
          return;
        }
        if (resp.statusCode >= 400 || !data.token) {
          wx.showToast({ title: '注册失败', icon: 'none' });
          return;
        }
        wx.setStorageSync('eh_token', data.token);
        wx.setStorageSync('eh_base_url', baseUrl);
        if (app.globalData) app.globalData.token = data.token;
        wx.showToast({ title: '注册成功', icon: 'none' });
        wx.switchTab({ url: '/pages/index/index' });
      },
      fail: () => wx.showToast({ title: '注册失败', icon: 'none' }),
      complete: () => this.setData({ submitLoading: false })
    });
  }
});

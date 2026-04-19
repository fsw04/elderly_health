function isValidPhone(phone: string) {
  return /^1\d{10}$/.test((phone || '').trim());
}

function isValidBirthDate(v: string) {
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
  onLoad(query: any) {
    if (query?.phone) {
      this.setData({ phone: decodeURIComponent(query.phone) });
    }
  },
  onName(e: any) { this.setData({ name: e.detail.value || '' }); },
  onBirthDate(e: any) { this.setData({ birthDate: e.detail.value || '' }); },
  onPhone(e: any) { this.setData({ phone: e.detail.value || '' }); },
  onGenderChange(e: any) { this.setData({ genderIndex: Number(e.detail.value || 0) }); },
  async submit() {
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

    this.setData({ submitLoading: true });
    try {
      const { request } = require('../../../api/request');
      const res = await request('/mp/account/register', 'POST', { phone, name, birthDate, gender });
      wx.setStorageSync('eh_token', res.token);
      const app = getApp<IAppOption>();
      app.globalData.token = res.token;
      wx.showToast({ title: '注册成功', icon: 'none' });
      wx.switchTab({ url: '/pages/index/index' });
    } catch (e: any) {
      wx.showToast({ title: e?.message || '注册失败', icon: 'none' });
    } finally {
      this.setData({ submitLoading: false });
    }
  },
});

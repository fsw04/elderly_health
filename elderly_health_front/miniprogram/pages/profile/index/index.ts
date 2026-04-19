function normalizeBirthDate(value: string) {
  return String(value || '').replace(/-/g, '');
}

function isValidBirthDate(value: string) {
  if (!value) return true;
  return /^\d{8}$/.test(value);
}

function isValidIdCard(value: string) {
  if (!value) return true;
  return /^(?:\d{15}|\d{17}[\dXx])$/.test(value);
}

Page({
  data: { form: {} as any },
  onShow() { this.loadData(); },
  async loadData() {
    const { mpApi } = require('../../../api/mp');
    const me = await mpApi.me();
    const form = {
      ...me,
      age: me.age,
      birthDate: normalizeBirthDate(me.birthDate || me.birth_date || ''),
      idCard: me.idCard || me.id_card || '',
      currentAddress: me.currentAddress || me.current_address || ''
    };
    this.setData({ form });
  },
  onInput(e: any) {
    const field = e.currentTarget.dataset.field;
    this.setData({ ['form.' + field]: e.detail.value });
  },
  async save() {
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

    const { mpApi } = require('../../../api/mp');
    await mpApi.updateMe(payload);
    wx.showToast({ title: '已保存' });
  },
  logout() {
    wx.showModal({
      title: '确认退出',
      content: '是否退出当前账号？',
      success: (res) => {
        if (!res.confirm) return;
        wx.removeStorageSync('eh_token');
        const app = getApp<IAppOption>();
        if (app && app.globalData) {
          app.globalData.token = '';
        }
        wx.reLaunch({ url: '/pages/auth/login/index' });
      }
    });
  }
});

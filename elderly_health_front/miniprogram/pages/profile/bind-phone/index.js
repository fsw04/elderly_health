Page({
  data: { phone: '', smsCode: '' },
  onPhone(e) { this.setData({ phone: e.detail.value }); },
  onCode(e) { this.setData({ smsCode: e.detail.value }); },
  async sendSms() {
    const { mpApi } = require('../../../api/mp');
    await mpApi.sendSms(this.data.phone);
    wx.showToast({ title: '已发送', icon: 'none' });
  },
  async submit() {
    const { mpApi } = require('../../../api/mp');
    await mpApi.bindPhone(this.data.phone, this.data.smsCode);
    wx.showToast({ title: '绑定成功' });
    wx.navigateBack();
  }
});

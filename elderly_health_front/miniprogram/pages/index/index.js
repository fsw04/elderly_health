Page({
  data: { home: { me: {}, counters: {}, recentReport: null } },
  onShow() {
    const app = getApp() || {};
    if (!app.globalData || !app.globalData.token) {
      wx.reLaunch({ url: '/pages/auth/login/index' });
      return;
    }
    this.loadData();
  },
  async loadData() {
    const { mpApi } = require('../../api/mp');
    const res = await mpApi.home();
    this.setData({ home: res.data || {} });
  },
  goReports() { wx.switchTab({ url: '/pages/reports/list/index' }); },
  goFamily() { wx.navigateTo({ url: '/pages/family/index' }); },
  goReportDetail(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: '/pages/reports/detail/index?id=' + id });
  }
});

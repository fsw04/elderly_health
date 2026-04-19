Page({
  data: { onlyAbnormal: false, items: [] as any[] },
  onShow() { this.loadData(); },
  async loadData() {
    const { mpApi } = require('../../../api/mp');
    const res = await mpApi.reports({ page: 1, pageSize: 20, onlyAbnormal: this.data.onlyAbnormal ? 1 : 0 });
    this.setData({ items: res.data.items || [] });
  },
  toggleAbnormal(e: any) { this.setData({ onlyAbnormal: e.detail.value }, () => this.loadData()); },
  goDetail(e: any) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: '/pages/reports/detail/index?id=' + id });
  }
});

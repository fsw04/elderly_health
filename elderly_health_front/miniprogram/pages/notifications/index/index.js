Page({
  data: { items: [] },
  onShow() { this.loadData(); },
  async loadData() {
    const { mpApi } = require('../../../api/mp');
    const res = await mpApi.notifications({ page: 1, pageSize: 30, onlyUnread: 0 });
    this.setData({ items: res.data.items || [] });
  },
  async markRead(e) {
    const { mpApi } = require('../../../api/mp');
    await mpApi.readNotification(e.currentTarget.dataset.id);
    this.loadData();
  }
});

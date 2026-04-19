Page({
  data: {
    targetPhone: '',
    requests: [],
    targetRequests: [],
    links: [],
    pageSize: 10,
    requesterPage: 1,
    targetPage: 1,
    linkPage: 1,
    requesterHasMore: false,
    targetHasMore: false,
    linkHasMore: false,
    requesterLoadingMore: false,
    targetLoadingMore: false,
    linkLoadingMore: false,
    statusOptions: ['pending', 'rejected', 'expired'],
    requesterStatus: 'pending',
    targetStatus: 'pending',
    requesterStatusIndex: 0,
    targetStatusIndex: 0,
    loading: false,
    errorMsg: '',
    showBackTop: false,
    lastCopiedRequestId: '',
    lastCopyAt: 0,
    actionKey: '',
  },
  onShow() { this.loadData(); },
  onPullDownRefresh() {
    this.loadData().finally(() => wx.stopPullDownRefresh());
  },
  onPageScroll(e) {
    const shouldShow = (e.scrollTop || 0) > 280;
    if (shouldShow !== this.data.showBackTop) {
      this.setData({ showBackTop: shouldShow });
    }
  },
  onPhone(e) { this.setData({ targetPhone: e.detail.value }); },
  onRequesterStatusChange(e) {
    const idx = Number(e.detail.value || 0);
    const status = this.data.statusOptions[idx] || 'pending';
    this.setData({ requesterStatus: status, requesterStatusIndex: idx }, () => this.loadData());
  },
  onTargetStatusChange(e) {
    const idx = Number(e.detail.value || 0);
    const status = this.data.statusOptions[idx] || 'pending';
    this.setData({ targetStatus: status, targetStatusIndex: idx }, () => this.loadData());
  },
  mapErrorMessage(err) {
    const msg = String(err?.message || '');
    if (msg.includes('AUTH_403')) return '无权限执行该操作';
    if (msg.includes('FAM_409_PENDING_EXISTS')) return '你已发起过待处理申请';
    if (msg.includes('FAM_410_REQUEST_EXPIRED')) return '申请已失效，请刷新后重试';
    if (msg.includes('404')) return '数据不存在或已被删除';
    return '操作失败，请稍后重试';
  },
  async loadData() {
    const { mpApi } = require('../../api/mp');
    this.setData({ loading: true, errorMsg: '' });
    try {
      const pageSize = this.data.pageSize;
      const [reqRes, targetRes, linkRes] = await Promise.all([
        mpApi.familyRequests('requester', this.data.requesterStatus, 1, pageSize),
        mpApi.familyRequests('target', this.data.targetStatus, 1, pageSize),
        mpApi.familyLinks(1, pageSize)
      ]);
      const reqData = reqRes.data || {};
      const targetData = targetRes.data || {};
      const linkData = linkRes.data || {};
      this.setData({
        requests: reqData.items || [],
        targetRequests: targetData.items || [],
        links: linkData.items || [],
        requesterPage: 1,
        targetPage: 1,
        linkPage: 1,
        requesterHasMore: (reqData.page || 1) * (reqData.pageSize || pageSize) < (reqData.total || 0),
        targetHasMore: (targetData.page || 1) * (targetData.pageSize || pageSize) < (targetData.total || 0),
        linkHasMore: (linkData.page || 1) * (linkData.pageSize || pageSize) < (linkData.total || 0),
      });
    } catch (e) {
      this.setData({ errorMsg: this.mapErrorMessage(e) });
    } finally {
      this.setData({ loading: false });
    }
  },
  async createRequest() {
    if (this.data.actionKey) return;
    const { mpApi } = require('../../api/mp');
    this.setData({ actionKey: 'create' });
    try {
      await mpApi.createFamilyRequest(this.data.targetPhone);
      wx.showToast({ title: '申请已提交', icon: 'none' });
      this.setData({ targetPhone: '' });
      this.loadData();
    } catch (e) {
      wx.showToast({ title: this.mapErrorMessage(e), icon: 'none' });
    } finally {
      this.setData({ actionKey: '' });
    }
  },
  async approveRequest(e) {
    if (this.data.actionKey) return;
    const { mpApi } = require('../../api/mp');
    const id = e.currentTarget.dataset.id;
    const key = `approve-${id}`;
    this.setData({ actionKey: key });
    try {
      await mpApi.approveFamilyRequest(id);
      wx.showToast({ title: '已同意', icon: 'none' });
      this.loadData();
    } catch (e) {
      wx.showToast({ title: this.mapErrorMessage(e), icon: 'none' });
    } finally {
      this.setData({ actionKey: '' });
    }
  },
  async rejectRequest(e) {
    if (this.data.actionKey) return;
    const { mpApi } = require('../../api/mp');
    const id = e.currentTarget.dataset.id;
    const key = `reject-${id}`;
    this.setData({ actionKey: key });
    try {
      await mpApi.rejectFamilyRequest(id, '已拒绝');
      wx.showToast({ title: '已拒绝', icon: 'none' });
      this.loadData();
    } catch (e) {
      wx.showToast({ title: this.mapErrorMessage(e), icon: 'none' });
    } finally {
      this.setData({ actionKey: '' });
    }
  },
  showRequesterDetail(e) {
    const idx = Number(e.currentTarget.dataset.index || 0);
    const item = this.data.requests[idx];
    if (!item) return;
    wx.showModal({
      title: '申请详情',
      showCancel: false,
      content:
        `申请ID：${item.id || '--'}\n` +
        `申请人ID：${item.requesterId || '--'}\n` +
        `目标用户ID：${item.targetUserId || '--'}\n` +
        `目标手机号：${item.targetPhone || '--'}\n` +
        `关系：${item.relationType || '--'}\n` +
        `状态：${item.status || '--'}\n` +
        `创建时间：${item.createdAt || '--'}\n` +
        `备注：${item.note || '--'}`,
    });
  },
  showTargetDetail(e) {
    const idx = Number(e.currentTarget.dataset.index || 0);
    const item = this.data.targetRequests[idx];
    if (!item) return;
    wx.showModal({
      title: '待确认详情',
      showCancel: false,
      content:
        `申请ID：${item.id || '--'}\n` +
        `申请人ID：${item.requesterId || '--'}\n` +
        `目标用户ID：${item.targetUserId || '--'}\n` +
        `申请手机号：${item.targetPhone || '--'}\n` +
        `关系：${item.relationType || '--'}\n` +
        `状态：${item.status || '--'}\n` +
        `创建时间：${item.createdAt || '--'}\n` +
        `备注：${item.note || '--'}`,
    });
  },
  copyRequestId(e) {
    const requestId = String(e.currentTarget.dataset.id || '');
    if (!requestId) return;
    const now = Date.now();
    if (this.data.lastCopiedRequestId === requestId && now - this.data.lastCopyAt < 1200) {
      wx.showToast({ title: '请勿重复点击', icon: 'none' });
      return;
    }
    wx.setClipboardData({
      data: requestId,
      success: () => {
        this.setData({ lastCopiedRequestId: requestId, lastCopyAt: now });
        wx.showToast({ title: 'ID已复制', icon: 'none' });
      }
    });
  },
  cancelRequest(e) {
    if (this.data.actionKey) return;
    const { mpApi } = require('../../api/mp');
    const requestId = e.currentTarget.dataset.id;
    wx.showModal({
      title: '确认取消',
      content: '确定取消这条家属申请吗？',
      success: async (res) => {
        if (!res.confirm) return;
        const key = `cancel-${requestId}`;
        this.setData({ actionKey: key });
        try {
          await mpApi.cancelFamilyRequest(requestId);
          wx.showToast({ title: '已取消', icon: 'none' });
          this.loadData();
        } catch (e) {
          wx.showToast({ title: this.mapErrorMessage(e), icon: 'none' });
        } finally {
          this.setData({ actionKey: '' });
        }
      }
    });
  },
  removeLink(e) {
    if (this.data.actionKey) return;
    const { mpApi } = require('../../api/mp');
    const linkId = e.currentTarget.dataset.id;
    wx.showModal({
      title: '确认解绑',
      content: '解绑后将无法继续查看对方报告，是否继续？',
      success: async (res) => {
        if (!res.confirm) return;
        const key = `unlink-${linkId}`;
        this.setData({ actionKey: key });
        try {
          await mpApi.removeFamilyLink(linkId);
          wx.showToast({ title: '已解绑', icon: 'none' });
          this.loadData();
        } catch (e) {
          wx.showToast({ title: this.mapErrorMessage(e), icon: 'none' });
        } finally {
          this.setData({ actionKey: '' });
        }
      }
    });
  },
  async loadMoreRequester() {
    if (this.data.requesterLoadingMore || !this.data.requesterHasMore) return;
    const { mpApi } = require('../../api/mp');
    const nextPage = this.data.requesterPage + 1;
    this.setData({ requesterLoadingMore: true });
    try {
      const res = await mpApi.familyRequests('requester', this.data.requesterStatus, nextPage, this.data.pageSize);
      const data = res.data || {};
      this.setData({
        requests: [...this.data.requests, ...(data.items || [])],
        requesterPage: nextPage,
        requesterHasMore: (data.page || nextPage) * (data.pageSize || this.data.pageSize) < (data.total || 0),
      });
    } catch (e) {
      wx.showToast({ title: this.mapErrorMessage(e), icon: 'none' });
    } finally {
      this.setData({ requesterLoadingMore: false });
    }
  },
  async loadMoreTarget() {
    if (this.data.targetLoadingMore || !this.data.targetHasMore) return;
    const { mpApi } = require('../../api/mp');
    const nextPage = this.data.targetPage + 1;
    this.setData({ targetLoadingMore: true });
    try {
      const res = await mpApi.familyRequests('target', this.data.targetStatus, nextPage, this.data.pageSize);
      const data = res.data || {};
      this.setData({
        targetRequests: [...this.data.targetRequests, ...(data.items || [])],
        targetPage: nextPage,
        targetHasMore: (data.page || nextPage) * (data.pageSize || this.data.pageSize) < (data.total || 0),
      });
    } catch (e) {
      wx.showToast({ title: this.mapErrorMessage(e), icon: 'none' });
    } finally {
      this.setData({ targetLoadingMore: false });
    }
  },
  async loadMoreLinks() {
    if (this.data.linkLoadingMore || !this.data.linkHasMore) return;
    const { mpApi } = require('../../api/mp');
    const nextPage = this.data.linkPage + 1;
    this.setData({ linkLoadingMore: true });
    try {
      const res = await mpApi.familyLinks(nextPage, this.data.pageSize);
      const data = res.data || {};
      this.setData({
        links: [...this.data.links, ...(data.items || [])],
        linkPage: nextPage,
        linkHasMore: (data.page || nextPage) * (data.pageSize || this.data.pageSize) < (data.total || 0),
      });
    } catch (e) {
      wx.showToast({ title: this.mapErrorMessage(e), icon: 'none' });
    } finally {
      this.setData({ linkLoadingMore: false });
    }
  },
  onReachBottom() {
    // 优先按列表顺序自动追加，直到无更多数据。
    if (this.data.requesterHasMore) {
      this.loadMoreRequester();
      return;
    }
    if (this.data.targetHasMore) {
      this.loadMoreTarget();
      return;
    }
    if (this.data.linkHasMore) {
      this.loadMoreLinks();
    }
  },
  backToTop() {
    wx.pageScrollTo({ scrollTop: 0, duration: 250 });
  },
});

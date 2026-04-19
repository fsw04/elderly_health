App<IAppOption>({
  globalData: {
    baseUrl: 'http://localhost:8000/api',
    token: wx.getStorageSync('eh_token') || '',
  },
  onLaunch() {
    const token = wx.getStorageSync('eh_token');
    if (token) {
      this.globalData.token = token;
    }
  }
})

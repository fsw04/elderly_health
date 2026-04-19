export function riskText(level: string) {
  if (level === 'high') return '高风险';
  if (level === 'medium') return '中风险';
  return '低风险';
}

export function safeText(val: any) {
  if (val === null || val === undefined || val === '') return '--';
  return String(val);
}

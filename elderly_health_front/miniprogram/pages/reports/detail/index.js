function withUnit(key, value) {
  const raw = String(value || '').trim();
  if (!raw) return '';
  const lowered = raw.toLowerCase();
  if (key === 'height' && !lowered.includes('cm') && /^\d+(\.\d+)?$/.test(raw)) return `${raw} cm`;
  if (key === 'weight' && !lowered.includes('kg') && /^\d+(\.\d+)?$/.test(raw)) return `${raw} kg`;
  if (key === 'bmi' && !lowered.includes('kg/m') && /^\d+(\.\d+)?$/.test(raw)) return `${raw} kg/m²`;
  if (key === 'bloodPressure' && !lowered.includes('mmhg') && /^\d+\s*\/\s*\d+$/.test(raw)) return `${raw} mmHg`;
  if (key === 'fastingBloodGlucose' && !lowered.includes('mmol/l') && /^\d+(\.\d+)?$/.test(raw)) return `${raw} mmol/L`;
  return raw;
}

Page({
  data: {
    report: null,
    doctorSummary: {
      height: '',
      weight: '',
      bmi: '',
      bloodPressure: '',
      fastingBloodGlucose: '',
      ecgFinding: '',
      bUltrasound: '',
      tcmConstitution: '',
    },
  },
  onLoad(query) { this.loadData(query.id); },
  async loadData(id) {
    const { mpApi } = require('../../../api/mp');
    const res = await mpApi.reportDetail(id);
    const report = res.data || {};
    const doctorSummary = (report.contentJson && report.contentJson.doctorSummary) || {};
    this.setData({
      report,
      doctorSummary: {
        height: withUnit('height', doctorSummary.height),
        weight: withUnit('weight', doctorSummary.weight),
        bmi: withUnit('bmi', doctorSummary.bmi),
        bloodPressure: withUnit('bloodPressure', doctorSummary.bloodPressure),
        fastingBloodGlucose: withUnit('fastingBloodGlucose', doctorSummary.fastingBloodGlucose),
        ecgFinding: doctorSummary.ecgFinding || '',
        bUltrasound: doctorSummary.bUltrasound || '',
        tcmConstitution: doctorSummary.tcmConstitution || '',
      },
    });
  }
});

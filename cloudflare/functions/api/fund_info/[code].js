import { json, fetchFundgz, fetchRiskLevel } from '../../_shared/helpers.js';

/**
 * GET /api/fund_info/:code
 * 添加基金时查询基金名称 + 自动识别风险评级
 */
export async function onRequestGet({ params }) {
  const { code } = params;

  const raw = await fetchFundgz(code);
  if (!raw) return json({ success: false, message: '无法获取基金信息' }, 404);

  // 尝试抓取风险评级（东方财富，可能失败，失败时返回空字符串）
  const riskLevel = await fetchRiskLevel(code);

  return json({
    success: true,
    fund_name: raw.name,
    risk_level: riskLevel || '',
    type: 'active', // 前端据名称自动判断类型
  });
}

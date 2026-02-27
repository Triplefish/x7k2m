import { json, getUser, loadFunds, saveFunds, fetchRiskLevel } from '../_shared/helpers.js';

/**
 * POST /api/update_risk_levels?user=X
 * 批量为缺少风险评级的基金抓取并回写 KV
 */
export async function onRequestPost({ request, env }) {
  const user = getUser(request);
  const funds = await loadFunds(env, user);

  let updated = 0;
  for (const fund of funds) {
    if (!fund.risk_level) {
      const level = await fetchRiskLevel(fund.code);
      if (level) {
        fund.risk_level = level;
        updated++;
      }
    }
  }

  await saveFunds(env, user, funds);
  return json({ success: true, updated });
}

import { json, resolveUser, unauthorized, loadFunds, fetchFundgz, formatEstimate } from '../_shared/helpers.js';

/**
 * GET /api/estimates?token=X
 * 并发拉取所有基金实时估值（含持仓份额）
 */
export async function onRequestGet({ request, env }) {
  const user = resolveUser(request, env);
  if (!user) return unauthorized();
  const funds = await loadFunds(env, user);

  const results = await Promise.all(
    funds.map(async (fund) => {
      const raw = await fetchFundgz(fund.code);
      if (!raw) {
        return {
          '基金名称': fund.name || fund.code,
          '基金代码': fund.code,
          '来源': fund.source || '其他',
          '类型': fund.type || '',
          '风险评级': fund.risk_level || '',
          '持仓份额': fund.shares || 0,
          '当前估值': '获取失败',
          '涨跌幅': '0',
          '涨跌额': '0',
          '昨日净值': '',
          '更新时间': '',
          error: true,
        };
      }
      return formatEstimate(fund, raw);
    })
  );

  return json(results);
}

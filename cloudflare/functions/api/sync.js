import { json, resolveUser, unauthorized, loadFunds, fetchFundgz, formatEstimate } from '../_shared/helpers.js';
import { updateVikaTable } from '../_shared/vika.js';

/**
 * POST /api/sync?token=X
 * 拉取所有基金估值 → 同步到维格表
 */
export async function onRequestPost({ request, env }) {
  const vikaToken = env.VIKA_API_TOKEN;
  const dsId = env.VIKA_DATASHEET_ID;

  if (!vikaToken || !dsId) {
    return json({ success: false, message: '未配置 VIKA_API_TOKEN / VIKA_DATASHEET_ID 环境变量' }, 400);
  }

  const user = resolveUser(request, env);
  if (!user) return unauthorized();
  const funds = await loadFunds(env, user);
  if (!funds.length) return json({ success: false, message: '基金列表为空' }, 400);

  const results = (
    await Promise.all(
      funds.map(async (fund) => {
        const raw = await fetchFundgz(fund.code);
        return raw ? formatEstimate(fund, raw) : null;
      })
    )
  ).filter(Boolean);

  if (!results.length) return json({ success: false, message: '所有基金估值获取失败' }, 500);

  try {
    const stat = await updateVikaTable(vikaToken, dsId, results);
    return json({ success: true, ...stat });
  } catch (e) {
    return json({ success: false, message: e.message }, 500);
  }
}

import { json, resolveUser, unauthorized, loadFunds, saveFunds } from '../../_shared/helpers.js';

/**
 * DELETE /api/funds/:code?token=X — 删除基金
 * PATCH  /api/funds/:code?token=X — 更新持仓份额 { shares: number }
 */

export async function onRequestDelete({ request, env, params }) {
  const user = resolveUser(request, env);
  if (!user) return unauthorized();
  const { code } = params;

  const funds = await loadFunds(env, user);
  const newFunds = funds.filter(f => f.code !== code);
  await saveFunds(env, user, newFunds);
  return json({ success: true });
}

export async function onRequestPatch({ request, env, params }) {
  const user = resolveUser(request, env);
  if (!user) return unauthorized();
  const { code } = params;
  const { shares } = await request.json();

  const funds = await loadFunds(env, user);
  const fund = funds.find(f => f.code === code);
  if (!fund) return json({ success: false, message: '基金不存在' }, 404);

  fund.shares = parseFloat(shares) || 0;
  await saveFunds(env, user, funds);
  return json({ success: true });
}

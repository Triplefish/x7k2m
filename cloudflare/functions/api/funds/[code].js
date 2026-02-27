import { json, getUser, loadFunds, saveFunds } from '../../_shared/helpers.js';

/**
 * DELETE /api/funds/:code?user=X — 删除基金
 */
export async function onRequestDelete({ request, env, params }) {
  const user = getUser(request);
  const { code } = params;

  const funds = await loadFunds(env, user);
  const newFunds = funds.filter(f => f.code !== code);
  await saveFunds(env, user, newFunds);
  return json({ success: true });
}

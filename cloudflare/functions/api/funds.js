import { json, getUser, loadFunds, saveFunds } from '../_shared/helpers.js';

/**
 * GET /api/funds?user=X  — 返回用户基金列表
 * POST /api/funds?user=X — 添加基金
 */

export async function onRequestGet({ request, env }) {
  const user = getUser(request);
  const funds = await loadFunds(env, user);
  return json(funds);
}

export async function onRequestPost({ request, env }) {
  const user = getUser(request);
  const data = await request.json();

  if (!data.code) return json({ success: false, message: '缺少基金代码' }, 400);

  const funds = await loadFunds(env, user);
  if (funds.find(f => f.code === data.code)) {
    return json({ success: false, message: '基金已存在' }, 400);
  }

  funds.push(data);
  await saveFunds(env, user, funds);
  return json({ success: true });
}

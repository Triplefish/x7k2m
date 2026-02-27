/**
 * 维格表 (Vika) 智能 Upsert 逻辑
 * 与 Python fund_tracker.py 中 update_vika_table() 完全对应
 */

const VIKA_API_BASE = 'https://vika.cn/fusion/v1';

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function vikaRequest(method, path, token, body = null) {
  const opts = {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`${VIKA_API_BASE}${path}`, opts);
  return res.json();
}

/**
 * 智能 Upsert：有则更新，无则新增，多余则删除
 * @param {string} token  - VIKA_API_TOKEN
 * @param {string} dsId   - VIKA_DATASHEET_ID
 * @param {object[]} records - 本次要同步的数据（每条需有 '基金代码' 字段）
 */
export async function updateVikaTable(token, dsId, records) {
  if (!token || !dsId) throw new Error('缺少维格表配置 VIKA_API_TOKEN / VIKA_DATASHEET_ID');

  // 1. 获取现有所有记录
  const listData = await vikaRequest('GET', `/datasheets/${dsId}/records?pageSize=1000`, token);
  await sleep(300);

  const existingMap = {}; // { fundCode: [recordId, ...] }
  if (listData?.data?.records) {
    for (const rec of listData.data.records) {
      const code = rec.fields['基金代码'];
      if (code) {
        if (!existingMap[code]) existingMap[code] = [];
        existingMap[code].push(rec.recordId);
      } else {
        if (!existingMap.__unknown__) existingMap.__unknown__ = [];
        existingMap.__unknown__.push(rec.recordId);
      }
    }
  }

  // 2. 分类
  const toCreate = [];
  const toUpdate = [];
  const toDelete = existingMap.__unknown__ ? [...existingMap.__unknown__] : [];
  const processedCodes = new Set();

  for (const record of records) {
    const code = record['基金代码'];
    processedCodes.add(code);
    if (existingMap[code]?.length) {
      toUpdate.push({ recordId: existingMap[code][0], fields: record });
      if (existingMap[code].length > 1) toDelete.push(...existingMap[code].slice(1));
    } else {
      toCreate.push({ fields: record });
    }
  }

  // 过时的基金记录也删除
  for (const [code, rids] of Object.entries(existingMap)) {
    if (code !== '__unknown__' && !processedCodes.has(code)) toDelete.push(...rids);
  }

  // 3. 执行删除
  for (let i = 0; i < toDelete.length; i += 10) {
    const batch = toDelete.slice(i, i + 10);
    await vikaRequest('DELETE', `/datasheets/${dsId}/records?recordIds=${batch.join(',')}`, token);
    await sleep(300);
  }

  // 4. 执行更新 (PATCH)
  for (let i = 0; i < toUpdate.length; i += 10) {
    await vikaRequest('PATCH', `/datasheets/${dsId}/records`, token, { records: toUpdate.slice(i, i + 10) });
    await sleep(300);
  }

  // 5. 执行新增 (POST)
  for (let i = 0; i < toCreate.length; i += 10) {
    await vikaRequest('POST', `/datasheets/${dsId}/records`, token, { records: toCreate.slice(i, i + 10) });
    await sleep(300);
  }

  return {
    updated: toUpdate.length,
    created: toCreate.length,
    deleted: toDelete.length,
  };
}

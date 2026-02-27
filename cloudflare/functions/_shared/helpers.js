/**
 * 共享工具函数
 * 供各 Pages Function 复用
 */

export const RISK_LEVEL_MAP = {
  low1: 'R1 低风险',
  low2: 'R2 中低风险',
  low3: 'R3 中等风险',
  low4: 'R4 中高风险',
  low5: 'R5 高风险',
};

/**
 * 从天天基金网 JSONP 接口获取基金估值
 * 返回解析后的 JSON 对象，失败返回 null
 */
export async function fetchFundgz(code) {
  try {
    const res = await fetch(
      `http://fundgz.1234567.com.cn/js/${code}.js?v=${Date.now()}`,
      { cf: { cacheTtl: 60 } }
    );
    const text = await res.text();
    // 格式: jsonpgz({...});
    const match = text.match(/\((\{.+\})\)/s);
    if (!match) return null;
    return JSON.parse(match[1]);
  } catch {
    return null;
  }
}

/**
 * 将基金 JSON 数据格式化为 API 返回格式
 */
export function formatEstimate(fund, raw) {
  const latestNav = parseFloat(raw.dwjz);
  const estimateNav = raw.gsz ? parseFloat(raw.gsz) : latestNav;
  const changePct = (estimateNav - latestNav) / latestNav;

  const typeLabel =
    fund.type === 'etf_linked' ? `ETF联接-${fund.etf_name || ''}`
    : fund.type === 'bond' ? '债券型'
    : '主动型';

  return {
    '基金名称': raw.name,
    '基金代码': fund.code,
    '来源': fund.source || '其他',
    '类型': typeLabel,
    '风险评级': fund.risk_level || '',
    '昨日净值': latestNav.toFixed(4),
    '当前估值': estimateNav.toFixed(4),
    '涨跌幅': changePct.toFixed(6),
    '涨跌额': (estimateNav - latestNav).toFixed(4),
    '更新时间': raw.gztime || raw.jzrq || '',
  };
}

/**
 * 从东方财富抓取基金风险评级 (R1-R5)
 * 匹配 class='lowX chooseLow' 样式类
 */
export async function fetchRiskLevel(code) {
  try {
    const res = await fetch(`https://fund.eastmoney.com/f10/tsdata_${code}.html`, {
      headers: {
        'Referer': 'https://fund.eastmoney.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      },
      cf: { cacheTtl: 3600 },
    });
    const html = await res.text();
    const match = html.match(/class=["']?(low[1-5])\s+chooseLow["']?/);
    if (match) return RISK_LEVEL_MAP[match[1]] || null;
  } catch {
    // ignore
  }
  return null;
}

/**
 * 标准 JSON 响应
 */
export function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

/**
 * 解析 URL 中的 user 参数，默认 user1
 */
export function getUser(request) {
  return new URL(request.url).searchParams.get('user') || 'user1';
}

/**
 * 从 KV 读取用户基金列表
 */
export async function loadFunds(env, user) {
  const raw = await env.FUND_KV.get(`funds:${user}`);
  return raw ? JSON.parse(raw) : [];
}

/**
 * 写入用户基金列表到 KV
 */
export async function saveFunds(env, user, funds) {
  await env.FUND_KV.put(`funds:${user}`, JSON.stringify(funds));
}

"""
基金实时估值追踪工具
优先使用天天基金网实时估值，备用 AkShare 数据
"""

import os
import requests
import json
import pandas as pd
from datetime import datetime
import urllib3
from dotenv import load_dotenv

# 加载 .env 文件（本地开发使用，GitHub Actions 不需要）
load_dotenv(verbose=False)

# 禁用 SSL 警告（仅用于解决某些网络环境的证书问题）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置信息（优先从环境变量读取，其次从 .env 文件读取）
VIKA_API_TOKEN = os.environ.get("VIKA_API_TOKEN", "").strip()
VIKA_DATASHEET_ID = os.environ.get("VIKA_DATASHEET_ID", "").strip()
VIKA_API_BASE = "https://vika.cn/fusion/v1"

# 基金数据文件路径
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'funds.json')

def load_funds():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load funds: {e}")
            return []
    return []

def save_funds(funds):
    try:
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(funds, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Failed to save funds: {e}")
        return False

# 初始化配置
FUNDS = load_funds()
if not FUNDS:
    # Fallback default if file doesn't exist or is empty
    FUNDS = [
        # 理财通基金
        {
            "name": "易方达黄金ETF联接C",
            "code": "002963",
            "type": "etf_linked",
            "etf_code": "159934",
            "etf_name": "黄金ETF",
            "source": "理财通"
        },
        {
            "name": "汇添富有色金属ETF",
            "code": "019165",
            "type": "etf_linked",
            "etf_code": "512400",
            "etf_name": "有色金属ETF",
            "source": "理财通"
        },
        {
            "name": "南方信息创新混合A",
            "code": "007490",
            "type": "active",
            "index_code": "399006",
            "index_name": "创业板指",
            "source": "理财通"
        },
        {
            "name": "国联安半导体ETF联接A",
            "code": "007300",
            "type": "etf_linked",
            "etf_code": "512480",
            "etf_name": "半导体ETF",
            "source": "理财通"
        },
        {
            "name": "博时转债增强债券A",
            "code": "050019",
            "type": "bond",
            "index_code": "000832",
            "index_name": "中证转债",
            "source": "理财通"
        },
        {
            "name": "易方达科创50ETF联接C",
            "code": "013305",
            "type": "etf_linked",
            "etf_code": "588000",
            "etf_name": "科创50ETF",
            "source": "理财通"
        },
        # 支付宝基金
        {
            "name": "国寿安保尊享债券A",
            "code": "000668",
            "type": "bond",
            "source": "支付宝"
        },
        {
            "name": "富国稳健添息债券C",
            "code": "019584",
            "type": "bond",
            "source": "支付宝"
        },
        {
            "name": "汇添富鑫享添利六个月持有期混合A",
            "code": "012951",
            "type": "bond",
            "source": "支付宝"
        },
        {
            "name": "上银慧享利30天滚动持有中短债债券A",
            "code": "015942",
            "type": "bond",
            "source": "支付宝"
        },
    ]
    # save_funds(FUNDS) # Optional: create file if missing


def get_fund_realtime_data(fund_code):
    """
    从天天基金网获取基金数据
    注意：此API可能随时失效（监管要求）
    返回: dict with fund data
    """
    try:
        url = f"http://fundgz.1234567.com.cn/js/{fund_code}.js"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200 and response.text:
            # 检查返回内容是否有效
            if 'jsonpgz(' not in response.text and '(' not in response.text:
                print(f"⚠️  基金 {fund_code} 返回内容异常，可能是无效代码")
                return {'success': False, 'error': '基金代码可能无效'}
            
            # 解析返回的 JavaScript 数据
            try:
                json_str = response.text.split('(')[1].split(')')[0]
                data = json.loads(json_str)
            except (IndexError, json.JSONDecodeError) as e:
                print(f"⚠️  基金 {fund_code} 数据解析失败: {response.text[:100]}")
                return {'success': False, 'error': '数据格式错误'}
            
            fund_name = data['name']              # 基金名称
            latest_nav = float(data['dwjz'])      # 昨日净值
            estimate_nav = data.get('gsz', None)  # 实时估值（可能为空）
            estimate_time = data.get('gztime', '') # 估值时间
            
            if estimate_nav and estimate_nav != '':
                estimate_nav = float(estimate_nav)
                change_pct = (estimate_nav - latest_nav) / latest_nav * 100
                change_amount = estimate_nav - latest_nav
                
                return {
                    'fund_name': fund_name,
                    'latest_nav': latest_nav,
                    'estimate_nav': estimate_nav,
                    'change_pct': change_pct,
                    'change_amount': change_amount,
                    'estimate_time': estimate_time,
                    'success': True,
                    'data_source': '天天基金网'
                }
            else:
                # 没有实时估值，返回昨日净值
                return {
                    'fund_name': fund_name,
                    'latest_nav': latest_nav,
                    'estimate_nav': latest_nav,
                    'change_pct': 0.0,
                    'change_amount': 0.0,
                    'estimate_time': data.get('jzrq', ''),
                    'success': True,
                    'note': '暂无实时估值',
                    'data_source': '天天基金网'
                }
        else:
            return {'success': False}
            
    except Exception as e:
        print(f"⚠️  天天基金网获取失败: {e}")
        return {'success': False}


def calculate_by_etf_price(fund, latest_nav):
    """
    备用方案：根据ETF价格自己计算估值
    适用于ETF联接基金
    """
    if fund['type'] != 'etf_linked':
        return None
    
    etf_code = fund.get('etf_code')
    if not etf_code:
        return None
    
    try:
        # 尝试多个数据源
        # 1. 东方财富
        url = f"http://push2.eastmoney.com/api/qt/stock/get?secid=1.{etf_code}&fields=f43,f44,f45,f46,f60,f170"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('data'):
                current_price = data['data'].get('f43')  # 当前价
                yesterday_close = data['data'].get('f60')  # 昨收
                
                if current_price and yesterday_close:
                    current_price = float(current_price) / 1000
                    yesterday_close = float(yesterday_close) / 1000
                    change_pct = (current_price - yesterday_close) / yesterday_close * 100
                    
                    estimated_nav = latest_nav * (1 + change_pct / 100)
                    
                    return {
                        'estimate_nav': estimated_nav,
                        'change_pct': change_pct,
                        'change_amount': estimated_nav - latest_nav,
                        'data_source': 'ETF价格计算',
                        'note': f'基于{fund["etf_name"]}估算'
                    }
    except Exception as e:
        pass
    
    return None


def get_fund_basic_info(fund_code):
    """
    获取基金基础信息（昨日净值）
    用于完全的备用方案
    """
    try:
        url = f"http://fundgz.1234567.com.cn/js/{fund_code}.js"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200 and response.text:
            try:
                json_str = response.text.split('(')[1].split(')')[0]
                data = json.loads(json_str)
                
                return {
                    'fund_name': data['name'],
                    'latest_nav': float(data['dwjz']),
                    'nav_date': data.get('jzrq', ''),
                    'success': True
                }
            except (IndexError, json.JSONDecodeError, KeyError):
                pass
    except Exception:
        pass
    
    return {'success': False}


def calculate_fund_estimate(fund):
    """
    获取单个基金的估值信息
    策略：
    1. 优先尝试天天基金网（如果还能用）
    2. 如果失败，ETF联接基金用ETF价格计算
    3. 最终兜底：只显示昨日净值
    """
    fund_code = fund['code']
    fund_name = fund['name']
    fund_type = fund['type']
    fund_source = fund.get('source', '未知')  # 获取来源
    
    print(f"\n📊 处理基金: {fund_name} ({fund_code}) - 来源: {fund_source}")
    
    # 方案1：天天基金网（可能随时失效）
    data = get_fund_realtime_data(fund_code)
    
    if data['success']:
        # 成功获取数据
        result = {
            "基金名称": data['fund_name'],
            "基金代码": fund_code,
            "来源": fund_source,
            "昨日净值": f"{data['latest_nav']:.4f}",
            "当前估值": f"{data['estimate_nav']:.4f}",
            "涨跌幅": f"{data['change_pct']/100:.4f}",
            "涨跌额": f"{data['change_amount']:+.4f}",
            "更新时间": data['estimate_time'],
            "数据来源": data.get('data_source', '天天基金网')
        }
        
        # 添加类型信息
        if fund_type == "etf_linked":
            result["类型"] = f"ETF联接-{fund.get('etf_name', '')}"
        elif fund_type == "active":
            result["类型"] = "主动型"
        elif fund_type == "bond":
            result["类型"] = "债券型"
        
        if 'note' in data:
            result["备注"] = data['note']
        
        print(f"   ✅ 昨日净值: {data['latest_nav']:.4f}")
        print(f"   ✅ 当前估值: {data['estimate_nav']:.4f}")
        print(f"   ✅ 涨跌: {data['change_pct']:+.2f}%")
        
        return result
    
    # 方案2：备用计算（仅ETF联接基金）
    print(f"   ⚠️  天天基金网失效，尝试备用方案...")
    
    basic_info = get_fund_basic_info(fund_code)
    if not basic_info['success']:
        print(f"   ❌ 无法获取基金信息")
        return None
    
    latest_nav = basic_info['latest_nav']
    
    # 如果是ETF联接基金，尝试用ETF价格计算
    if fund_type == "etf_linked":
        backup_data = calculate_by_etf_price(fund, latest_nav)
        if backup_data:
            print(f"   ✅ 使用备用方案计算成功")
            return {
                "基金名称": basic_info['fund_name'],
                "基金代码": fund_code,
                "来源": fund_source,
                "类型": f"ETF联接-{fund.get('etf_name', '')}",
                "昨日净值": f"{latest_nav:.4f}",
                "当前估值": f"{backup_data['estimate_nav']:.4f}",
                "涨跌幅": f"{backup_data['change_pct']/100:.4f}",
                "涨跌额": f"{backup_data['change_amount']:+.4f}",
                "更新时间": datetime.now().strftime("%H:%M"),
                "数据来源": backup_data['data_source'],
                "备注": backup_data['note']
            }
    
    # 方案3：最终兜底 - 只显示昨日净值
    print(f"   ℹ️  仅显示昨日净值")
    return {
        "基金名称": basic_info['fund_name'],
        "基金代码": fund_code,
        "来源": fund_source,
        "类型": fund_type,
        "昨日净值": f"{latest_nav:.4f}",
        "当前估值": f"{latest_nav:.4f}",
        "涨跌幅": "0.0000",
        "涨跌额": "0.0000",
        "更新时间": basic_info['nav_date'],
        "数据来源": "昨日净值",
        "备注": "暂无实时数据"
    }


def update_vika_table(records):
    """使用 REST API 智能更新维格表 (Upsert: 有则更新，无则新增，多则删除)"""
    if not VIKA_API_TOKEN or not VIKA_DATASHEET_ID:
        print("❌ 缺少维格表配置信息")
        return False
    
    try:
        headers = {
            "Authorization": f"Bearer {VIKA_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # 1. 获取现有所有数据（建立索引）
        print("\n🔍 检查现有记录...")
        list_url = f"{VIKA_API_BASE}/datasheets/{VIKA_DATASHEET_ID}/records"
        params = {"pageSize": 1000} 
        response = requests.get(list_url, headers=headers, params=params, timeout=10, verify=False)
        
        # 避免QPS限制
        import time
        time.sleep(0.5)

        existing_map = {} # 格式: { "002963": ["rec1", "rec2"], ... }
        
        if response.status_code == 200:
            data = response.json()
            if data.get('data') and data['data'].get('records'):
                for rec in data['data']['records']:
                    rid = rec['recordId']
                    # 获取基金代码，注意这里如果列名没对上，code会是None
                    f_code = rec['fields'].get('基金代码')
                    
                    if f_code:
                        if f_code not in existing_map:
                            existing_map[f_code] = []
                        existing_map[f_code].append(rid)
                    else:
                        # 可能是脏数据（比如之前没填进去的空行）
                        if "unknown" not in existing_map:
                            existing_map["unknown"] = []
                        existing_map["unknown"].append(rid)

        # 2. 分类操作：需要更新的、需要新增的、需要删除的
        to_create = []
        to_update = []
        to_delete = []
        
        # 记录本次涉及到的 有效 recordIds
        processed_fund_codes = set()
        
        # 先把所有未知的（脏数据）加入删除列表
        if "unknown" in existing_map:
            to_delete.extend(existing_map["unknown"])

        for record in records:
            code = record['基金代码']
            processed_fund_codes.add(code)
            
            if code in existing_map and existing_map[code]:
                # 存在：更新第一条
                target_id = existing_map[code][0]
                to_update.append({
                    "recordId": target_id,
                    "fields": record
                })
                # 如果有重复的（同一个代码多条记录），把剩下的加入删除列表
                if len(existing_map[code]) > 1:
                    to_delete.extend(existing_map[code][1:])
            else:
                # 不存在：新增
                to_create.append({
                    "fields": record
                })

        # 3. 删除不在本次列表里的其他过时数据
        for code, rids in existing_map.items():
            if code != "unknown" and code not in processed_fund_codes:
                to_delete.extend(rids)
        
        # 4. 执行操作
        # 4.1 批量删除
        if to_delete:
            print(f"🗑️  清理 {len(to_delete)} 条重复或脏数据...")
            for i in range(0, len(to_delete), 10):
                batch = to_delete[i:i+10]
                ids_str = ",".join(batch)
                del_url = f"{VIKA_API_BASE}/datasheets/{VIKA_DATASHEET_ID}/records?recordIds={ids_str}"
                requests.delete(del_url, headers=headers, verify=False)
                time.sleep(0.5)

        # 4.2 批量更新
        if to_update:
            print(f"🔄 更新 {len(to_update)} 条现有数据...")
            patch_url = f"{VIKA_API_BASE}/datasheets/{VIKA_DATASHEET_ID}/records"
            for i in range(0, len(to_update), 10):
                batch = to_update[i:i+10]
                payload = {"records": batch}
                requests.patch(patch_url, json=payload, headers=headers, verify=False)
                time.sleep(0.5)

        # 4.3 批量新增
        if to_create:
            print(f"📝 新增 {len(to_create)} 条新数据...")
            create_url = f"{VIKA_API_BASE}/datasheets/{VIKA_DATASHEET_ID}/records"
            for i in range(0, len(to_create), 10):
                batch = to_create[i:i+10]
                payload = {"records": batch}
                requests.post(create_url, json=payload, headers=headers, verify=False)
                time.sleep(0.5)

        print(f"✅ 同步完成：更新{len(to_update)} / 新增{len(to_create)} / 清理{len(to_delete)}")
        return True
        
    except Exception as e:
        print(f"❌ 更新维格表失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 基金实时估值追踪工具")
    print("=" * 60)
    print(f"⏰ 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # 遍历所有基金
    for fund in FUNDS:
        result = calculate_fund_estimate(fund)
        if result:
            results.append(result)
    
    # 输出汇总
    print("\n" + "=" * 60)
    print(f"📈 估值汇总 (共 {len(results)} 个基金)")
    print("=" * 60)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['基金名称']}")
        print(f"   昨日净值: {result['昨日净值']}")
        print(f"   涨跌幅: {result['涨跌幅']}")
        print(f"   当前估值: {result['当前估值']}")
    
    # 更新到维格表
    if results:
        print("\n" + "=" * 60)
        print("📤 更新数据到维格表...")
        print("=" * 60)
        update_vika_table(results)
    
    print("\n✅ 任务完成！")


if __name__ == "__main__":
    main()

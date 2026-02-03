"""
基金实时估值追踪工具
优先使用天天基金网实时估值，备用 AkShare 数据
"""

import os
import requests
import json
import pandas as pd
from datetime import datetime
from vika import Vika
import urllib3

# 禁用 SSL 警告（仅用于解决某些网络环境的证书问题）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置信息
VIKA_API_TOKEN = os.environ.get("VIKA_API_TOKEN")
VIKA_DATASHEET_ID = os.environ.get("VIKA_DATASHEET_ID")

# 基金配置
FUNDS = [
    {
        "name": "易方达黄金ETF联接C",
        "code": "002963",
        "type": "etf_linked",
        "etf_code": "159934",
        "etf_name": "黄金ETF"
    },
    {
        "name": "汇添富有色金属ETF",
        "code": "019165",
        "type": "etf_linked",
        "etf_code": "512400",
        "etf_name": "有色金属ETF"
    },
    {
        "name": "南方信息创新混合A",
        "code": "007490",
        "type": "active",
        "index_code": "399006",  # 创业板指
        "index_name": "创业板指"
    },
    {
        "name": "国联安半导体ETF联接A",
        "code": "007300",
        "type": "etf_linked",
        "etf_code": "512480",
        "etf_name": "半导体ETF"
    },
    {
        "name": "博时转债增强债券A",
        "code": "050019",
        "type": "bond",
        "index_code": "000832",  # 中证转债
        "index_name": "中证转债"
    },
    {
        "name": "易方达科创50ETF联接C",
        "code": "013305",
        "type": "etf_linked",
        "etf_code": "588000",
        "etf_name": "科创50ETF"
    },
    {
        "name": "汇添富科技领先混合C",
        "code": "025881",
        "type": "active",
        "index_code": "000688",  # 科创50指数
        "index_name": "科创50"
    }
]


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
            # 解析返回的 JavaScript 数据
            json_str = response.text.split('(')[1].split(')')[0]
            data = json.loads(json_str)
            
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
        url = f"http://push2.eastmoney.com/api/qt/stock/get?secid=1.{etf_code}&fields=f43,f44,f45,f46,f170"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('data'):
                current_price = data['data'].get('f43')  # 当前价
                yesterday_close = data['data'].get('f60')  # 昨收
                
           估值信息
    策略：
    1. 优先尝试天天基金网（如果还能用）
    2. 如果失败，ETF联接基金用ETF价格计算
    3. 最终兜底：只显示昨日净值
    """
    fund_code = fund['code']
    fund_name = fund['name']
    fund_type = fund['type']
    
    print(f"\n📊 处理基金: {fund_name} ({fund_code})")
    
    # 方案1：天天基金网（可能随时失效）
    data = get_fund_realtime_data(fund_code)
    
    if data['success']:
        # 成功获取数据
        result = {
            "基金名称": data['fund_name'],
            "基金代码": fund_code,
            "昨日净值": f"{data['latest_nav']:.4f}",
            "当前估值": f"{data['estimate_nav']:.4f}",
            "涨跌幅": f"{data['change_pct']:+.2f}%",
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
                "类型": f"ETF联接-{fund.get('etf_name', '')}",
                "昨日净值": f"{latest_nav:.4f}",
                "当前估值": f"{backup_data['estimate_nav']:.4f}",
                "涨跌幅": f"{backup_data['change_pct']:+.2f}%",
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
        "类型": fund_type,
        "昨日净值": f"{latest_nav:.4f}",
        "当前估值": f"{latest_nav:.4f}",
        "涨跌幅": "0.00%",
        "涨跌额": "0.0000",
        "更新时间": basic_info['nav_date'],
        "数据来源": "昨日净值",
        "备注": "暂无实时数据"
    }
    print(f"\n📊 处理基金: {fund_name} ({fund_code})")
    
    # 获取天天基金网的实时数据
    data = get_fund_realtime_data(fund_code)
    
    if not data['success']:
        print(f"❌ 无法获取基金数据，跳过")
        return None
    
    # 准备返回的数据
    result = {
        "基金名称": data['fund_name'],
        "基金代码": fund_code,
        "昨日净值": f"{data['latest_nav']:.4f}",
        "估算净值": f"{data['estimate_nav']:.4f}",
        "估算涨跌": f"{data['change_pct']:+.2f}%",
        "估算增长": f"{data['change_amount']:+.4f}",
        "更新时间": data['estimate_time'],
        "数据来源": "天天基金网"
    }
    
    # 根据基金类型添加额外信息
    if fund_type == "etf_linked":
        etf_name = fund.get('etf_name', '')
        etf_code = fund.get('etf_code', '')
        result["基金类型"] = "ETF联接"
        result["追踪标的"] = f"{etf_name}({etf_code})" if etf_name else "ETF"
        result["准确度"] = "高"
    elif fund_type == "active":
        index_name = fund.get('index_name', '')
        result["基金类型"] = "主动型"
        result["参考指数"] = index_name
        result["准确度"] = "官方估值"
    elif fund_type == "bond":
        result["基金类型"] = "债券型"
        result["准确度"] = "官方估值"
    
    # 添加备注
    if 'note' in data:
        result["备注"] = data['note']
    
    print(f"   昨日净值: {data['latest_nav']:.4f}")
    print(f"   估算净值: {data['estimate_nav']:.4f}")
    print(f"   估算涨跌: {data['change_pct']:+.2f}%")
    print(f"   更新时间: {data['estimate_time']}")
    
    return result


def update_vika_table(records):
    """更新维格表数据"""
    if not VIKA_API_TOKEN or not VIKA_DATASHEET_ID:
        print("❌ 缺少维格表配置信息")
        return False
    
    try:
        vika = Vika(VIKA_API_TOKEN)
        datasheet = vika.datasheet(VIKA_DATASHEET_ID)
        
        # 清空现有数据
        print("\n🗑️  清空旧数据...")
        all_records = datasheet.records.all()
        if all_records:
            for record in all_records:
                datasheet.records.delete(record.record_id)
        
        # 批量插入新数据
        print("📝 插入新数据...")
        for record in records:
            datasheet.records.create(record)
        
        print(f"✅ 成功更新 {len(records)} 条记录到维格表")
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
        print(f"   估算涨跌: {result['估算涨跌']}")
        print(f"   估算净值: {result['估算净值']}")
    
    # 更新到维格表
    if results:
        print("\n" + "=" * 60)
        print("📤 更新数据到维格表...")
        print("=" * 60)
        update_vika_table(results)
    
    print("\n✅ 任务完成！")


if __name__ == "__main__":
    main()

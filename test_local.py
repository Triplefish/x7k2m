"""
本地测试脚本 - 不连接维格表，仅测试数据获取
使用天天基金网官方 API，无需 AkShare
"""

import requests
import json
from datetime import datetime

# 测试基金列表（您的7个基金）
TEST_FUNDS = [
    {"name": "易方达黄金ETF联接C", "code": "002963"},
    {"name": "汇添富有色金属ETF", "code": "019165"},
    {"name": "南方信息创新混合A", "code": "007490"},
    {"name": "国联安半导体ETF联接A", "code": "007300"},
    {"name": "博时转债增强债券A", "code": "050019"},
    {"name": "易方达科创50ETF联接C", "code": "013305"},
    {"name": "汇添富科技领先混合C", "code": "025881"},
]


def test_fund_realtime_estimate():
    """测试基金实时估值获取（天天基金网官方数据）"""
    print("=" * 70)
    print("💰 测试基金实时估值获取（天天基金网）")
    print("=" * 70)
    print("\n这是最准确的数据源！天天基金网会实时计算基金估值。\n")
    
    success_count = 0
    
    for fund in TEST_FUNDS:
        fund_code = fund['code']
        try:
            url = f"http://fundgz.1234567.com.cn/js/{fund_code}.js"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                json_str = response.text.split('(')[1].split(')')[0]
                data = json.loads(json_str)
                
                fund_name = data['name']
                latest_nav = float(data['dwjz'])  # 昨日净值
                estimate_nav = data.get('gsz', None)  # 实时估值
                estimate_time = data.get('gztime', '')  # 估值时间
                
                print(f"✅ {fund_name}")
                print(f"   基金代码: {fund_code}")
                print(f"   昨日净值: {latest_nav:.4f}")
                
                if estimate_nav and estimate_nav != '':
                    estimate_nav = float(estimate_nav)
                    change_pct = (estimate_nav - latest_nav) / latest_nav * 100
                    change_amount = estimate_nav - latest_nav
                    
                    print(f"   实时估值: {estimate_nav:.4f}")
                    print(f"   估算涨跌: {change_pct:+.2f}%")
                    print(f"   涨跌金额: {change_amount:+.4f}")
                    print(f"   估值时间: {estimate_time}")
                    success_count += 1
                else:
                    print(f"   实时估值: 暂无（可能是非交易时间）")
                    print(f"   净值日期: {data.get('jzrq', '')}")
                    success_count += 1
                
                print()
            else:
                print(f"❌ {fund['name']} - HTTP {response.status_code}")
                print()
        
        except Exception as e:
            print(f"❌ {fund['name']} - 获取失败: {e}")
            print()
    
    return success_count


def test_sina_backup():
    """测试新浪财经备用数据源（用于获取ETF价格）"""
    print("=" * 70)
    print("📊 测试备用数据源 - 新浪财经（ETF实时价格）")
    print("=" * 70)
    print("\n备用方案：如果需要单独查看ETF价格\n")
    
    test_etfs = [
        {"name": "黄金ETF", "code": "sh159934"},
        {"name": "有色金属ETF", "code": "sh512400"},
        {"name": "半导体ETF", "code": "sh512480"},
    ]
    
    for etf in test_etfs:
        try:
            url = f"https://hq.sinajs.cn/list={etf['code']}"
            response = requests.get(url, timeout=5, verify=False)
            
            if response.status_code == 200 and response.text:
                data = response.text.split('"')[1].split(',')
                if len(data) > 3:
                    current_price = float(data[3])
                    yesterday_close = float(data[2])
                    change_pct = (current_price - yesterday_close) / yesterday_close * 100
                    
                    print(f"✅ {etf['name']} ({etf['code']})")
                    print(f"   当前价格: {current_price:.3f}")
                    print(f"   昨日收盘: {yesterday_close:.3f}")
                    print(f"   涨跌幅: {change_pct/100:.4f}")
                    print()
                else:
                    print(f"⚠️  {etf['name']} - 数据格式异常")
                    print()
            else:
                print(f"❌ {etf['name']} - 连接失败")
                print()
        except Exception as e:
            print(f"❌ {etf['name']} - {e}")
            print()


def main():
    print("\n")
    print("🧪 基金估值工具 - 本地测试（优化版）")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n")
    print("📌 说明：现在使用天天基金网官方实时估值，比自己计算更准确！")
    print("📌 不再依赖 AkShare，避免 SSL 证书问题。")
    print("\n")
    
    # 测试主要数据源
    success_count = test_fund_realtime_estimate()
    
    print("=" * 70)
    
    # 测试备用数据源（可选）
    try:
        test_sina_backup()
    except Exception as e:
        print(f"⚠️  备用数据源测试失败（不影响主功能）: {e}\n")
    
    # 总结
    print("=" * 70)
    print("✅ 测试完成！")
    print("=" * 70)
    
    if success_count >= 5:
        print(f"\n🎉 太好了！成功获取了 {success_count}/7 个基金的数据！")
        print("✅ 数据源可用，可以继续部署到 GitHub Actions")
        print("\n💡 下一步：")
        print("   1. 注册维格表账号（vika.cn）")
        print("   2. 获取 API Token 和数据表 ID")
        print("   3. 配置到 GitHub Secrets")
        print("   4. 运行 GitHub Actions")
    else:
        print(f"\n⚠️  只有 {success_count}/7 个基金成功")
        print("   请检查网络连接或稍后重试")


if __name__ == "__main__":
    main()

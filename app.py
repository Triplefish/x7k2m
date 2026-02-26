from flask import Flask, render_template, request, jsonify
import sys
import os
import threading
import fund_tracker
import json

app = Flask(__name__)

# 用户数据文件映射
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
USER_DATA_FILES = {
    'user1': os.path.join(DATA_DIR, 'funds.json'),
    'user2': os.path.join(DATA_DIR, 'funds_user2.json'),
}
DEFAULT_USER = 'user1'

def get_user(req=None):
    """从请求参数中获取用户标识，默认为 user1"""
    if req is None:
        req = request
    return req.args.get('user', DEFAULT_USER)

def load_funds_for_user(user):
    """加载指定用户的基金列表"""
    data_file = USER_DATA_FILES.get(user, USER_DATA_FILES[DEFAULT_USER])
    return fund_tracker.load_funds(data_file)

def save_funds_for_user(user, funds):
    """保存指定用户的基金列表"""
    data_file = USER_DATA_FILES.get(user, USER_DATA_FILES[DEFAULT_USER])
    return fund_tracker.save_funds(funds, data_file)

def _sync_vika_background(results):
    """后台线程：同步数据到维格表"""
    try:
        print("🔄 [后台] 正在自动同步 user1 数据到维格表...")
        fund_tracker.update_vika_table(results)
    except Exception as e:
        print(f"⚠️  [后台] 维格表同步失败: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/funds', methods=['GET'])
def get_funds():
    user = get_user()
    funds = load_funds_for_user(user)
    return jsonify(funds)

@app.route('/api/funds', methods=['POST'])
def add_fund():
    user = get_user()
    data = request.json
    funds = load_funds_for_user(user)
    
    # Check if duplicate
    for f in funds:
        if f['code'] == data['code']:
            return jsonify({'success': False, 'message': '基金已存在'}), 400
            
    funds.append(data)
    save_funds_for_user(user, funds)
    if user == DEFAULT_USER:
        fund_tracker.FUNDS = funds
    return jsonify({'success': True})

@app.route('/api/funds/<string:code>', methods=['DELETE'])
def delete_fund(code):
    user = get_user()
    funds = load_funds_for_user(user)
    new_funds = [f for f in funds if f['code'] != code]
    save_funds_for_user(user, new_funds)
    if user == DEFAULT_USER:
        fund_tracker.FUNDS = new_funds
    return jsonify({'success': True})

@app.route('/api/estimates', methods=['GET'])
def get_estimates():
    user = get_user()
    funds = load_funds_for_user(user)
    results = []
    
    for fund in funds:
        try:
            res = fund_tracker.calculate_fund_estimate(fund)
            if res:
                results.append(res)
            else:
                results.append({
                    "基金名称": fund.get('name', fund['code']),
                    "基金代码": fund['code'],
                    "当前估值": "获取失败",
                    "涨跌幅": "0",
                    "风险评级": fund.get('risk_level', ''),
                    "error": True
                })
        except Exception as e:
            results.append({
                "基金名称": fund.get('name', fund['code']),
                "基金代码": fund['code'],
                "当前估值": "出错",
                "涨跌幅": "0",
                "风险评级": fund.get('risk_level', ''),
                "error": str(e)
            })

    # user1 每次刷新自动同步到维格表（后台线程，不阻塞响应）
    if user == 'user1' and results:
        t = threading.Thread(target=_sync_vika_background, args=(results,), daemon=True)
        t.start()

    return jsonify(results)

@app.route('/api/fund_info/<string:code>', methods=['GET'])
def get_fund_info(code):
    info = fund_tracker.get_fund_realtime_data(code)
    if info['success']:
        # 尝试获取风险评级
        risk_level = fund_tracker.get_fund_risk_level(code)
        return jsonify({
            'fund_name': info['fund_name'],
            'type': 'active',
            'risk_level': risk_level or '',
            'success': True
        })
        
    return jsonify({'success': False, 'message': '无法获取基金信息'}), 404

@app.route('/api/sync', methods=['POST'])
def sync_vika():
    user = get_user()
    funds = load_funds_for_user(user)
    results = []
    for fund in funds:
        res = fund_tracker.calculate_fund_estimate(fund)
        if res:
            results.append(res)
            
    if not results:
        return jsonify({'success': False, 'message': '无数据可同步'})
        
    success = fund_tracker.update_vika_table(results)
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': '同步失败，请检查日志'})

if __name__ == '__main__':
    app.run(debug=True, port=8888)

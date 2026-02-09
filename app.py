from flask import Flask, render_template, request, jsonify
import sys
import os
import fund_tracker
import json

app = Flask(__name__)

# Ensure we can load funds
DATA_FILE = fund_tracker.DATA_FILE

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/funds', methods=['GET'])
def get_funds():
    funds = fund_tracker.load_funds()
    return jsonify(funds)

@app.route('/api/funds', methods=['POST'])
def add_fund():
    data = request.json
    funds = fund_tracker.load_funds()
    
    # Check if duplicate
    for f in funds:
        if f['code'] == data['code']:
            return jsonify({'success': False, 'message': '基金已存在'}), 400
            
    funds.append(data)
    fund_tracker.save_funds(funds)
    fund_tracker.FUNDS = funds # Update global var in module
    return jsonify({'success': True})

@app.route('/api/funds/<string:code>', methods=['DELETE'])
def delete_fund(code):
    funds = fund_tracker.load_funds()
    new_funds = [f for f in funds if f['code'] != code]
    fund_tracker.save_funds(new_funds)
    fund_tracker.FUNDS = new_funds
    return jsonify({'success': True})

@app.route('/api/estimates', methods=['GET'])
def get_estimates():
    # Force reload funds in case they changed
    fund_tracker.FUNDS = fund_tracker.load_funds()
    results = []
    
    # We can probably parallelize this or just loop. The original script loops.
    # To avoid blocking too long, we might limit it? Or just let it run.
    # Ideally should use a background task, but for simple script simple loop is fine.
    
    for fund in fund_tracker.FUNDS:
        try:
            # We can use the logic from main() but encapsulated
            res = fund_tracker.calculate_fund_estimate(fund)
            if res:
                results.append(res)
            else:
                 results.append({
                    "基金名称": fund['name'],
                    "基金代码": fund['code'],
                    "当前估值": "获取失败",
                    "涨跌幅": "0",
                    "error": True
                })
        except Exception as e:
             results.append({
                    "基金名称": fund['name'],
                    "基金代码": fund['code'],
                    "当前估值": "出错",
                    "涨跌幅": "0",
                    "error": str(e)
                })
    return jsonify(results)

@app.route('/api/fund_info/<string:code>', methods=['GET'])
def get_fund_info(code):
    # Try realtime data first as it is more likely to be up? Or basic info? 
    # fund_tracker.get_fund_realtime_data uses 1234567.com.cn which is good
    info = fund_tracker.get_fund_realtime_data(code)
    if info['success']:
        return jsonify({
            'fund_name': info['fund_name'],
            'type': 'active', # Default guess
            'success': True
        })
        
    return jsonify({'success': False, 'message': '无法获取基金信息'}), 404

@app.route('/api/sync', methods=['POST'])
def sync_vika():
    # Get latest estimates first
    fund_tracker.FUNDS = fund_tracker.load_funds()
    results = []
    for fund in fund_tracker.FUNDS:
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
    app.run(debug=True, port=5000)

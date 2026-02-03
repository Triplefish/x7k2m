# 🚀 基金实时估值追踪工具

一个完全免费的个人基金实时估值追踪工具，使用维格表展示，微信随时查看。

## ✨ 特点

- 💰 **完全免费**：使用免费的数据源和服务
- 📱 **微信可看**：维格表可以直接在微信打开
- 🔄 **自动更新**：GitHub Actions 定时运行，无需手动操作
- 📊 **准确可靠**：ETF联接基金估值准确度 95%+
- 🎯 **简单易用**：配置简单，5分钟部署完成

## 🎯 支持的基金类型

| 类型 | 估值方式 | 准确度 |
|------|---------|--------|
| ETF联接基金 | 直接使用ETF实时价格 | ⭐⭐⭐⭐⭐ |
| 主动型基金 | 使用相关指数估算 | ⭐⭐⭐ |
| 债券型基金 | 使用债券指数估算 | ⭐⭐ |

## 📦 技术栈

- **数据源**：AkShare（免费金融数据库）
- **展示平台**：维格表 Vika（免费智能表格）
- **自动化**：GitHub Actions（免费定时任务）
- **语言**：Python 3.10+

## 🚀 快速开始

### 1. 注册维格表

1. 访问 [https://vika.cn](https://vika.cn) 注册账号
2. 创建一个新的数据表
3. 获取 API Token：
   - 点击右上角头像 → 设置 → 开发者配置
   - 创建 API Token 并复制
4. 获取数据表 ID：
   - 打开数据表，URL 中 `dst` 后面的就是表格 ID
   - 例如：`https://vika.cn/workbench/dstXXXXXXXXXX/viwXXXXXXXX`
   - 数据表 ID 就是 `dstXXXXXXXXXX`

### 2. Fork 本仓库

1. 点击右上角 Fork 按钮
2. 将仓库 Fork 到你的账号下

### 3. 配置 Secrets

在你的仓库中：

1. 点击 `Settings` → `Secrets and variables` → `Actions`
2. 点击 `New repository secret`
3. 添加以下两个 secrets：

   - **Name**: `VIKA_API_TOKEN`  
     **Value**: 你的维格表 API Token
   
   - **Name**: `VIKA_DATASHEET_ID`  
     **Value**: 你的数据表 ID

### 4. 启用 Actions

1. 点击仓库的 `Actions` 标签
2. 点击 `I understand my workflows, go ahead and enable them`
3. 点击左侧的 `基金估值追踪` workflow
4. 点击 `Enable workflow`

### 5. 手动运行测试

1. 在 Actions 页面，点击 `基金估值追踪`
2. 点击右侧 `Run workflow` 按钮
3. 等待运行完成（约 1-2 分钟）
4. 打开维格表查看数据

## 📝 自定义基金列表

编辑 `fund_tracker.py` 文件中的 `FUNDS` 列表：

```python
FUNDS = [
    {
        "name": "你的基金名称",
        "code": "基金代码",
        "type": "etf_linked",  # 类型：etf_linked/active/bond
        "etf_code": "对应的ETF代码",
        "etf_name": "ETF名称"
    },
    # 添加更多基金...
]
```

### 基金类型说明

- **etf_linked**：ETF联接基金，需要提供 `etf_code` 和 `etf_name`
- **active**：主动型基金，需要提供 `index_code` 和 `index_name`
- **bond**：债券型基金，需要提供 `index_code` 和 `index_name`

## ⏰ 运行时间

默认配置：交易日（周一至周五）每小时运行一次，时间范围 9:30-15:00

修改运行时间请编辑 `.github/workflows/fund-tracker.yml` 中的 `cron` 表达式。

## 🧪 本地测试

在部署前，可以先本地测试数据获取是否正常：

```bash
# 安装依赖
pip install -r requirements.txt

# 运行测试脚本（不需要维格表配置）
python test_local.py
```

## 📊 维格表字段说明

| 字段名 | 说明 |
|--------|------|
| 基金名称 | 基金的完整名称 |
| 基金代码 | 6位数字代码 |
| 基金类型 | ETF联接/主动型/债券型 |
| 昨日净值 | 最新公布的净值 |
| 追踪标的 | 参考的ETF或指数 |
| 标的涨跌 | 标的今日涨跌幅 |
| 估算涨跌 | 基金估算涨跌幅 |
| 估算净值 | 估算的当前净值 |
| 估算增长 | 估算的绝对增长值 |
| 更新时间 | 数据更新时间戳 |
| 准确度 | 估值准确度说明 |

## 💡 常见问题

### Q: 为什么有些基金估值不准确？

**A**: 
- ETF联接基金：准确度最高（95%+），因为直接追踪ETF价格
- 主动型基金：只能用相关指数估算，存在较大偏差
- 债券型基金：债券价格不透明，仅供参考

### Q: 数据多久更新一次？

**A**: 默认交易日每小时更新一次（9:30-15:00）。你可以：
- 手动触发：在 Actions 页面点击 `Run workflow`
- 修改频率：编辑 workflow 文件的 cron 表达式

### Q: GitHub Actions 为什么没有运行？

**A**: 检查以下几点：
1. Actions 是否已启用
2. Secrets 是否正确配置
3. 是否在交易日的指定时间范围内
4. 检查 Actions 运行日志查看错误信息

### Q: 可以添加更多基金吗？

**A**: 当然可以！编辑 `fund_tracker.py` 中的 `FUNDS` 列表，添加你需要的基金即可。

### Q: 维格表免费版有限制吗？

**A**: 免费版每月 1 万次 API 调用，对于个人使用完全足够（每天更新 8 次，一个月才 240 次）。

## 🔒 数据安全

- 代码在你的私有仓库中运行
- API Token 存储在 GitHub Secrets 中加密保存
- 持仓数据只保存在你的维格表中
- 不会泄露任何个人信息

## 📈 后续优化建议

- [ ] 添加涨跌幅通知功能（邮件/微信）
- [ ] 添加历史数据记录和趋势分析
- [ ] 支持持仓金额计算
- [ ] 添加数据可视化图表
- [ ] 支持更多数据源备份

## 📄 开源协议

MIT License

## 🙏 致谢

- [AkShare](https://github.com/akfamily/akshare) - 优秀的金融数据接口库
- [维格表](https://vika.cn) - 强大的智能表格平台
- [GitHub Actions](https://github.com/features/actions) - 免费的CI/CD服务

---

⭐ 如果这个项目对你有帮助，欢迎 Star！

💬 有问题或建议？欢迎提 Issue！

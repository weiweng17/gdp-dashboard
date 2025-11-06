```markdown
// filepath: /workspaces/gdp-dashboard/README.md

## 部署到 Streamlit Community Cloud（share.streamlit.io）

以下说明帮助你把本仓库的一键部署到 Streamlit Community Cloud 并获得公网访问地址。

前置条件
- 代码已推送到 GitHub（仓库示例：`github.com/<your-username>/gdp-dashboard`）。
- `streamlit_app.py` 位于仓库根目录，且 `requirements.txt` 列出应用依赖（请按下方示例确认/更新）。

推荐的依赖（`requirements.txt`）
```
streamlit
pandas
numpy
plotly
openpyxl
```
说明：`numpy`、`plotly` 与 `openpyxl` 常用于本项目代码中的数据处理和可视化、Excel 读取，请确保包含以避免部署失败。

部署步骤（GUI）
1. 登录：https://share.streamlit.io ，使用你的 GitHub 帐号授权 Streamlit。
2. 点击 “New app” 或 “Create an app”。
3. 选择你的 GitHub 仓库（例如 `your-username/gdp-dashboard`），选择分支（如 `main`），并在 “Main file” 里选择 `streamlit_app.py`。
4. 点击 Deploy。平台会自动安装 `requirements.txt` 中的依赖并启动应用。
5. 部署成功后，页面会显示一个公网 URL（格式类似 `https://share.streamlit.io/<user>/<repo>/<branch>/streamlit_app.py`），打开即可访问。

命令行部署/验证（可选）
- 部署后检查 HTTP 响应：
```bash
curl -I https://share.streamlit.io/<your-user>/<repo>/<branch>/streamlit_app.py
```
- 若需要在本地模拟运行（调试用）：
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

常见问题与解决
- 构建失败提示 `ModuleNotFoundError`：在 `requirements.txt` 中加入缺失包名，提交并推送后 Streamlit Cloud 会自动触发重部署。
- 需要私密信息（API keys 等）：不要把 secrets 放到仓库，进入 Streamlit Cloud 的应用页面 -> Settings -> Secrets，添加键值对，代码中用 `st.secrets["KEY_NAME"]` 读取。
- 指定 Python 版本：可在仓库根添加 `runtime.txt`（例如 `python-3.10.12`）以强制使用特定版本（可选）。

如果在 Cloud 控制台看到部署失败或日志报错，把日志贴过来我会帮你定位并给出修复补丁。
```
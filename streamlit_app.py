import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os
import threading
import time
import webbrowser
import warnings

# 忽略警告
warnings.filterwarnings("ignore")

# 自动打开浏览器功能
def open_streamlit_browser():
    """在Streamlit启动后自动打开浏览器"""
    time.sleep(4)  # 给Streamlit更多时间启动
    try:
        # 尝试多个可能的端口
        ports = [8501, 8502, 8503, 8504, 8505]
        for port in ports:
            try:
                webbrowser.open_new(f"http://localhost:{port}")
                print(f"尝试打开浏览器: http://localhost:{port}")
                break
            except:
                continue
    except Exception as e:
        print(f"自动打开浏览器失败: {e}")
        print("请手动打开浏览器并访问: http://localhost:8501")

# 只在打包环境下启用自动打开浏览器
if getattr(sys, 'frozen', False):
    # 打包环境
    threading.Thread(target=open_streamlit_browser, daemon=True).start()
else:
    # 开发环境，使用Streamlit默认行为
    pass

# 你的原有代码从这里开始...
# 获取当前脚本的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 将当前目录添加到sys.path的最前面
sys.path.insert(0, current_dir)

# 显示调试信息
st.write("## 调试信息")
st.write(f"当前目录: {current_dir}")
st.write(f"analyzer.py 存在: {os.path.exists(os.path.join(current_dir, 'analyzer.py'))}")
st.write(f"enhanced_analyzer.py 存在: {os.path.exists(os.path.join(current_dir, 'enhanced_analyzer.py'))}")

# 尝试导入外部模块，如果失败则使用内置分析器
external_modules_loaded = False
try:
    from analyzer import *
    from enhanced_analyzer import *

    external_modules_loaded = True
    st.success("✅ 外部模块导入成功")
except ImportError as e:
    st.warning(f"⚠️ 外部模块导入失败: {e}，使用内置分析器")
    st.write("Python路径:")
    for path in sys.path:
        st.write(f"- {path}")


# 完全独立的销售分析仪表板 - 不依赖任何外部模块
class BuiltInAnalyzer:
    """内置分析器 - 替代所有外部模块"""

    def __init__(self):
        self.df = None
        self.analysis_results = {}

    def preprocess_data(self, df):
        """数据预处理"""
        df_clean = df.copy()

        # 处理日期字段
        date_columns = ['日期', 'sku首次销售时间_分区域', 'sku首次入库时间_分区域']
        for col in date_columns:
            if col in df_clean.columns:
                df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')

        # 处理数值字段
        numeric_columns = ['销售金额', '利润', '利润率', '销售个数', '在库数量', '在库金额',
                           '平台费用', '头程费用', '后程费用', '广告费', '商品成本', '销售计划']
        for col in numeric_columns:
            if col in df_clean.columns:
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

        # 修复 Arrow 兼容性问题
        for col in df_clean.columns:
            if df_clean[col].dtype == 'object':
                df_clean[col] = df_clean[col].astype(str)

        # 提取年月信息
        if '日期' in df_clean.columns:
            df_clean['年月'] = df_clean['日期'].dt.to_period('M').astype(str)
        else:
            current_month = datetime.now().strftime("%Y-%m")
            df_clean['年月'] = current_month

        return df_clean

    def run_all_analysis(self, df):
        """执行所有分析"""
        self.df = df
        self.analysis_results = {}

        # 基础统计分析
        self.run_basic_analysis()

        # 分类分析
        if '小分类' in self.df.columns:
            self.run_category_analysis()

        # 月度分析
        if '年月' in self.df.columns:
            self.run_monthly_analysis()

        # 产品分析
        self.run_product_analysis()

        # 滞销分析
        self.run_unsold_analysis()

        return self.analysis_results

    def run_basic_analysis(self):
        """基础统计分析"""
        basic_stats = {}

        if '销售金额' in self.df.columns:
            basic_stats['总销售额'] = self.df['销售金额'].sum()
            basic_stats['平均销售额'] = self.df['销售金额'].mean()
            basic_stats['最大销售额'] = self.df['销售金额'].max()

        if '利润' in self.df.columns:
            basic_stats['总利润'] = self.df['利润'].sum()
            basic_stats['平均利润'] = self.df['利润'].mean()
            if basic_stats.get('总销售额', 0) > 0:
                basic_stats['平均利润率'] = (basic_stats['总利润'] / basic_stats['总销售额'] * 100)

        if 'SKU编码' in self.df.columns:
            basic_stats['SKU总数'] = self.df['SKU编码'].nunique()

        self.analysis_results['basic_stats'] = basic_stats

    def run_category_analysis(self):
        """分类分析"""
        category_analysis = self.df.groupby('小分类').agg({
            '销售金额': 'sum',
            '利润': 'sum',
            'SKU编码': 'nunique'
        }).round(2)

        # 计算利润率
        if '销售金额' in category_analysis.columns and '利润' in category_analysis.columns:
            category_analysis['利润率'] = (category_analysis['利润'] / category_analysis['销售金额'] * 100).round(2)

        category_analysis = category_analysis.sort_values('销售金额', ascending=False)
        self.analysis_results['category_analysis'] = category_analysis

    def run_monthly_analysis(self):
        """月度分析"""
        monthly_analysis = self.df.groupby('年月').agg({
            '销售金额': 'sum',
            '利润': 'sum',
            'SKU编码': 'nunique'
        }).round(2)

        # 计算环比
        monthly_analysis = monthly_analysis.sort_index()
        for col in ['销售金额', '利润']:
            if col in monthly_analysis.columns:
                monthly_analysis[f'{col}_环比%'] = monthly_analysis[col].pct_change() * 100
                monthly_analysis[f'{col}_环比%'] = monthly_analysis[f'{col}_环比%'].round(2)

        self.analysis_results['monthly_analysis'] = monthly_analysis

    def run_product_analysis(self):
        """产品分析"""
        if 'SKU编码' not in self.df.columns:
            return

        # 热销产品
        product_sales = self.df.groupby('SKU编码').agg({
            '销售金额': 'sum',
            '利润': 'sum',
            '销售个数': 'sum'
        }).round(2).sort_values('销售金额', ascending=False)

        # 计算产品利润率
        if '销售金额' in product_sales.columns and '利润' in product_sales.columns:
            product_sales['利润率'] = (product_sales['利润'] / product_sales['销售金额'] * 100).round(2)

        self.analysis_results['product_analysis'] = product_sales.head(20)

    def run_unsold_analysis(self):
        """滞销产品分析"""
        if '年月' not in self.df.columns or 'SKU编码' not in self.df.columns:
            return

        # 获取月份范围
        months = sorted(self.df['年月'].unique())
        if len(months) < 2:
            return

        # 检查最近3个月的销售情况
        recent_months = months[-3:] if len(months) >= 3 else months
        all_skus = self.df['SKU编码'].unique()

        # 找出在最近几个月有销售的SKU
        recent_sales = self.df[self.df['年月'].isin(recent_months)]
        sold_skus = recent_sales['SKU编码'].unique()

        # 找出滞销SKU
        unsold_skus = list(set(all_skus) - set(sold_skus))

        # 获取滞销SKU的详细信息
        if unsold_skus:
            unsold_details = self.df[self.df['SKU编码'].isin(unsold_skus)][
                ['SKU编码', '商品名称', '小分类', '在库数量', '在库金额']
            ].drop_duplicates('SKU编码')

            # 计算最后一次销售时间
            last_sales = self.df.groupby('SKU编码')['年月'].max().reset_index()
            last_sales.columns = ['SKU编码', '最后销售月份']

            unsold_details = unsold_details.merge(last_sales, on='SKU编码', how='left')

            # 计算滞销月数
            current_month = months[-1]
            unsold_details['滞销月数'] = unsold_details['最后销售月份'].apply(
                lambda x: len(months) - months.index(x) - 1 if x in months else len(months)
            )

            # 按滞销月数排序
            unsold_details = unsold_details.sort_values(['滞销月数', '在库金额'], ascending=[False, False])

            self.analysis_results['unsold_analysis'] = {
                'unsold_products': unsold_details,
                'total_skus': len(all_skus),
                'sold_skus': len(sold_skus),
                'unsold_skus': len(unsold_skus)
            }


class SalesDashboard:
    """销售仪表板 - 完全独立版本"""

    def __init__(self):
        self.df = None
        self.filtered_df = None
        self.analyzer = BuiltInAnalyzer()
        self.analysis_results = {}

    def run(self):
        """运行仪表板"""
        st.set_page_config(
            page_title="智能销售分析系统",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # 标题和说明
        st.title("🤖 智能销售分析系统")
        st.markdown("""
        欢迎使用智能销售分析系统！本系统提供：
        - 📊 **基础业务分析** - 销售数据和利润分析
        - 🎯 **智能洞察** - 基于数据的业务建议  
        - 📈 **趋势分析** - 销售趋势和分布分析
        - 🔄 **实时交互** - 动态筛选和可视化
        """)

        # 文件上传
        uploaded_file = st.sidebar.file_uploader(
            "上传销售数据文件",
            type=['csv', 'xlsx'],
            help="支持CSV和Excel格式"
        )

        if uploaded_file is not None:
            self.process_uploaded_file(uploaded_file)
        else:
            self.show_welcome()

    def show_welcome(self):
        """显示欢迎页面"""
        st.info("👆 请在左侧上传您的销售数据文件开始分析")

        # 显示示例数据结构
        st.subheader("📋 期望的数据结构")
        example_data = {
            'SKU编码': ['SKU001', 'SKU002', 'SKU003'],
            '商品名称': ['商品A', '商品B', '商品C'],
            '小分类': ['分类1', '分类2', '分类1'],
            '日期': ['2023-01-01', '2023-01-02', '2023-01-03'],
            '销售金额': [1000, 1500, 800],
            '利润': [200, 300, 150],
            '销售个数': [10, 15, 8],
            '在库数量': [50, 30, 20],
            '在库金额': [5000, 3000, 2000]
        }
        st.dataframe(pd.DataFrame(example_data))

    def process_uploaded_file(self, uploaded_file):
        """处理上传的文件"""
        try:
            # 显示文件信息
            file_details = {
                "文件名": uploaded_file.name,
                "文件类型": uploaded_file.type,
                "文件大小": f"{uploaded_file.size / 1024:.1f} KB"
            }

            with st.expander("📁 文件信息", expanded=False):
                st.json(file_details)

            # 读取数据
            with st.spinner("📥 读取数据文件中..."):
                if uploaded_file.name.endswith('.csv'):
                    # 尝试多种编码
                    encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312']
                    for encoding in encodings:
                        try:
                            uploaded_file.seek(0)  # 重置文件指针
                            self.df = pd.read_csv(uploaded_file, encoding=encoding)
                            st.success(f"使用编码: {encoding}")
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        st.error("无法解码CSV文件，请检查文件编码")
                        return
                else:
                    self.df = pd.read_excel(uploaded_file)

            # 数据预处理
            with st.spinner("🔄 预处理数据..."):
                self.df = self.analyzer.preprocess_data(self.df)

            # 显示数据预览
            with st.expander("🔍 数据预览", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"数据形状: {self.df.shape}")
                    st.write("列名:", list(self.df.columns))
                with col2:
                    st.write("数据类型:")
                    st.write(self.df.dtypes.astype(str))

                st.dataframe(self.df.head(10), use_container_width=True)

            # 检查必要字段
            required_columns = ['销售金额', 'SKU编码']
            missing_columns = [col for col in required_columns if col not in self.df.columns]
            if missing_columns:
                st.error(f"缺少必要字段: {missing_columns}")
                st.info("请确保数据包含以下字段: 销售金额, SKU编码")
                return

            # 执行分析
            with st.spinner("🔍 执行数据分析..."):
                self.analysis_results = self.analyzer.run_all_analysis(self.df)

            # 显示分析结果
            self.display_analysis_results()

        except Exception as e:
            st.error(f"处理文件时发生错误: {str(e)}")
            st.info("请检查文件格式是否正确")

    def display_analysis_results(self):
        """显示分析结果"""
        # 侧边栏控制
        st.sidebar.header("🎛️ 分析控制")

        # 数据筛选
        st.sidebar.subheader("数据筛选")

        # 日期筛选（如果存在日期字段）
        if '日期' in self.df.columns:
            date_col = pd.to_datetime(self.df['日期'], errors='coerce')
            min_date = date_col.min()
            max_date = date_col.max()

            if not pd.isna(min_date) and not pd.isna(max_date):
                date_range = st.sidebar.date_input(
                    "选择日期范围",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )
                if len(date_range) == 2:
                    mask = (date_col >= pd.to_datetime(date_range[0])) & (date_col <= pd.to_datetime(date_range[1]))
                    filtered_df = self.df[mask]
                else:
                    filtered_df = self.df
            else:
                filtered_df = self.df
        else:
            filtered_df = self.df

        # 小分类筛选
        if '小分类' in filtered_df.columns:
            categories = ['全部'] + sorted(filtered_df['小分类'].dropna().unique().tolist())
            selected_category = st.sidebar.selectbox("选择小分类", categories)
            if selected_category != '全部':
                filtered_df = filtered_df[filtered_df['小分类'] == selected_category]

        # 保存筛选后的数据
        self.filtered_df = filtered_df

        # 重要：使用筛选后的数据重新执行分析
        with st.spinner("🔄 根据筛选条件更新分析..."):
            self.analysis_results = self.analyzer.run_all_analysis(self.filtered_df)

        # 分析模块选择
        analysis_modules = st.sidebar.multiselect(
            "选择分析模块",
            ["概览仪表板", "分类分析", "月度趋势", "产品分析", "滞销分析", "数据洞察"],
            default=["概览仪表板", "分类分析", "产品分析"]
        )

        # 显示选中的分析模块
        if "概览仪表板" in analysis_modules:
            self.display_overview_dashboard()

        if "分类分析" in analysis_modules:
            self.display_category_analysis()

        if "月度趋势" in analysis_modules:
            self.display_monthly_trends()

        if "产品分析" in analysis_modules:
            self.display_product_analysis()

        if "滞销分析" in analysis_modules:
            self.display_unsold_analysis()

        if "数据洞察" in analysis_modules:
            self.display_data_insights()

    def display_overview_dashboard(self):
        """显示概览仪表板"""
        st.header("📊 业务概览仪表板")

        if 'basic_stats' not in self.analysis_results:
            st.warning("暂无基础统计数据")
            return

        basic_stats = self.analysis_results['basic_stats']

        # 关键指标卡片
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="总销售额",
                value=f"¥{basic_stats.get('总销售额', 0):,.0f}",
                delta=None
            )

        with col2:
            st.metric(
                label="总利润",
                value=f"¥{basic_stats.get('总利润', 0):,.0f}",
                delta=None
            )

        with col3:
            avg_margin = basic_stats.get('平均利润率', 0)
            st.metric(
                label="平均利润率",
                value=f"{avg_margin:.1f}%",
                delta=None
            )

        with col4:
            st.metric(
                label="SKU总数",
                value=f"{basic_stats.get('SKU总数', 0):,}",
                delta=None
            )

        # 销售分布图表
        col1, col2 = st.columns(2)

        with col1:
            if 'category_analysis' in self.analysis_results:
                category_data = self.analysis_results['category_analysis']
                if not category_data.empty:
                    # 确保数据长度一致
                    top_categories = category_data.head(10)
                    if len(top_categories) > 0 and len(top_categories.index) == len(top_categories['销售金额']):
                        fig = px.pie(
                            top_categories,
                            values='销售金额',
                            names=top_categories.index,
                            title="销售额分类分布 (Top 10)"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("分类数据格式不正确，无法绘制饼图")

        with col2:
            if 'product_analysis' in self.analysis_results:
                product_data = self.analysis_results['product_analysis']
                if not product_data.empty:
                    # 确保数据长度一致
                    top_products = product_data.head(10)
                    if len(top_products) > 0 and len(top_products.index) == len(top_products['销售金额']):
                        fig = px.bar(
                            top_products,
                            x=top_products.index,
                            y='销售金额',
                            title="Top 10 热销产品"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("产品数据格式不正确，无法绘制条形图")

    def display_category_analysis(self):
        """显示分类分析"""
        st.header("📈 分类分析")

        if 'category_analysis' not in self.analysis_results:
            st.warning("暂无分类分析数据")
            return

        category_data = self.analysis_results['category_analysis']

        if category_data.empty:
            st.warning("分类分析数据为空")
            return

        # 分类分析表格
        st.dataframe(category_data, use_container_width=True)

        # 分类可视化
        col1, col2 = st.columns(2)

        with col1:
            # 确保数据长度一致
            top_categories = category_data.head(15)
            if len(top_categories) > 0 and len(top_categories.index) == len(top_categories['销售金额']):
                fig = px.bar(
                    top_categories,
                    x=top_categories.index,
                    y='销售金额',
                    title="各分类销售额 (Top 15)",
                    color='销售金额'
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("无法绘制分类销售额图表 - 数据格式问题")

        with col2:
            if '利润率' in category_data.columns:
                # 确保数据长度一致
                top_categories = category_data.head(15)
                if len(top_categories) > 0 and len(top_categories.index) == len(top_categories['利润率']):
                    fig = px.bar(
                        top_categories,
                        x=top_categories.index,
                        y='利润率',
                        title="各分类利润率 (Top 15)",
                        color='利润率'
                    )
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("无法绘制分类利润率图表 - 数据格式问题")

    def display_product_analysis(self):
        """显示产品分析"""
        st.header("🏆 产品分析")

        if 'product_analysis' not in self.analysis_results:
            st.warning("暂无产品分析数据")
            return

        product_data = self.analysis_results['product_analysis']

        if product_data.empty:
            st.warning("产品分析数据为空")
            return

        # 产品分析表格
        st.dataframe(product_data, use_container_width=True)

        # 产品分析可视化
        col1, col2 = st.columns(2)

        with col1:
            # 确保数据长度一致
            top_products = product_data.head(20)
            if len(top_products) > 0 and len(top_products.index) == len(top_products['销售金额']) == len(
                    top_products['利润率']):
                fig = px.scatter(
                    top_products,
                    x='销售金额',
                    y='利润率',
                    size='销售个数',
                    hover_name=top_products.index,
                    title="产品销售额 vs 利润率 (Top 20)",
                    color='销售金额'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("无法绘制产品散点图 - 数据格式问题")

        with col2:
            # 确保数据长度一致
            top_products = product_data.head(20)
            if len(top_products) > 0 and len(top_products.index) == len(top_products['销售金额']):
                fig = px.treemap(
                    top_products,
                    path=[px.Constant("所有产品"), top_products.index],
                    values='销售金额',
                    title="产品销售额分布 (Top 20)"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("无法绘制产品树状图 - 数据格式问题")

    def display_monthly_trends(self):
        """显示月度趋势"""
        st.header("📅 月度趋势分析")

        if 'monthly_analysis' not in self.analysis_results:
            st.warning("暂无月度分析数据")
            return

        monthly_data = self.analysis_results['monthly_analysis']

        if monthly_data.empty:
            st.warning("月度分析数据为空")
            return

        # 月度趋势表格
        st.dataframe(monthly_data, use_container_width=True)

        # 月度趋势图表
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=monthly_data.index,
            y=monthly_data['销售金额'],
            mode='lines+markers',
            name='销售额',
            line=dict(color='blue', width=3)
        ))

        if '利润' in monthly_data.columns:
            fig.add_trace(go.Scatter(
                x=monthly_data.index,
                y=monthly_data['利润'],
                mode='lines+markers',
                name='利润',
                line=dict(color='green', width=3)
            ))

        fig.update_layout(
            title="月度销售趋势",
            xaxis_title="月份",
            yaxis_title="金额",
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

    def display_product_analysis(self):
        """显示产品分析"""
        st.header("🏆 产品分析")

        if 'product_analysis' not in self.analysis_results:
            st.warning("暂无产品分析数据")
            return

        product_data = self.analysis_results['product_analysis']

        if product_data.empty:
            st.warning("产品分析数据为空")
            return

        # 产品分析表格
        st.dataframe(product_data, use_container_width=True)

        # 产品分析可视化
        col1, col2 = st.columns(2)

        with col1:
            fig = px.scatter(
                product_data.head(20),
                x='销售金额',
                y='利润率',
                size='销售个数',
                hover_name=product_data.index,
                title="产品销售额 vs 利润率",
                color='销售金额'
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.treemap(
                product_data.head(20),
                path=[px.Constant("所有产品"), product_data.index],
                values='销售金额',
                title="产品销售额分布"
            )
            st.plotly_chart(fig, use_container_width=True)

    def display_unsold_analysis(self):
        """显示滞销分析"""
        st.header("📦 滞销产品分析")

        if 'unsold_analysis' not in self.analysis_results:
            st.warning("暂无滞销分析数据")
            return

        unsold_data = self.analysis_results['unsold_analysis']

        # 滞销概况
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="总SKU数",
                value=unsold_data.get('total_skus', 0)
            )

        with col2:
            st.metric(
                label="有销售SKU",
                value=unsold_data.get('sold_skus', 0)
            )

        with col3:
            st.metric(
                label="滞销SKU",
                value=unsold_data.get('unsold_skus', 0)
            )

        # 滞销产品详情
        if 'unsold_products' in unsold_data and not unsold_data['unsold_products'].empty:
            st.subheader("滞销产品清单")
            unsold_products = unsold_data['unsold_products']
            st.dataframe(unsold_products, use_container_width=True)

            # 滞销分析可视化
            col1, col2 = st.columns(2)

            with col1:
                if '小分类' in unsold_products.columns:
                    category_unsold = unsold_products.groupby('小分类').size().reset_index(name='滞销数量')
                    fig = px.bar(
                        category_unsold,
                        x='小分类',
                        y='滞销数量',
                        title="各分类滞销产品数量"
                    )
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                if '在库金额' in unsold_products.columns:
                    fig = px.histogram(
                        unsold_products,
                        x='滞销月数',
                        y='在库金额',
                        title="滞销月数与在库金额分布"
                    )
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("🎉 没有发现滞销产品！")

    def display_data_insights(self):
        """显示数据洞察"""
        st.header("💡 数据洞察与建议")

        insights = []

        # 基于分析结果生成洞察
        if 'basic_stats' in self.analysis_results:
            basic_stats = self.analysis_results['basic_stats']

            # 利润率洞察
            avg_margin = basic_stats.get('平均利润率', 0)
            if avg_margin < 10:
                insights.append("⚠️ **利润率偏低**: 当前平均利润率较低，建议优化成本结构或调整定价策略")
            elif avg_margin > 30:
                insights.append("✅ **利润率良好**: 当前利润率表现优秀，继续保持")

            # 销售额洞察
            total_sales = basic_stats.get('总销售额', 0)
            if total_sales == 0:
                insights.append("❌ **无销售数据**: 上传的数据中没有销售记录")

        # 滞销产品洞察
        if 'unsold_analysis' in self.analysis_results:
            unsold_data = self.analysis_results['unsold_analysis']
            unsold_count = unsold_data.get('unsold_skus', 0)
            total_skus = unsold_data.get('total_skus', 1)
            unsold_ratio = (unsold_count / total_skus) * 100

            if unsold_ratio > 30:
                insights.append(f"🚨 **高滞销率**: {unsold_ratio:.1f}%的产品处于滞销状态，建议清理库存")
            elif unsold_ratio > 0:
                insights.append(f"📝 **存在滞销产品**: 有{unsold_count}个SKU需要关注")

        # 分类洞察
        if 'category_analysis' in self.analysis_results:
            category_data = self.analysis_results['category_analysis']
            if not category_data.empty:
                top_category = category_data.index[0]
                top_sales = category_data.iloc[0]['销售金额']
                insights.append(f"🏆 **优势品类**: '{top_category}'是销售额最高的分类，贡献了¥{top_sales:,.0f}的销售额")

        # 显示洞察
        if insights:
            for i, insight in enumerate(insights, 1):
                st.info(f"{i}. {insight}")
        else:
            st.warning("暂无数据洞察")

        # 行动建议
        st.subheader("🎯 建议行动")
        st.markdown("""
        1. **定期监控** - 每周查看销售数据和关键指标
        2. **库存优化** - 及时处理滞销产品，优化库存结构
        3. **品类管理** - 加强优势品类，优化弱势品类
        4. **定价策略** - 根据利润率数据调整产品定价
        5. **促销规划** - 针对滞销产品制定促销计划
        """)


# 运行应用
if __name__ == "__main__":
    dashboard = SalesDashboard()
    dashboard.run()
    
# deployed trigger: Thu Nov  6 06:06:53 UTC 2025

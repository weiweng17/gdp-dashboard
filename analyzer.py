import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys
from io import BytesIO

# 修复Windows编码问题
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加自定义模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 其余现有代码保持不变...
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys
from io import BytesIO

# 添加自定义模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入自定义模块
try:
    from analysis_config import ANALYSIS_MODULES, FIELD_MAPPING, REPORT_CONFIG
    from visualization import SalesVisualizer

    HAS_CUSTOM_MODULES = True
except ImportError as e:
    print(f"⚠️ 自定义模块加载失败: {e}")
    print("将继续使用基础功能")
    HAS_CUSTOM_MODULES = False

warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


class MonthlySalesAnalyzer:
    def __init__(self):
        """
        初始化分析器
        """
        self.file_path = None
        self.df = None
        self.raw_df = None
        self.analysis_date = datetime.now().strftime("%Y-%m-%d")
        self.analysis_results = {}
        self.visualizer = None
        self.chart_images = {}

        # 加载配置
        if HAS_CUSTOM_MODULES:
            self.analysis_modules = ANALYSIS_MODULES
            self.field_mapping = FIELD_MAPPING
            self.report_config = REPORT_CONFIG
            print("✅ 自定义配置模块加载成功")
        else:
            # 默认配置
            self.analysis_modules = {
                'category': '小分类分析',
                'sales_plan': '销售计划完成情况',
                'unsold_products': '滞销产品分析',
                'profit_analysis': '利润分析',
                'monthly_comparison': '月度对比分析'
            }
            self.field_mapping = {}
            self.report_config = {
                'unsold_months_threshold': 3,  # 滞销产品判定阈值（月）
                'low_profit_threshold': 0.05,  # 低利润阈值（5%）
                'sales_drop_threshold': 0.3,  # 销售下降阈值（30%）
                'top_n_products': 20
            }
            print("ℹ️  使用默认配置")

    def select_file(self):
        """
        使用弹窗选择CSV文件
        """
        root = tk.Tk()
        root.withdraw()

        file_types = [
            ("CSV files", "*.csv"),
            ("Excel files", "*.xlsx"),
            ("All files", "*.*")
        ]

        file_path = filedialog.askopenfilename(
            title="选择销售数据文件",
            filetypes=file_types,
            initialdir=os.getcwd()
        )

        root.destroy()

        if file_path:
            self.file_path = file_path
            print(f"📁 已选择文件: {os.path.basename(file_path)}")
            return True
        else:
            print("❌ 未选择文件，程序退出")
            return False

    def load_data(self):
        """
        加载数据文件
        """
        if not self.file_path:
            print("❌ 文件路径为空")
            return False

        try:
            if not os.path.exists(self.file_path):
                print(f"❌ 文件不存在: {self.file_path}")
                return False

            print("⏳ 正在加载数据文件...")

            # 根据文件类型选择加载方式
            if self.file_path.endswith('.csv'):
                encodings = ['utf-8-sig', 'gbk', 'gb2312', 'utf-8']
                for encoding in encodings:
                    try:
                        self.raw_df = pd.read_csv(self.file_path, encoding=encoding, low_memory=False)
                        self.df = self.raw_df.copy()
                        print(f"✅ CSV数据加载成功！使用编码: {encoding}")
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    print("❌ 无法解码CSV文件，请检查文件编码")
                    return False
            elif self.file_path.endswith('.xlsx'):
                try:
                    self.raw_df = pd.read_excel(self.file_path)
                    self.df = self.raw_df.copy()
                    print("✅ Excel数据加载成功！")
                except Exception as e:
                    print(f"❌ Excel文件加载失败: {e}")
                    return False
            else:
                print("❌ 不支持的文件格式")
                return False

            print(f"📊 数据形状: {self.df.shape} (行数: {len(self.df)}, 列数: {len(self.df.columns)})")
            print(f"📋 数据列名: {list(self.df.columns)}")

            return True

        except Exception as e:
            print(f"❌ 数据加载失败: {e}")
            return False

    def preprocess_data(self):
        """
        数据预处理
        """
        df_clean = self.df.copy()

        print("🔄 正在预处理数据...")
        print(f"   原始数据行数: {len(df_clean)}")

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

        # 过滤无效数据
        initial_count = len(df_clean)
        required_columns = []
        if '销售金额' in df_clean.columns:
            required_columns.append('销售金额')
        if 'SKU编码' in df_clean.columns:
            required_columns.append('SKU编码')

        if required_columns:
            df_clean = df_clean.dropna(subset=required_columns, how='any')
            final_count = len(df_clean)
            print(f"✅ 数据清洗完成，过滤掉 {initial_count - final_count} 条无效记录")

        # 提取年月信息用于月度分析
        if '日期' in df_clean.columns:
            df_clean['年月'] = df_clean['日期'].dt.to_period('M').astype(str)
        elif 'Year of 日期' in df_clean.columns and 'Month of 日期' in df_clean.columns:
            df_clean['年月'] = df_clean['Year of 日期'].astype(str) + '-' + df_clean['Month of 日期'].astype(
                str).str.zfill(2)
        else:
            current_month = datetime.now().strftime("%Y-%m")
            df_clean['年月'] = current_month
            print("   ⚠️ 未找到日期字段，使用当前月份")

        self.df = df_clean
        return df_clean

    def check_required_columns(self):
        """
        检查必要的列是否存在
        """
        required_columns = ['销售金额', 'SKU编码', '小分类']
        missing_columns = [col for col in required_columns if col not in self.df.columns]

        if missing_columns:
            print(f"⚠️  缺少必要字段: {missing_columns}")
            print(f"   可用字段: {list(self.df.columns)}")
            return False
        return True

    def run_category_analysis(self):
        """
        1. 小分类收入和利润分析
        """
        print("🏷️ 执行小分类收入和利润分析...")

        if '小分类' not in self.df.columns:
            print("❌ 缺少小分类字段")
            return None

        category_analysis = self.df.groupby('小分类').agg({
            '销售金额': 'sum',
            '利润': 'sum',
            '销售个数': 'sum',
            'SKU编码': 'nunique'
        }).round(2)

        # 计算利润率
        if '销售金额' in category_analysis.columns and '利润' in category_analysis.columns:
            category_analysis['利润率'] = (category_analysis['利润'] / category_analysis['销售金额'] * 100).round(2)

        # 按销售额排序
        category_analysis = category_analysis.sort_values('销售金额', ascending=False)

        # 生成改进建议
        suggestions = []
        for category, row in category_analysis.iterrows():
            suggestion = f"{category}: "

            if row.get('利润率', 0) < 5:
                suggestion += "利润率过低，建议优化成本或调整定价；"
            elif row.get('利润率', 0) > 20:
                suggestion += "利润率良好，可考虑加大推广；"

            if row.get('销售金额', 0) < category_analysis['销售金额'].quantile(0.25):
                suggestion += "销售额偏低，需要重点关注；"
            elif row.get('销售金额', 0) > category_analysis['销售金额'].quantile(0.75):
                suggestion += "销售额表现优秀，可总结经验；"

            if 'SKU编码' in row and row['SKU编码'] < 3:
                suggestion += "SKU数量较少，考虑丰富产品线；"

            suggestions.append(suggestion)

        category_analysis['改进建议'] = suggestions

        self.analysis_results['category_analysis'] = category_analysis
        return category_analysis

    def run_sales_plan_analysis(self):
        """
        2. 销售计划完成情况分析
        """
        print("📊 执行销售计划完成情况分析...")

        if '销售计划' not in self.df.columns:
            print("⚠️ 缺少销售计划字段，跳过此分析")
            return None

        # 按小分类分析计划完成情况
        plan_analysis = self.df.groupby('小分类').agg({
            '销售金额': 'sum',
            '销售计划': 'sum',
            'SKU编码': 'nunique'
        }).round(2)

        # 计算完成率
        plan_analysis['完成率'] = (plan_analysis['销售金额'] / plan_analysis['销售计划'] * 100).round(2)

        # 识别需要关注的SKU
        sku_analysis = self.df.groupby(['SKU编码', '商品名称', '小分类']).agg({
            '销售金额': 'sum',
            '销售计划': 'sum',
            '销售个数': 'sum'
        }).round(2)

        sku_analysis['完成率'] = (sku_analysis['销售金额'] / sku_analysis['销售计划'] * 100).round(2)

        # 标记需要重点关注的SKU
        focus_skus = sku_analysis[
            (sku_analysis['完成率'] < 50) |
            (sku_analysis['销售金额'] < sku_analysis['销售计划'] * 0.5)
            ].sort_values('完成率')

        results = {
            'category_plan': plan_analysis,
            'sku_plan': sku_analysis,
            'focus_skus': focus_skus
        }

        self.analysis_results['sales_plan_analysis'] = results
        return results

    def run_unsold_analysis(self):
        """
        3. 滞销产品分析
        """
        print("📦 执行滞销产品分析...")

        # 获取数据中的月份范围
        if '年月' not in self.df.columns:
            print("❌ 无法确定月份信息")
            return None

        months = sorted(self.df['年月'].unique())
        print(f"   数据包含月份: {months}")

        # 确定滞销阈值（最近N个月）
        unsold_threshold = self.report_config.get('unsold_months_threshold', 3)
        recent_months = months[-unsold_threshold:] if len(months) >= unsold_threshold else months

        print(f"   检查最近 {len(recent_months)} 个月的销售情况: {recent_months}")

        # 找出所有SKU
        all_skus = self.df['SKU编码'].unique()

        # 找出在最近几个月有销售的SKU
        recent_sales = self.df[self.df['年月'].isin(recent_months)]
        sold_skus = recent_sales['SKU编码'].unique()

        # 找出滞销SKU（在最近几个月没有销售）
        unsold_skus = list(set(all_skus) - set(sold_skus))

        print(f"   总SKU数量: {len(all_skus)}, 近期销售SKU: {len(sold_skus)}, 滞销SKU: {len(unsold_skus)}")

        # 获取滞销SKU的详细信息
        unsold_details = self.df[self.df['SKU编码'].isin(unsold_skus)][
            ['SKU编码', '商品名称', '小分类', '在库数量', '在库金额']
        ].drop_duplicates('SKU编码')

        # 计算最后一次销售时间
        last_sales = self.df.groupby('SKU编码')['年月'].max().reset_index()
        last_sales.columns = ['SKU编码', '最后销售月份']

        unsold_details = unsold_details.merge(last_sales, on='SKU编码', how='left')

        # 计算滞销月数
        current_month = months[-1] if months else datetime.now().strftime("%Y-%m")
        unsold_details['滞销月数'] = unsold_details['最后销售月份'].apply(
            lambda x: len(months) - months.index(x) - 1 if x in months else len(months)
        )

        # 按滞销月数排序
        unsold_details = unsold_details.sort_values(['滞销月数', '在库金额'], ascending=[False, False])

        # 生成维护建议
        maintenance_suggestions = []
        for _, row in unsold_details.iterrows():
            suggestion = f"{row['SKU编码']}({row['商品名称']}): "

            if row['滞销月数'] >= 6:
                suggestion += "长期滞销，建议清仓处理；"
            elif row['滞销月数'] >= 3:
                suggestion += "滞销时间较长，需要促销活动；"
            else:
                suggestion += "近期滞销，需要关注销售趋势；"

            if row.get('在库金额', 0) > 10000:
                suggestion += "库存金额较高，优先处理；"

            maintenance_suggestions.append(suggestion)

        unsold_details['维护建议'] = maintenance_suggestions

        self.analysis_results['unsold_analysis'] = {
            'unsold_products': unsold_details,
            'analysis_period': recent_months,
            'total_skus': len(all_skus),
            'sold_skus': len(sold_skus),
            'unsold_skus': len(unsold_skus)
        }

        return unsold_details

    def run_profit_analysis(self):
        """
        4. 利润分析及月份对比
        """
        print("执行利润分析及月份对比...")

        # 检查必要的列是否存在
        if '年月' not in self.df.columns or '利润' not in self.df.columns:
            print("缺少必要的利润或日期字段，跳过利润分析")
            return None

        # 按SKU和月份分析利润
        monthly_profit = self.df.groupby(['SKU编码', '商品名称', '年月']).agg({
            '销售金额': 'sum',
            '利润': 'sum',
            '销售个数': 'sum'
        }).round(2)

        # 计算利润率
        monthly_profit['利润率'] = (monthly_profit['利润'] / monthly_profit['销售金额'] * 100).round(2)

        # 重置索引以便于分析
        monthly_profit = monthly_profit.reset_index()

        # 找出利润差的SKU（利润率低于阈值）
        low_profit_threshold = self.report_config.get('low_profit_threshold', 0.05) * 100
        low_profit_skus = monthly_profit[
            (monthly_profit['利润率'] < low_profit_threshold) &
            (monthly_profit['销售金额'] > 0)
            ]

        # 月份对比分析
        months = sorted(monthly_profit['年月'].unique())
        if len(months) >= 2:
            # 计算月度变化
            profit_comparison = []

            for sku in monthly_profit['SKU编码'].unique():
                sku_data = monthly_profit[monthly_profit['SKU编码'] == sku]
                if len(sku_data) >= 2:
                    # 按月份排序
                    sku_data = sku_data.sort_values('年月')

                    # 计算月度变化
                    current_month = sku_data.iloc[-1]
                    previous_month = sku_data.iloc[-2] if len(sku_data) > 1 else None

                    if previous_month is not None:
                        profit_change = current_month['利润'] - previous_month['利润']
                        profit_change_pct = (profit_change / previous_month['利润'] * 100) if previous_month[
                                                                                                  '利润'] != 0 else 0

                        sales_change = current_month['销售金额'] - previous_month['销售金额']
                        sales_change_pct = (sales_change / previous_month['销售金额'] * 100) if previous_month[
                                                                                                    '销售金额'] != 0 else 0

                        profit_comparison.append({
                            'SKU编码': sku,
                            '商品名称': current_month['商品名称'],
                            '当前月份': current_month['年月'],
                            '上月月份': previous_month['年月'],
                            '当前利润': current_month['利润'],
                            '上月利润': previous_month['利润'],
                            '利润变化': profit_change,
                            '利润变化率%': round(profit_change_pct, 2),
                            '当前销售额': current_month['销售金额'],
                            '上月销售额': previous_month['销售金额'],
                            '销售额变化': sales_change,
                            '销售额变化率%': round(sales_change_pct, 2)
                        })

            profit_comparison_df = pd.DataFrame(profit_comparison)

            # 找出利润下降明显的SKU
            significant_drop = profit_comparison_df[
                (profit_comparison_df['利润变化率%'] < -30) |
                (profit_comparison_df['利润'] < 0)
                ].sort_values('利润变化率%')

        else:
            profit_comparison_df = pd.DataFrame()
            significant_drop = pd.DataFrame()

        results = {
            'monthly_profit': monthly_profit,
            'low_profit_skus': low_profit_skus,
            'profit_comparison': profit_comparison_df,
            'significant_drop': significant_drop
        }

        self.analysis_results['profit_analysis'] = results
        return results

    def run_monthly_comparison(self):
        """
        5. 月度销售看板及环比分析
        """
        print("📈 执行月度对比分析...")

        if '年月' not in self.df.columns:
            print("❌ 无法进行月度对比分析")
            return None

        # 月度汇总数据
        monthly_summary = self.df.groupby('年月').agg({
            '销售金额': 'sum',
            '利润': 'sum',
            '销售个数': 'sum',
            'SKU编码': 'nunique',
            '订单数': 'sum' if '订单数' in self.df.columns else ('销售金额', 'count')
        }).round(2)

        # 计算平均订单金额等指标
        if '订单数' in monthly_summary.columns:
            monthly_summary['平均订单金额'] = (monthly_summary['销售金额'] / monthly_summary['订单数']).round(2)
        monthly_summary['平均利润率'] = (monthly_summary['利润'] / monthly_summary['销售金额'] * 100).round(2)

        # 计算环比增长率
        monthly_summary = monthly_summary.sort_index()
        for column in ['销售金额', '利润', '销售个数']:
            if column in monthly_summary.columns:
                monthly_summary[f'{column}_环比%'] = monthly_summary[column].pct_change() * 100
                monthly_summary[f'{column}_环比%'] = monthly_summary[f'{column}_环比%'].round(2)

        # 识别下降明显的SKU
        sales_drop_threshold = self.report_config.get('sales_drop_threshold', 0.3) * 100

        # 按SKU分析月度销售变化
        sku_monthly = self.df.groupby(['SKU编码', '商品名称', '年月']).agg({
            '销售金额': 'sum',
            '销售个数': 'sum'
        }).reset_index()

        # 计算SKU的月度环比
        sku_comparison = []
        for sku in sku_monthly['SKU编码'].unique():
            sku_data = sku_monthly[sku_monthly['SKU编码'] == sku].sort_values('年月')
            if len(sku_data) >= 2:
                current = sku_data.iloc[-1]
                previous = sku_data.iloc[-2]

                sales_change_pct = ((current['销售金额'] - previous['销售金额']) / previous['销售金额'] * 100) if \
                previous['销售金额'] > 0 else -100

                if sales_change_pct <= -sales_drop_threshold:
                    sku_comparison.append({
                        'SKU编码': sku,
                        '商品名称': current['商品名称'],
                        '当前月份': current['年月'],
                        '当前销售额': current['销售金额'],
                        '上月销售额': previous['销售金额'],
                        '销售额下降%': round(sales_change_pct, 2),
                        '下降程度': '严重' if sales_change_pct <= -50 else '明显'
                    })

        significant_drop_skus = pd.DataFrame(sku_comparison).sort_values('销售额下降%')

        results = {
            'monthly_summary': monthly_summary,
            'significant_drop_skus': significant_drop_skus,
            'sales_drop_threshold': sales_drop_threshold
        }

        self.analysis_results['monthly_comparison'] = results
        return results

    def run_visualization(self):
        """
        执行可视化分析
        """
        try:
            print("🎨 执行可视化分析...")

            # 创建销售看板图表
            self.create_sales_dashboard()

            print("✅ 可视化分析完成")
            return True
        except Exception as e:
            print(f"⚠️  可视化分析失败: {e}")
            return False

    def create_sales_dashboard(self):
        """
        创建销售看板图表
        """
        try:
            # 月度趋势图
            if 'monthly_comparison' in self.analysis_results:
                monthly_data = self.analysis_results['monthly_comparison']['monthly_summary']

                fig, axes = plt.subplots(2, 2, figsize=(15, 12))
                fig.suptitle(f'销售看板 - {self.analysis_date}', fontsize=16)

                # 销售额趋势
                if '销售金额' in monthly_data.columns:
                    axes[0, 0].plot(monthly_data.index, monthly_data['销售金额'], marker='o', linewidth=2)
                    axes[0, 0].set_title('月度销售额趋势')
                    axes[0, 0].set_ylabel('销售额')
                    axes[0, 0].tick_params(axis='x', rotation=45)

                # 利润趋势
                if '利润' in monthly_data.columns:
                    axes[0, 1].plot(monthly_data.index, monthly_data['利润'], marker='s', color='green', linewidth=2)
                    axes[0, 1].set_title('月度利润趋势')
                    axes[0, 1].set_ylabel('利润')
                    axes[0, 1].tick_params(axis='x', rotation=45)

                # 小分类销售额分布
                if 'category_analysis' in self.analysis_results:
                    category_data = self.analysis_results['category_analysis'].head(10)
                    axes[1, 0].barh(category_data.index, category_data['销售金额'])
                    axes[1, 0].set_title('小分类销售额TOP10')
                    axes[1, 0].set_xlabel('销售额')

                # 环比变化
                if '销售金额_环比%' in monthly_data.columns:
                    colors = ['red' if x < 0 else 'green' for x in monthly_data['销售金额_环比%']]
                    axes[1, 1].bar(monthly_data.index, monthly_data['销售金额_环比%'], color=colors)
                    axes[1, 1].set_title('销售额环比变化%')
                    axes[1, 1].set_ylabel('环比%')
                    axes[1, 1].tick_params(axis='x', rotation=45)
                    axes[1, 1].axhline(y=0, color='black', linestyle='-', alpha=0.3)

                plt.tight_layout()

                # 保存图表到内存
                buf = BytesIO()
                plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                buf.seek(0)
                self.chart_images['sales_dashboard'] = buf
                plt.close()

        except Exception as e:
            print(f"创建销售看板失败: {e}")

    def run_all_analysis(self):
        """
        执行所有分析模块
        """
        print("🚀 开始执行销售数据分析...")

        if not self.check_required_columns():
            print("❌ 缺少必要字段，无法进行分析")
            return None

        # 定义分析模块执行顺序
        analysis_modules = [
            self.run_category_analysis,
            self.run_sales_plan_analysis,
            self.run_unsold_analysis,
            self.run_profit_analysis,
            self.run_monthly_comparison,
        ]

        # 执行分析模块
        for module in analysis_modules:
            try:
                module()
                print(f"   ✅ {module.__name__} 完成")
            except Exception as e:
                print(f"⚠️  {module.__name__} 执行失败: {e}")

        # 执行可视化分析
        self.run_visualization()

        print("✅ 所有分析模块执行完成！")
        return self.analysis_results

    def generate_report(self):
        """
        生成分析报告
        """
        print("\n" + "=" * 80)
        print(f"📈 销售数据分析报告 - {self.analysis_date}")
        print("=" * 80)

        # 1. 小分类分析
        if 'category_analysis' in self.analysis_results:
            print("\n1. 🏷️ 小分类收入和利润分析:")
            category_data = self.analysis_results['category_analysis']
            print(category_data[['销售金额', '利润', '利润率', '改进建议']].to_string())

        # 2. 销售计划完成情况
        if 'sales_plan_analysis' in self.analysis_results:
            results = self.analysis_results['sales_plan_analysis']
            if 'category_plan' in results:
                print(f"\n2. 📊 销售计划完成情况:")
                print(results['category_plan'][['销售金额', '销售计划', '完成率']].to_string())

                if 'focus_skus' in results and len(results['focus_skus']) > 0:
                    print(f"\n   需要重点关注的SKU (完成率<50%):")
                    print(results['focus_skus'][['SKU编码', '商品名称', '完成率']].head(10).to_string())

        # 3. 滞销产品分析
        if 'unsold_analysis' in self.analysis_results:
            results = self.analysis_results['unsold_analysis']
            print(f"\n3. 📦 滞销产品分析 (最近{len(results['analysis_period'])}个月无销售):")
            print(f"   总SKU: {results['total_skus']}, 有销售: {results['sold_skus']}, 滞销: {results['unsold_skus']}")
            if 'unsold_products' in results and len(results['unsold_products']) > 0:
                print(results['unsold_products'][['SKU编码', '商品名称', '滞销月数', '在库金额', '维护建议']].head(
                    15).to_string())

        # 4. 利润分析
        if 'profit_analysis' in self.analysis_results:
            results = self.analysis_results['profit_analysis']
            if 'significant_drop' in results and len(results['significant_drop']) > 0:
                print(f"\n4. 💰 利润下降明显的SKU:")
                print(results['significant_drop'][['SKU编码', '商品名称', '利润变化率%', '当前利润']].head(
                    10).to_string())

        # 5. 月度对比
        if 'monthly_comparison' in self.analysis_results:
            results = self.analysis_results['monthly_comparison']
            print(f"\n5. 📈 月度对比分析:")
            if 'monthly_summary' in results:
                print(results['monthly_summary'].to_string())

            if 'significant_drop_skus' in results and len(results['significant_drop_skus']) > 0:
                print(f"\n   销售下降明显的SKU (下降>{results['sales_drop_threshold']}%):")
                print(results['significant_drop_skus'][['SKU编码', '商品名称', '销售额下降%', '下降程度']].head(
                    10).to_string())

        return self.analysis_results

    def export_to_excel(self):
        """
        导出分析结果到Excel
        """
        if not self.analysis_results:
            print("没有分析结果可导出")
            return None

        # 确保reports目录存在
        reports_dir = "reports"
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
            print(f"创建目录: {reports_dir}")

        root = tk.Tk()
        root.withdraw()

        # 修改这一行，使用绝对路径
        default_filename = os.path.join(reports_dir, f"销售分析报告_{self.analysis_date}.xlsx")

        output_path = filedialog.asksaveasfilename(
            title="保存分析报告",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialdir=reports_dir,  # 设置初始目录为reports_dir
            initialfile=os.path.basename(default_filename)  # 只提供文件名，不包含路径
        )

        root.destroy()

        if not output_path:
            print("未选择保存位置")
            return None

        try:
            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                workbook = writer.book

                # 1. 报告摘要
                summary_sheet = workbook.add_worksheet('报告摘要')
                summary_sheet.set_column('A:A', 25)
                summary_sheet.set_column('B:B', 20)

                title_format = workbook.add_format({
                    'bold': True, 'font_size': 16, 'align': 'center', 'valign': 'vcenter'
                })
                summary_sheet.merge_range('A1:B1', f'销售分析报告 - {self.analysis_date}', title_format)


                # 3. 小分类分析
                if 'category_analysis' in self.analysis_results:
                    self.analysis_results['category_analysis'].to_excel(
                        writer, sheet_name='小分类分析')

                # 4. 销售计划分析
                if 'sales_plan_analysis' in self.analysis_results:
                    results = self.analysis_results['sales_plan_analysis']
                    if 'category_plan' in results:
                        results['category_plan'].to_excel(writer, sheet_name='销售计划完成情况', startrow=0)
                    if 'focus_skus' in results:
                        results['focus_skus'].to_excel(writer, sheet_name='需关注SKU')

                # 5. 滞销产品分析
                if 'unsold_analysis' in self.analysis_results:
                    results = self.analysis_results['unsold_analysis']
                    if 'unsold_products' in results:
                        results['unsold_products'].to_excel(writer, sheet_name='滞销产品分析')

                # 6. 利润分析
                if 'profit_analysis' in self.analysis_results:
                    results = self.analysis_results['profit_analysis']
                    if 'monthly_profit' in results:
                        results['monthly_profit'].to_excel(writer, sheet_name='月度利润分析')
                    if 'significant_drop' in results:
                        results['significant_drop'].to_excel(writer, sheet_name='利润下降SKU')

                # 7. 月度对比
                if 'monthly_comparison' in self.analysis_results:
                    results = self.analysis_results['monthly_comparison']
                    if 'monthly_summary' in results:
                        results['monthly_summary'].to_excel(writer, sheet_name='月度对比')
                    if 'significant_drop_skus' in results:
                        results['significant_drop_skus'].to_excel(writer, sheet_name='销售下降SKU')

                # 8. 销售看板
                if 'sales_dashboard' in self.chart_images:
                    dashboard_sheet = workbook.add_worksheet('销售看板')
                    dashboard_sheet.insert_image('A1', 'sales_dashboard',
                                                 {'image_data': self.chart_images['sales_dashboard']})

            print(f"📁 分析结果已导出到: {output_path}")
            return output_path

        except Exception as e:
            print(f"❌ 导出失败: {e}")
            return None


def main():
    """
    主函数
    """
    print("=" * 60)
    print("📈 销售数据分析工具")
    print("=" * 60)

    # 创建分析器实例
    analyzer = MonthlySalesAnalyzer()

    # 选择文件
    if not analyzer.select_file():
        return

    # 加载数据
    if not analyzer.load_data():
        return

    # 数据预处理
    analyzer.preprocess_data()

    # 执行所有分析
    analyzer.run_all_analysis()

    # 生成报告
    analyzer.generate_report()

    # 导出到Excel（只调用一次）
    output_path = analyzer.export_to_excel()

    print("\n🎉 分析完成！")

    # 询问是否打开结果文件
    if output_path:
        root = tk.Tk()
        root.withdraw()

        if messagebox.askyesno("分析完成", "分析已完成！是否打开结果文件？"):
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(output_path)
                elif os.name == 'posix':  # macOS 或 Linux
                    if sys.platform == 'darwin':  # macOS
                        os.system(f'open "{output_path}"')
                    else:  # Linux
                        os.system(f'xdg-open "{output_path}"')
                print(f"📂 已打开结果文件: {os.path.basename(output_path)}")
            except Exception as e:
                print(f"⚠️ 无法自动打开文件: {e}")
                print(f"请手动打开: {output_path}")

        root.destroy()
    else:
        print("❌ 未生成结果文件")


if __name__ == "__main__":
    main()
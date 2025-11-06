import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')


class EnhancedSalesAnalyzer:
    """增强版销售分析器 - 提供深度业务洞察"""

    def __init__(self, base_analyzer):
        self.analyzer = base_analyzer
        self.df = base_analyzer.df
        self.analysis_results = base_analyzer.analysis_results

    def run_deep_analysis(self):
        """执行深度分析"""
        print("🔍 执行深度业务分析...")

        results = {}

        # 1. 销售健康度评估
        results['health_assessment'] = self.assess_business_health()

        # 2. 智能业务建议
        results['business_recommendations'] = self.generate_business_recommendations()

        # 3. 异常检测
        results['anomalies'] = self.detect_anomalies()

        # 4. 趋势预测
        results['trends'] = self.analyze_trends()

        # 5. 竞争分析
        results['competitive_analysis'] = self.competitive_analysis()

        # 合并到原有结果
        self.analyzer.analysis_results.update(results)
        return results

    def assess_business_health(self):
        """业务健康度评估"""
        health_scores = {}

        # 销售额健康度
        if 'monthly_comparison' in self.analysis_results:
            monthly_data = self.analysis_results['monthly_comparison']['monthly_summary']
            if '销售金额_环比%' in monthly_data.columns:
                recent_growth = monthly_data['销售金额_环比%'].iloc[-1] if len(monthly_data) > 1 else 0
                health_scores['sales_growth'] = self._calculate_growth_score(recent_growth)

        # 利润率健康度
        if 'profit_analysis' in self.analysis_results:
            profit_data = self.analysis_results['profit_analysis']
            if 'low_profit_skus' in profit_data:
                low_profit_ratio = len(profit_data['low_profit_skus']) / len(self.df['SKU编码'].unique())
                health_scores['profit_health'] = max(0, 100 - (low_profit_ratio * 100))

        # 库存健康度
        if 'unsold_analysis' in self.analysis_results:
            unsold_data = self.analysis_results['unsold_analysis']
            unsold_ratio = unsold_data['unsold_skus'] / unsold_data['total_skus']
            health_scores['inventory_health'] = max(0, 100 - (unsold_ratio * 100))

        # 总体健康度
        if health_scores:
            health_scores['overall'] = np.mean(list(health_scores.values()))

        return health_scores

    def _calculate_growth_score(self, growth_rate):
        """计算增长得分"""
        if growth_rate > 20:
            return 100
        elif growth_rate > 10:
            return 80
        elif growth_rate > 0:
            return 60
        elif growth_rate > -10:
            return 40
        else:
            return 20

    def generate_business_recommendations(self):
        """生成智能业务建议"""
        recommendations = []

        # 基于分类分析的建议
        if 'category_analysis' in self.analysis_results:
            cat_data = self.analysis_results['category_analysis']
            for category, row in cat_data.iterrows():
                if row.get('利润率', 0) < 5:
                    recommendations.append({
                        'type': '利润优化',
                        'priority': '高',
                        'category': category,
                        'recommendation': f"{category}利润率过低({row['利润率']:.1f}%)，建议检查成本结构或调整定价",
                        'impact': '高',
                        'effort': '中'
                    })

                if row.get('销售金额', 0) > cat_data['销售金额'].quantile(0.8):
                    recommendations.append({
                        'type': '资源分配',
                        'priority': '中',
                        'category': category,
                        'recommendation': f"{category}是畅销品类，可考虑增加营销投入",
                        'impact': '中',
                        'effort': '低'
                    })

        # 基于滞销产品的建议
        if 'unsold_analysis' in self.analysis_results:
            unsold_data = self.analysis_results['unsold_analysis']['unsold_products']
            high_value_unsold = unsold_data[unsold_data['在库金额'] > 5000]
            if len(high_value_unsold) > 0:
                recommendations.append({
                    'type': '库存优化',
                    'priority': '高',
                    'category': '库存',
                    'recommendation': f"发现{len(high_value_unsold)}个高价值滞销SKU，总库存金额{high_value_unsold['在库金额'].sum():.0f}元，建议立即处理",
                    'impact': '高',
                    'effort': '高'
                })

        # 基于销售趋势的建议
        if 'monthly_comparison' in self.analysis_results:
            monthly_data = self.analysis_results['monthly_comparison']['monthly_summary']
            if len(monthly_data) > 1:
                recent_growth = monthly_data['销售金额_环比%'].iloc[
                    -1] if '销售金额_环比%' in monthly_data.columns else 0
                if recent_growth < -10:
                    recommendations.append({
                        'type': '销售预警',
                        'priority': '高',
                        'category': '整体',
                        'recommendation': f"近期销售额环比下降{abs(recent_growth):.1f}%，需要关注市场变化和竞争情况",
                        'impact': '高',
                        'effort': '中'
                    })

        return pd.DataFrame(recommendations)

    def detect_anomalies(self):
        """异常检测"""
        anomalies = []

        # 价格异常检测
        if '销售金额' in self.df.columns and '销售个数' in self.df.columns:
            self.df['单价'] = self.df['销售金额'] / self.df['销售个数']
            price_stats = self.df['单价'].describe()
            price_outliers = self.df[
                (self.df['单价'] > price_stats['75%'] + 1.5 * (price_stats['75%'] - price_stats['25%'])) |
                (self.df['单价'] < price_stats['25%'] - 1.5 * (price_stats['75%'] - price_stats['25%']))
                ]

            if len(price_outliers) > 0:
                anomalies.append({
                    'type': '价格异常',
                    'count': len(price_outliers),
                    'description': f'发现{len(price_outliers)}个价格异常交易',
                    'details': price_outliers[['SKU编码', '商品名称', '单价']].to_dict('records')
                })

        # 销售数量异常
        if '销售个数' in self.df.columns:
            quantity_stats = self.df['销售个数'].describe()
            quantity_outliers = self.df[
                self.df['销售个数'] > quantity_stats['75%'] + 1.5 * (quantity_stats['75%'] - quantity_stats['25%'])]

            if len(quantity_outliers) > 0:
                anomalies.append({
                    'type': '销量异常',
                    'count': len(quantity_outliers),
                    'description': f'发现{len(quantity_outliers)}个销量异常交易',
                    'details': quantity_outliers[['SKU编码', '商品名称', '销售个数']].to_dict('records')
                })

        return anomalies

    def analyze_trends(self):
        """趋势分析"""
        trends = {}

        if 'monthly_comparison' in self.analysis_results:
            monthly_data = self.analysis_results['monthly_comparison']['monthly_summary']

            # 销售趋势
            if '销售金额' in monthly_data.columns and len(monthly_data) >= 3:
                sales_trend = self._calculate_trend(monthly_data['销售金额'])
                trends['sales_trend'] = {
                    'direction': '上升' if sales_trend > 0 else '下降',
                    'strength': abs(sales_trend),
                    'description': f'销售额呈现{"上升" if sales_trend > 0 else "下降"}趋势'
                }

            # 利润趋势
            if '利润' in monthly_data.columns and len(monthly_data) >= 3:
                profit_trend = self._calculate_trend(monthly_data['利润'])
                trends['profit_trend'] = {
                    'direction': '上升' if profit_trend > 0 else '下降',
                    'strength': abs(profit_trend),
                    'description': f'利润呈现{"上升" if profit_trend > 0 else "下降"}趋势'
                }

        return trends

    def _calculate_trend(self, series):
        """计算时间序列趋势"""
        if len(series) < 2:
            return 0

        x = np.arange(len(series))
        y = series.values
        slope = np.polyfit(x, y, 1)[0]
        return slope / np.mean(y) if np.mean(y) != 0 else 0

    def competitive_analysis(self):
        """竞争分析（基于内部数据）"""
        analysis = {}

        # 产品集中度分析
        if 'product_analysis' in self.analysis_results:
            product_data = self.analysis_results['product_analysis']['all_products']
            if '销售金额' in product_data.columns:
                total_sales = product_data['销售金额'].sum()
                top_10_sales = product_data.nlargest(10, '销售金额')['销售金额'].sum()
                concentration_ratio = top_10_sales / total_sales if total_sales > 0 else 0

                analysis['product_concentration'] = {
                    'ratio': concentration_ratio,
                    'interpretation': '高度集中' if concentration_ratio > 0.8 else
                    '中度集中' if concentration_ratio > 0.5 else '分散',
                    'recommendation': '产品集中度高，依赖少数畅销产品' if concentration_ratio > 0.8 else
                    '产品结构相对均衡'
                }

        # 分类均衡性分析
        if 'category_analysis' in self.analysis_results:
            cat_data = self.analysis_results['category_analysis']
            if '销售金额' in cat_data.columns:
                gini_coefficient = self._calculate_gini(cat_data['销售金额'])
                analysis['category_balance'] = {
                    'gini': gini_coefficient,
                    'interpretation': '高度不均衡' if gini_coefficient > 0.6 else
                    '中度不均衡' if gini_coefficient > 0.4 else '相对均衡',
                    'recommendation': '分类销售高度不均衡，需要优化产品组合' if gini_coefficient > 0.6 else
                    '分类销售相对均衡'
                }

        return analysis

    def _calculate_gini(self, series):
        """计算基尼系数"""
        sorted_series = np.sort(series)
        n = len(sorted_series)
        index = np.arange(1, n + 1)
        return (np.sum((2 * index - n - 1) * sorted_series)) / (n * np.sum(sorted_series))


# 修改原有的MonthlySalesAnalyzer，添加深度分析
def enhance_analyzer(analyzer):
    """为分析器添加深度分析功能"""
    enhanced = EnhancedSalesAnalyzer(analyzer)

    # 重写run_all_analysis方法
    original_run_all = analyzer.run_all_analysis

    def enhanced_run_all_analysis():
        results = original_run_all()
        if results:
            enhanced.run_deep_analysis()
        return analyzer.analysis_results

    analyzer.run_all_analysis = enhanced_run_all_analysis
    return analyzer
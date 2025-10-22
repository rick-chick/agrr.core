#!/usr/bin/env python3
"""
簡易予測精度検証スクリプト
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def load_predictions(file_path):
    """予測結果を読み込み"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    predictions = data['predictions']
    df = pd.DataFrame(predictions)
    df['date'] = pd.to_datetime(df['date'])
    return df

def analyze_predictions(df):
    """予測結果の統計分析"""
    print("=== 予測結果の統計分析 ===")
    print(f"予測期間: {df['date'].min()} から {df['date'].max()}")
    print(f"予測日数: {len(df)} 日")
    print()
    
    # 基本統計
    metrics = ['temperature', 'temperature_max', 'temperature_min']
    for metric in metrics:
        print(f"--- {metric} ---")
        print(f"  平均: {df[metric].mean():.2f}°C")
        print(f"  最小: {df[metric].min():.2f}°C")
        print(f"  最大: {df[metric].max():.2f}°C")
        print(f"  標準偏差: {df[metric].std():.2f}°C")
        print()
    
    # 季節性の確認
    df['month'] = df['date'].dt.month
    monthly_stats = df.groupby('month')[metrics].agg(['mean', 'std']).round(2)
    print("=== 月別統計 ===")
    print(monthly_stats)
    print()
    
    # 温度の妥当性チェック
    print("=== 温度の妥当性チェック ===")
    invalid_temp = df[df['temperature_max'] <= df['temperature_min']]
    if len(invalid_temp) > 0:
        print(f"⚠️  最高気温 ≤ 最低気温の日: {len(invalid_temp)} 日")
        print(invalid_temp[['date', 'temperature_max', 'temperature_min']].head())
    else:
        print("✅ 温度の関係性は正常")
    
    # 極端な値のチェック
    extreme_high = df[df['temperature_max'] > 50]
    extreme_low = df[df['temperature_min'] < -20]
    if len(extreme_high) > 0:
        print(f"⚠️  極端に高い温度 (>50°C): {len(extreme_high)} 日")
    if len(extreme_low) > 0:
        print(f"⚠️  極端に低い温度 (<-20°C): {len(extreme_low)} 日")
    
    if len(extreme_high) == 0 and len(extreme_low) == 0:
        print("✅ 温度範囲は妥当")
    
    return monthly_stats

def create_simple_plots(df):
    """簡単な可視化"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('予測結果の可視化分析', fontsize=16, fontweight='bold')
    
    # 1. 時系列プロット
    ax1 = axes[0, 0]
    dates = df['date'].values
    ax1.plot(dates, df['temperature'].values, label='平均気温', linewidth=2)
    ax1.plot(dates, df['temperature_max'].values, label='最高気温', alpha=0.7)
    ax1.plot(dates, df['temperature_min'].values, label='最低気温', alpha=0.7)
    ax1.fill_between(dates, df['temperature_min'].values, df['temperature_max'].values, alpha=0.2)
    ax1.set_title('気温予測の時系列')
    ax1.set_ylabel('気温 (°C)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. 月別平均気温
    ax2 = axes[0, 1]
    df['month'] = df['date'].dt.month
    monthly_temp = df.groupby('month')['temperature'].mean()
    months = ['1月', '2月', '3月', '4月', '5月', '6月', 
              '7月', '8月', '9月', '10月', '11月', '12月']
    ax2.plot(range(1, 13), monthly_temp.values, marker='o', linewidth=2, markersize=6)
    ax2.set_title('月別平均気温')
    ax2.set_xlabel('月')
    ax2.set_ylabel('平均気温 (°C)')
    ax2.set_xticks(range(1, 13))
    ax2.set_xticklabels(months, rotation=45)
    ax2.grid(True, alpha=0.3)
    
    # 3. 温度分布
    ax3 = axes[1, 0]
    ax3.hist(df['temperature'].values, bins=30, alpha=0.7, label='平均気温', density=True)
    ax3.hist(df['temperature_max'].values, bins=30, alpha=0.7, label='最高気温', density=True)
    ax3.hist(df['temperature_min'].values, bins=30, alpha=0.7, label='最低気温', density=True)
    ax3.set_title('気温分布')
    ax3.set_xlabel('気温 (°C)')
    ax3.set_ylabel('密度')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. 日別変動
    ax4 = axes[1, 1]
    daily_range = df['temperature_max'] - df['temperature_min']
    ax4.plot(dates, daily_range.values, linewidth=1, alpha=0.8)
    ax4.set_title('日較差（最高気温 - 最低気温）')
    ax4.set_ylabel('日較差 (°C)')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('/tmp/prediction_analysis.png', dpi=300, bbox_inches='tight')
    print("📊 グラフを保存しました: /tmp/prediction_analysis.png")
    
    return fig

def main():
    """メイン実行"""
    print("🔍 予測精度検証を開始...")
    
    # 予測結果の読み込み
    df = load_predictions('/tmp/prediction_vectorized.json')
    
    # 統計分析
    monthly_stats = analyze_predictions(df)
    
    # 可視化
    print("📊 可視化を生成中...")
    create_simple_plots(df)
    
    print("✅ 分析完了！")
    print("📁 結果ファイル: /tmp/prediction_analysis.png")

if __name__ == "__main__":
    main()

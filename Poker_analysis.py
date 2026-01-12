import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, Tuple, List
import re

plt.rcParams['figure.figsize'] = (16, 10)
plt.rcParams['font.size'] = 10


class CompletePokerAnalysis:
    
    def __init__(self, df_hands: pd.DataFrame, df_players: pd.DataFrame):
        self.df_hands = df_hands.copy()
        self.df_players = df_players.copy()
        self._prepare_data()
    
    def _prepare_data(self):

        if 'big_blind' not in self.df_players.columns:
            self.df_players = self.df_players.merge(
                self.df_hands[['hand_id', 'big_blind']],
                on='hand_id',
                how='left'
            )
        
        self.df_players['profit_bb'] = (
            self.df_players['profit'] / self.df_players['big_blind']
        )
        
        self.df_players['outcome'] = 'breakeven'
        self.df_players.loc[self.df_players['profit'] > 0, 'outcome'] = 'win'
        self.df_players.loc[self.df_players['profit'] < 0, 'outcome'] = 'loss'
        
        self.df_hands['went_to_flop'] = self.df_hands['flop'].notna()
        self.df_hands['went_to_turn'] = self.df_hands['turn'].notna()
        self.df_hands['went_to_river'] = self.df_hands['river'].notna()
        
        self.df_hands['final_street'] = 'preflop'
        self.df_hands.loc[self.df_hands['went_to_flop'], 'final_street'] = 'flop'
        self.df_hands.loc[self.df_hands['went_to_turn'], 'final_street'] = 'turn'
        self.df_hands.loc[self.df_hands['went_to_river'], 'final_street'] = 'river'
        
        self.df_players = self.df_players.merge(
            self.df_hands[['hand_id', 'final_street']],
            on='hand_id',
            how='left'
        )
    
    
    def analyze_wins_vs_losses(self) -> Dict:

        wins = self.df_players[self.df_players['outcome'] == 'win']
        losses = self.df_players[self.df_players['outcome'] == 'loss']
        
        return {
            'wins': {
                'count': len(wins),
                'frequency': len(wins) / len(self.df_players) * 100,
                'mean': wins['profit_bb'].mean(),
                'median': wins['profit_bb'].median(),
                'std': wins['profit_bb'].std(),
                'total': wins['profit_bb'].sum(),
                'q75': wins['profit_bb'].quantile(0.75),
                'q95': wins['profit_bb'].quantile(0.95)
            },
            'losses': {
                'count': len(losses),
                'frequency': len(losses) / len(self.df_players) * 100,
                'mean': losses['profit_bb'].mean(),
                'median': losses['profit_bb'].median(),
                'std': losses['profit_bb'].std(),
                'total': losses['profit_bb'].sum(),
                'q25': losses['profit_bb'].quantile(0.25),
                'q05': losses['profit_bb'].quantile(0.05)
            },
            'win_loss_ratio': len(wins) / len(losses) if len(losses) > 0 else np.inf,
            'avg_win_loss_ratio': wins['profit_bb'].mean() / abs(losses['profit_bb'].mean()) if len(losses) > 0 else np.inf
        }
    
    def print_wins_losses_report(self):

        stats = self.analyze_wins_vs_losses()
        
        print("="*80)
        print(" "*20 + "1. ANÁLISE DE GANHOS E PERDAS (RISCO)")
        print("="*80)
        print()
        
        print("GANHOS (profit > 0):")
        print(f"  Frequência: {stats['wins']['frequency']:.1f}% das mãos ({stats['wins']['count']:,})")
        print(f"  Ganho médio: +{stats['wins']['mean']:.2f} BB/mão")
        print(f"  Ganho mediano: +{stats['wins']['median']:.2f} BB")
        print(f"  Desvio padrão: {stats['wins']['std']:.2f} BB")
        print(f"  Total acumulado: +{stats['wins']['total']:,.0f} BB")
        print(f"  75% dos ganhos até: +{stats['wins']['q75']:.2f} BB")
        print(f"  95% dos ganhos até: +{stats['wins']['q95']:.2f} BB")
        print()
        
        print("PERDAS (profit < 0):")
        print(f"  Frequência: {stats['losses']['frequency']:.1f}% das mãos ({stats['losses']['count']:,})")
        print(f"  Perda média: {stats['losses']['mean']:.2f} BB/mão")
        print(f"  Perda mediana: {stats['losses']['median']:.2f} BB")
        print(f"  Desvio padrão: {stats['losses']['std']:.2f} BB")
        print(f"  Total acumulado: {stats['losses']['total']:,.0f} BB")
        print(f"  25% das perdas acima de: {stats['losses']['q25']:.2f} BB")
        print(f"  5% piores perdas (cauda): {stats['losses']['q05']:.2f} BB")
        print()
        
        print("PERFIL DE RISCO:")
        print(f"  Win/Loss Ratio (frequência): {stats['win_loss_ratio']:.2f}")
        print(f"  Avg Win/Loss Ratio (tamanho): {stats['avg_win_loss_ratio']:.2f}")
        
        if stats['avg_win_loss_ratio'] > 1:
            print(f"   Ganhos médios são {stats['avg_win_loss_ratio']:.1f}x maiores que perdas médias")
        else:
            print(f"   Perdas médias são maiores que ganhos médios")
        print()
    
    def plot_wins_losses_distribution(self, save_path: str = None):
        wins = self.df_players[self.df_players['outcome'] == 'win']['profit_bb']
        losses = self.df_players[self.df_players['outcome'] == 'loss']['profit_bb']
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        axes[0, 0].hist(wins, bins=50, color='green', alpha=0.7, edgecolor='black')
        axes[0, 0].axvline(wins.mean(), color='darkgreen', linestyle='--', linewidth=2, label=f'Média: {wins.mean():.2f}')
        axes[0, 0].axvline(wins.median(), color='lime', linestyle='--', linewidth=2, label=f'Mediana: {wins.median():.2f}')
        axes[0, 0].set_xlabel('Ganho (BB)', fontweight='bold')
        axes[0, 0].set_ylabel('Frequência', fontweight='bold')
        axes[0, 0].set_title('Distribuição de GANHOS', fontweight='bold', fontsize=14)
        axes[0, 0].legend()
        axes[0, 0].grid(alpha=0.3)
        
        axes[0, 1].hist(losses, bins=50, color='red', alpha=0.7, edgecolor='black')
        axes[0, 1].axvline(losses.mean(), color='darkred', linestyle='--', linewidth=2, label=f'Média: {losses.mean():.2f}')
        axes[0, 1].axvline(losses.median(), color='orange', linestyle='--', linewidth=2, label=f'Mediana: {losses.median():.2f}')
        axes[0, 1].set_xlabel('Perda (BB)', fontweight='bold')
        axes[0, 1].set_ylabel('Frequência', fontweight='bold')
        axes[0, 1].set_title('Distribuição de PERDAS', fontweight='bold', fontsize=14)
        axes[0, 1].legend()
        axes[0, 1].grid(alpha=0.3)
        
        data_to_plot = [wins, losses]
        bp = axes[1, 0].boxplot(data_to_plot, labels=['Ganhos', 'Perdas'], 
                               patch_artist=True, showmeans=True, widths=0.6)
        bp['boxes'][0].set_facecolor('lightgreen')
        bp['boxes'][1].set_facecolor('lightcoral')
        axes[1, 0].axhline(y=0, color='black', linestyle='--', linewidth=1)
        axes[1, 0].set_ylabel('Profit (BB)', fontweight='bold')
        axes[1, 0].set_title('Comparação: Ganhos vs Perdas', fontweight='bold', fontsize=14)
        axes[1, 0].grid(alpha=0.3)
        
        outcomes = self.df_players['outcome'].value_counts()
        colors_map = {'win': 'green', 'loss': 'red', 'breakeven': 'gray'}
        colors = [colors_map.get(x, 'gray') for x in outcomes.index]
        
        axes[1, 1].bar(outcomes.index, outcomes.values, color=colors, alpha=0.7, edgecolor='black')
        axes[1, 1].set_ylabel('Frequência', fontweight='bold')
        axes[1, 1].set_title('Frequência de Resultados', fontweight='bold', fontsize=14)
        axes[1, 1].grid(alpha=0.3)
        
        for i, (outcome, count) in enumerate(outcomes.items()):
            pct = count / len(self.df_players) * 100
            axes[1, 1].text(i, count + 500, f'{pct:.1f}%', ha='center', fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()
    
    
    def analyze_wins_losses_by_position(self) -> pd.DataFrame:

        positions = ['SB', 'BB', 'UTG', 'MP', 'CO', 'BTN']
        results = []
        
        for pos in positions:
            pos_data = self.df_players[self.df_players['position'] == pos]
            wins = pos_data[pos_data['outcome'] == 'win']
            losses = pos_data[pos_data['outcome'] == 'loss']
            
            if len(pos_data) == 0:
                continue
            
            results.append({
                'position': pos,
                'total_hands': len(pos_data),
                'win_freq': len(wins) / len(pos_data) * 100,
                'loss_freq': len(losses) / len(pos_data) * 100,
                'avg_win': wins['profit_bb'].mean() if len(wins) > 0 else 0,
                'avg_loss': losses['profit_bb'].mean() if len(losses) > 0 else 0,
                'total_win': wins['profit_bb'].sum() if len(wins) > 0 else 0,
                'total_loss': losses['profit_bb'].sum() if len(losses) > 0 else 0,
                'ev': pos_data['profit_bb'].mean(),
                'std': pos_data['profit_bb'].std()
            })
        
        return pd.DataFrame(results)
    
    def print_position_wins_losses_report(self):
        
        stats = self.analyze_wins_losses_by_position()
        
        print("="*80)
        print(" "*15 + "2. GANHOS E PERDAS POR POSIÇÃO (6 POSIÇÕES)")
        print("="*80)
        print()
        
        for _, row in stats.iterrows():
            print(f" {row['position']:>3s}:")
            print(f"    Mãos: {int(row['total_hands']):,}")
            print(f"    Win rate: {row['win_freq']:.1f}% | Loss rate: {row['loss_freq']:.1f}%")
            print(f"    Quando GANHA: +{row['avg_win']:.2f} BB (total: +{row['total_win']:,.0f} BB)")
            print(f"    Quando PERDE: {row['avg_loss']:.2f} BB (total: {row['total_loss']:,.0f} BB)")
            print(f"    EV médio: {row['ev']:+.3f} BB/mão (σ={row['std']:.2f})")
            print()
    
    def plot_position_wins_losses(self, save_path: str = None):

        stats = self.analyze_wins_losses_by_position()
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        positions = stats['position'].values
        x = np.arange(len(positions))
        
       
        width = 0.35
        axes[0, 0].bar(x - width/2, stats['avg_win'], width, label='Ganho Médio', 
                      color='green', alpha=0.7, edgecolor='black')
        axes[0, 0].bar(x + width/2, stats['avg_loss'], width, label='Perda Média', 
                      color='red', alpha=0.7, edgecolor='black')
        axes[0, 0].set_xlabel('Posição', fontweight='bold')
        axes[0, 0].set_ylabel('Profit Médio (BB)', fontweight='bold')
        axes[0, 0].set_title('Tamanho Médio: Ganhos vs Perdas por Posição', fontweight='bold', fontsize=14)
        axes[0, 0].set_xticks(x)
        axes[0, 0].set_xticklabels(positions)
        axes[0, 0].legend()
        axes[0, 0].grid(alpha=0.3)
        axes[0, 0].axhline(y=0, color='black', linestyle='--', linewidth=1)
        
        axes[0, 1].bar(x - width/2, stats['win_freq'], width, label='% Vitórias', 
                      color='green', alpha=0.7, edgecolor='black')
        axes[0, 1].bar(x + width/2, stats['loss_freq'], width, label='% Derrotas', 
                      color='red', alpha=0.7, edgecolor='black')
        axes[0, 1].set_xlabel('Posição', fontweight='bold')
        axes[0, 1].set_ylabel('Frequência (%)', fontweight='bold')
        axes[0, 1].set_title('Frequência: Ganhos vs Perdas por Posição', fontweight='bold', fontsize=14)
        axes[0, 1].set_xticks(x)
        axes[0, 1].set_xticklabels(positions)
        axes[0, 1].legend()
        axes[0, 1].grid(alpha=0.3)
        
        axes[1, 0].bar(x - width/2, stats['total_win'], width, label='Total Ganho', 
                      color='green', alpha=0.7, edgecolor='black')
        axes[1, 0].bar(x + width/2, stats['total_loss'], width, label='Total Perdido', 
                      color='red', alpha=0.7, edgecolor='black')
        axes[1, 0].set_xlabel('Posição', fontweight='bold')
        axes[1, 0].set_ylabel('Total (BB)', fontweight='bold')
        axes[1, 0].set_title('Total Acumulado por Posição', fontweight='bold', fontsize=14)
        axes[1, 0].set_xticks(x)
        axes[1, 0].set_xticklabels(positions)
        axes[1, 0].legend()
        axes[1, 0].grid(alpha=0.3)
        axes[1, 0].axhline(y=0, color='black', linestyle='--', linewidth=1)
        
        data_by_pos = [
            self.df_players[self.df_players['position'] == pos]['profit_bb'].dropna()
            for pos in positions
        ]
        
        bp = axes[1, 1].boxplot(data_by_pos, labels=positions, patch_artist=True, showmeans=True)
        for patch in bp['boxes']:
            patch.set_facecolor('lightblue')
        
        axes[1, 1].axhline(y=0, color='red', linestyle='--', linewidth=1)
        axes[1, 1].set_xlabel('Posição', fontweight='bold')
        axes[1, 1].set_ylabel('Profit (BB)', fontweight='bold')
        axes[1, 1].set_title('Distribuição Completa por Posição', fontweight='bold', fontsize=14)
        axes[1, 1].grid(alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()
    
    
    def analyze_losing_hands(self) -> pd.DataFrame:

        df_visible = self.df_players[self.df_players['hole_cards'].notna()].copy()
        
        if len(df_visible) == 0:
            return pd.DataFrame()
        
        df_visible['hand_class'] = df_visible['hole_cards'].apply(
            lambda x: self.classify_starting_hand(x)[0]
        )
        
        hand_ev = df_visible.groupby('hand_class').agg({
            'profit_bb': ['mean', 'std', 'count', 'sum'],
            'profit': lambda x: (x < 0).sum()  
        }).round(3)
        
        hand_ev.columns = ['ev', 'std', 'n', 'total_profit', 'loss_count']
        hand_ev = hand_ev.reset_index()
        
        hand_ev = hand_ev[hand_ev['n'] >= 10]
        
        hand_ev['loss_rate'] = (hand_ev['loss_count'] / hand_ev['n'] * 100).round(1)
        
        losing_hands = hand_ev[hand_ev['ev'] < 0].sort_values('ev')
        
        return losing_hands
    
    def print_losing_hands_report(self):
        losing = self.analyze_losing_hands()
        
        print("="*80)
        print(" "*15 + "3. MÃOS QUE PERDEM DINHEIRO")
        print("="*80)
        print()
        
        if len(losing) == 0:
            print("Dados insuficientes (hole cards não visíveis)")
            print()
            return
        
        print(f" MÃOS COM EV NEGATIVO: {len(losing)}")
        print()
        
        premium_hands = ['AA', 'KK', 'QQ', 'JJ', 'TT', 'AKs', 'AQs', 'AKo']
        premium_losing = losing[losing['hand_class'].isin(premium_hands)]
        
        if len(premium_losing) > 0:
            print(" MÃOS PREMIUM COM EV NEGATIVO:")
            for _, row in premium_losing.iterrows():
                print(f"  {row['hand_class']:>5s}: {row['ev']:+.3f} BB/mão  "
                      f"(loss rate: {row['loss_rate']:.1f}%, n={int(row['n'])})")
            print()
        
        print("TOP 15 PIORES MÃOS (por EV):")
        for _, row in losing.head(15).iterrows():
            print(f"  {row['hand_class']:>5s}: {row['ev']:+.3f} BB/mão  "
                  f"(total: {row['total_profit']:+,.0f} BB, loss rate: {row['loss_rate']:.1f}%, n={int(row['n'])})")
        print()
        
        print("INSIGHTS:")
        worst_hand = losing.iloc[0]
        print(f"   Pior mão: {worst_hand['hand_class']} ({worst_hand['ev']:.3f} BB/mão)")
        print(f"   Total de mãos não lucrativas: {len(losing)}")
        
        if len(premium_losing) > 0:
            print(f"   {len(premium_losing)} mãos premium com EV negativo - indica overplay")
        else:
            print(f"  Nenhuma mão premium com EV negativo")
        print()
    
    
    def analyze_loss_distribution(self) -> Dict:

        losses = self.df_players[self.df_players['outcome'] == 'loss'].copy()
        
        loss_by_position = losses.groupby('position').agg({
            'profit_bb': ['mean', 'sum', 'count', lambda x: x.quantile(0.05)]
        }).round(2)
        loss_by_position.columns = ['avg_loss', 'total_loss', 'n_losses', 'worst_5pct']
        loss_by_position = loss_by_position.sort_values('total_loss')
        
        loss_by_street = losses.groupby('final_street').agg({
            'profit_bb': ['mean', 'sum', 'count', lambda x: x.quantile(0.05)]
        }).round(2)
        loss_by_street.columns = ['avg_loss', 'total_loss', 'n_losses', 'worst_5pct']
        
        worst_5pct = losses['profit_bb'].quantile(0.05)
        catastrophic = losses[losses['profit_bb'] <= worst_5pct]
        
        return {
            'by_position': loss_by_position,
            'by_street': loss_by_street,
            'worst_5pct_threshold': worst_5pct,
            'catastrophic_losses': catastrophic
        }
    
    def print_loss_distribution_report(self):
        analysis = self.analyze_loss_distribution()
        
        print("="*80)
        print(" "*20 + "4. ONDE O DINHEIRO É PERDIDO")
        print("="*80)
        print()
        
        print(" PERDAS POR POSIÇÃO:")
        for pos, row in analysis['by_position'].iterrows():
            print(f"  {pos:>3s}: {row['avg_loss']:.2f} BB/perda  "
                  f"(total: {row['total_loss']:,.0f} BB, n={int(row['n_losses']):,})  "
                  f"Pior 5%: {row['worst_5pct']:.2f} BB")
        print()
        
        print(" PERDAS POR STREET FINAL:")
        for street, row in analysis['by_street'].iterrows():
            print(f"  {street.upper():>7s}: {row['avg_loss']:.2f} BB/perda  "
                  f"(total: {row['total_loss']:,.0f} BB, n={int(row['n_losses']):,})  "
                  f"Pior 5%: {row['worst_5pct']:.2f} BB")
        print()
        
        print("  CAUDA DA DISTRIBUIÇÃO (5% piores perdas):")
        print(f"  Threshold: {analysis['worst_5pct_threshold']:.2f} BB")
        print(f"  Número de perdas catastróficas: {len(analysis['catastrophic_losses']):,}")
        print(f"  Perda média nestas mãos: {analysis['catastrophic_losses']['profit_bb'].mean():.2f} BB")
        print(f"  Pior perda individual: {analysis['catastrophic_losses']['profit_bb'].min():.2f} BB")
        print()
        
        worst_pos = analysis['by_position'].index[0]
        worst_street = analysis['by_street']['total_loss'].idxmin()
        
        print(" MAIORES PONTOS DE VAZAMENTO:")
        print(f"   Posição: {worst_pos} ({analysis['by_position'].loc[worst_pos, 'total_loss']:,.0f} BB total)")
        print(f"   Street: {worst_street.upper()} ({analysis['by_street'].loc[worst_street, 'total_loss']:,.0f} BB total)")
        print()
    
    def plot_loss_distribution(self, save_path: str = None):

        analysis = self.analyze_loss_distribution()
        losses = self.df_players[self.df_players['outcome'] == 'loss']
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        axes[0, 0].hist(losses['profit_bb'], bins=50, color='red', alpha=0.7, edgecolor='black')
        axes[0, 0].axvline(analysis['worst_5pct_threshold'], color='darkred', 
                          linestyle='--', linewidth=2, 
                          label=f'5% pior: {analysis["worst_5pct_threshold"]:.2f} BB')
        axes[0, 0].axvline(losses['profit_bb'].mean(), color='orange', 
                          linestyle='--', linewidth=2, 
                          label=f'Média: {losses["profit_bb"].mean():.2f} BB')
        axes[0, 0].set_xlabel('Perda (BB)', fontweight='bold')
        axes[0, 0].set_ylabel('Frequência', fontweight='bold')
        axes[0, 0].set_title('Distribuição de Perdas (Cauda Destacada)', fontweight='bold', fontsize=14)
        axes[0, 0].legend()
        axes[0, 0].grid(alpha=0.3)
        
        pos_data = analysis['by_position'].sort_values('total_loss')
        axes[0, 1].barh(pos_data.index, pos_data['total_loss'], color='red', alpha=0.7, edgecolor='black')
        axes[0, 1].set_xlabel('Total Perdido (BB)', fontweight='bold')
        axes[0, 1].set_ylabel('Posição', fontweight='bold')
        axes[0, 1].set_title('Total de Perdas por Posição', fontweight='bold', fontsize=14)
        axes[0, 1].grid(alpha=0.3)
        
        street_data = analysis['by_street'].sort_values('total_loss')
        colors_street = ['#ff4444', '#ff6666', '#ff8888', '#ffaaaa']
        axes[1, 0].bar(street_data.index, street_data['total_loss'], 
                      color=colors_street[:len(street_data)], alpha=0.7, edgecolor='black')
        axes[1, 0].set_xlabel('Street Final', fontweight='bold')
        axes[1, 0].set_ylabel('Total Perdido (BB)', fontweight='bold')
        axes[1, 0].set_title('Total de Perdas por Street Final', fontweight='bold', fontsize=14)
        axes[1, 0].grid(alpha=0.3)
        
        pivot_data = losses.pivot_table(
            values='profit_bb',
            index='position',
            columns='final_street',
            aggfunc='mean'
        )
        
        positions_order = ['SB', 'BB', 'UTG', 'MP', 'CO', 'BTN']
        pivot_data = pivot_data.reindex(positions_order)
        
        im = axes[1, 1].imshow(pivot_data.values, cmap='Reds', aspect='auto')
        
        axes[1, 1].set_xticks(np.arange(len(pivot_data.columns)))
        axes[1, 1].set_yticks(np.arange(len(pivot_data.index)))
        axes[1, 1].set_xticklabels(pivot_data.columns)
        axes[1, 1].set_yticklabels(pivot_data.index)
        axes[1, 1].set_xlabel('Street Final', fontweight='bold')
        axes[1, 1].set_ylabel('Posição', fontweight='bold')
        axes[1, 1].set_title('Heatmap: Perda Média (Posição × Street)', fontweight='bold', fontsize=14)
        
        for i in range(len(pivot_data.index)):
            for j in range(len(pivot_data.columns)):
                value = pivot_data.iloc[i, j]
                if not np.isnan(value):
                    axes[1, 1].text(j, i, f'{value:.2f}',
                                   ha="center", va="center", color='white', fontweight='bold')
        
        plt.colorbar(im, ax=axes[1, 1], label='Perda Média (BB)')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()

    
    def calculate_cumulative_profit(self) -> pd.DataFrame:
        df_sorted = self.df_players.sort_values(['session', 'hand_id']).copy()
        df_sorted['cumulative_profit_bb'] = df_sorted['profit_bb'].cumsum()
        df_sorted['hand_number'] = range(len(df_sorted))
        return df_sorted[['hand_number', 'cumulative_profit_bb', 'profit_bb']]
    
    def calculate_drawdown(self, cumulative: pd.DataFrame) -> Dict:
        cum_profit = cumulative['cumulative_profit_bb'].values
        running_max = np.maximum.accumulate(cum_profit)
        drawdown = cum_profit - running_max
        max_drawdown = drawdown.min()
        max_drawdown_idx = drawdown.argmin()
        
        return {
            'max_drawdown': max_drawdown,
            'max_drawdown_hand': max_drawdown_idx,
            'drawdown_series': drawdown
        }
    
    def plot_cumulative_profit(self, save_path: str = None):
        cumulative = self.calculate_cumulative_profit()
        drawdown_data = self.calculate_drawdown(cumulative)
        
        fig, axes = plt.subplots(2, 1, figsize=(16, 10))
        
        axes[0].plot(cumulative['hand_number'], cumulative['cumulative_profit_bb'], 
                    color='steelblue', linewidth=1.5, alpha=0.8)
        axes[0].axhline(y=0, color='red', linestyle='--', linewidth=1)
        axes[0].fill_between(cumulative['hand_number'], 0, cumulative['cumulative_profit_bb'],
                            where=(cumulative['cumulative_profit_bb'] >= 0), 
                            color='green', alpha=0.2)
        axes[0].fill_between(cumulative['hand_number'], 0, cumulative['cumulative_profit_bb'],
                            where=(cumulative['cumulative_profit_bb'] < 0), 
                            color='red', alpha=0.2)
        
        axes[0].set_xlabel('Número da Mão', fontweight='bold')
        axes[0].set_ylabel('Lucro Cumulativo (BB)', fontweight='bold')
        axes[0].set_title('Curva de Lucro Cumulativo', fontweight='bold', fontsize=14)
        axes[0].grid(alpha=0.3)
        
        final_profit = cumulative['cumulative_profit_bb'].iloc[-1]
        axes[0].text(0.02, 0.98, 
                    f"Lucro Final: {final_profit:+,.0f} BB\nMáx Drawdown: {drawdown_data['max_drawdown']:,.0f} BB",
                    transform=axes[0].transAxes, fontsize=12, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        axes[1].fill_between(cumulative['hand_number'], 0, drawdown_data['drawdown_series'],
                            color='red', alpha=0.5)
        axes[1].plot(cumulative['hand_number'], drawdown_data['drawdown_series'],
                    color='darkred', linewidth=1)
        axes[1].set_xlabel('Número da Mão', fontweight='bold')
        axes[1].set_ylabel('Drawdown (BB)', fontweight='bold')
        axes[1].set_title('Drawdown ao Longo do Tempo', fontweight='bold', fontsize=14)
        axes[1].grid(alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()
    
    def classify_starting_hand(self, hole_cards: str) -> Tuple[str, str]:
        if pd.isna(hole_cards):
            return ("Unknown", "Unknown")
        
        cards = hole_cards.strip().split()
        if len(cards) < 2:
            return ("Unknown", "Unknown")
        
        rank1 = cards[0][0]
        suit1 = cards[0][-1]
        rank2 = cards[1][0]
        suit2 = cards[1][-1]
        
        rank_order = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10,
                     '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2}
        
        r1_val = rank_order.get(rank1, 0)
        r2_val = rank_order.get(rank2, 0)
        
        if r1_val < r2_val:
            rank1, rank2 = rank2, rank1
            suit1, suit2 = suit2, suit1
        
        if rank1 == rank2:
            return (f"{rank1}{rank2}", f"{rank1}{rank2}")
        elif suit1 == suit2:
            return (f"{rank1}{rank2}s", f"{rank1}{rank2}s")
        else:
            return (f"{rank1}{rank2}o", f"{rank1}{rank2}o")
    
    def analyze_hand_strength_matrix(self) -> pd.DataFrame:
        df_visible = self.df_players[self.df_players['hole_cards'].notna()].copy()
        
        if len(df_visible) == 0:
            return pd.DataFrame()
        
        df_visible['hand_class'] = df_visible['hole_cards'].apply(
            lambda x: self.classify_starting_hand(x)[0]
        )
        
        hand_stats = df_visible.groupby('hand_class').agg({
            'profit': lambda x: (x > 0).mean() * 100,
            'profit_bb': ['mean', 'count']
        }).round(2)
        
        hand_stats.columns = ['win_rate', 'avg_profit_bb', 'n']
        hand_stats = hand_stats.reset_index()
        hand_stats = hand_stats[hand_stats['n'] >= 10]
        hand_stats = hand_stats.sort_values('win_rate', ascending=False)
        
        return hand_stats
    
    def create_hand_matrix_for_heatmap(self) -> pd.DataFrame:
        ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
        
        hand_stats = self.analyze_hand_strength_matrix()
        
        if len(hand_stats) == 0:
            return pd.DataFrame(np.nan, index=ranks, columns=ranks)
        
        winrate_dict = dict(zip(hand_stats['hand_class'], hand_stats['win_rate']))
        
        matrix = np.zeros((13, 13))
        
        for i, rank1 in enumerate(ranks):
            for j, rank2 in enumerate(ranks):
                if i == j:
                    hand = f"{rank1}{rank2}"
                elif i < j:
                    hand = f"{rank1}{rank2}s"
                else:
                    hand = f"{rank2}{rank1}o"
                
                matrix[i, j] = winrate_dict.get(hand, np.nan)
        
        df_matrix = pd.DataFrame(matrix, index=ranks, columns=ranks)
        
        return df_matrix
    
    def plot_hand_strength_heatmap(self, save_path: str = None):
        matrix = self.create_hand_matrix_for_heatmap()
        
        fig, ax = plt.subplots(figsize=(14, 12))
        
        im = ax.imshow(matrix.values, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)
        
        ax.set_xticks(np.arange(len(matrix.columns)))
        ax.set_yticks(np.arange(len(matrix.index)))
        ax.set_xticklabels(matrix.columns)
        ax.set_yticklabels(matrix.index)
        
        ax.set_xlabel('Segunda Carta', fontweight='bold', fontsize=12)
        ax.set_ylabel('Primeira Carta', fontweight='bold', fontsize=12)
        ax.set_title('Preflop Hand Win % Heatmap with Ranks and Labels', 
                    fontweight='bold', fontsize=14)
        
        for i in range(len(matrix.index)):
            for j in range(len(matrix.columns)):
                value = matrix.iloc[i, j]
                
                if not np.isnan(value):
                    rank1 = matrix.index[i]
                    rank2 = matrix.columns[j]
                    
                    if i == j:
                        hand_label = f"{rank1}{rank2}"
                    elif i < j:
                        hand_label = f"{rank1}{rank2}s"
                    else:
                        hand_label = f"{rank2}{rank1}o"
                    
                    text_color = 'white' if value < 50 else 'black'
                    
                    ax.text(j, i, f"{value:.1f}%\n{hand_label}",
                           ha="center", va="center", color=text_color,
                           fontsize=8, fontweight='bold')
        
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Win %', rotation=270, labelpad=20, fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()
    
    
    def generate_complete_report(self, save_dir: str = 'outputs'):
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        
        print("\n" + "="*80)
        print(" "*10 + " ANÁLISE DE TOMADA DE DECISÃO SOB INCERTEZA")
        print(" "*15 + "Avaliação de Risco, Contexto e Valor Esperado")
        print("="*80)
        print()
        
        self.print_wins_losses_report()
        print("Gerando gráficos de ganhos e perdas...")
        self.plot_wins_losses_distribution(save_dir / '01_wins_losses_distribution.png')
        
        self.print_position_wins_losses_report()
        print("Gerando gráficos por posição...")
        self.plot_position_wins_losses(save_dir / '02_position_wins_losses.png')
        
        self.print_losing_hands_report()
        
        self.print_loss_distribution_report()
        print("Gerando gráficos de distribuição de perdas...")
        self.plot_loss_distribution(save_dir / '03_loss_distribution.png')
        
        print("="*80)
        print(" "*25 + "5. CURVA DE LUCRO CUMULATIVO")
        print("="*80)
        print()
        cumulative = self.calculate_cumulative_profit()
        drawdown_data = self.calculate_drawdown(cumulative)
        
        final_profit = cumulative['cumulative_profit_bb'].iloc[-1]
        print(f"Lucro final: {final_profit:+,.2f} BB")
        print(f"Máximo drawdown: {drawdown_data['max_drawdown']:,.2f} BB")
        print()
        
        print("Gerando curva de lucro cumulativo...")
        self.plot_cumulative_profit(save_dir / '04_cumulative_profit.png')
        
        hand_stats = self.analyze_hand_strength_matrix()
        
        if len(hand_stats) > 0:
            print("="*80)
            print(" "*18 + "6. PROBABILIDADE DE VITÓRIA POR MÃO")
            print("="*80)
            print()
            print(f"{len(hand_stats)} mãos distintas analisadas")
            print()
            print("TOP 10 MÃOS:")
            for _, row in hand_stats.head(10).iterrows():
                print(f"  {row['hand_class']:>5s}: {row['win_rate']:5.1f}% win rate  "
                      f"({row['avg_profit_bb']:+6.2f} BB/mão, n={int(row['n'])})")
            print()
            
            print("Gerando heatmap de probabilidades...")
            self.plot_hand_strength_heatmap(save_dir / '05_hand_strength_heatmap.png')
        
        print("\n" + "="*80)
        print("ANÁLISE COMPLETA FINALIZADA")
        print("="*80)
        print()
        print(f"Todos os gráficos salvos em: {save_dir}/")
        print()

def analyze_complete(
    hands_path: str = 'data/hands.parquet',
    players_path: str = 'data/players_in_hand.parquet',
    save_dir: str = 'outputs'
) -> CompletePokerAnalysis:
    print("Carregando dados...")
    df_hands = pd.read_parquet(hands_path)
    df_players = pd.read_parquet(players_path)
    
    print(f"{len(df_hands):,} mãos carregadas")
    print(f"{len(df_players):,} registros de jogadores carregados")
    print()
    
    analysis = CompletePokerAnalysis(df_hands, df_players)
    analysis.generate_complete_report(save_dir)
    
    return analysis
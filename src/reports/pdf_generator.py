"""
Gerador de Relatórios em PDF
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import matplotlib
matplotlib.use('Agg')  # Backend sem display
import matplotlib.pyplot as plt
import pandas as pd
import polars as pl
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure

from config.settings import REPORTS_DIR

logger = logging.getLogger(__name__)


class PDFGenerator:
    """Gera relatórios em PDF a partir de dados"""

    def __init__(self, output_dir: Path = REPORTS_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(self, data: pl.DataFrame, params: Dict[str, Any],
                       report_type: str = "detailed") -> Optional[Path]:
        """
        Gera relatório PDF

        Args:
            data: DataFrame com os dados
            params: Parâmetros da consulta
            report_type: Tipo de relatório (detailed, summary, hourly)

        Returns:
            Caminho do arquivo PDF gerado
        """
        if data is None or len(data) == 0:
            logger.warning("Sem dados para gerar relatório")
            return None

        # Gera nome do arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unidade = params.get("unidade", "geral")
        operacao = params.get("operacao", "operacao")
        filename = f"relatorio_{unidade}_{operacao}_{timestamp}.pdf"
        filepath = self.output_dir / filename

        try:
            # Converte para Pandas se necessário
            if isinstance(data, pl.DataFrame):
                df = data.to_pandas()
            else:
                df = data

            # Cria PDF
            with PdfPages(filepath) as pdf:
                # Página 1: Resumo
                self._create_summary_page(pdf, df, params)

                # Página 2: Gráficos
                if report_type in ["detailed", "hourly"]:
                    self._create_charts_page(pdf, df, params)

                # Página 3: Tabela de dados
                if report_type == "detailed":
                    self._create_data_table_page(pdf, df, params)

                # Página 4: Análise hora a hora (se solicitado)
                if report_type == "hourly":
                    self._create_hourly_page(pdf, df, params)

                # Metadados do PDF
                d = pdf.infodict()
                d['Title'] = f'Relatório {operacao.title()} - {unidade.title()}'
                d['Author'] = 'CIABot Oráculo'
                d['Subject'] = f'Relatório de {operacao}'
                d['CreationDate'] = datetime.now()

            logger.info(f"Relatório gerado: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Erro ao gerar PDF: {e}")
            return None

    def _create_summary_page(self, pdf: PdfPages, df: pd.DataFrame,
                            params: Dict[str, Any]) -> None:
        """Cria página de resumo"""
        fig = Figure(figsize=(8.5, 11))
        ax = fig.add_subplot(111)
        ax.axis('off')

        # Título
        unidade = params.get("unidade", "Geral")
        operacao = params.get("operacao", "Operação")
        periodo = params.get("periodo", "Período")

        title = f"Relatório de {operacao.title()}\n{unidade.title()}"
        ax.text(0.5, 0.95, title, ha='center', va='top',
               fontsize=20, fontweight='bold', transform=ax.transAxes)

        # Data/hora
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        ax.text(0.5, 0.90, f"Gerado em: {now}", ha='center', va='top',
               fontsize=10, transform=ax.transAxes)

        # Período
        ax.text(0.5, 0.85, f"Período: {periodo}", ha='center', va='top',
               fontsize=12, transform=ax.transAxes)

        # Estatísticas principais
        stats_y = 0.75
        ax.text(0.1, stats_y, "ESTATÍSTICAS GERAIS", ha='left', va='top',
               fontsize=14, fontweight='bold', transform=ax.transAxes)

        stats_y -= 0.08
        ax.text(0.1, stats_y, f"Total de registros: {len(df):,}",
               ha='left', va='top', fontsize=12, transform=ax.transAxes)

        # Colunas numéricas
        numeric_cols = df.select_dtypes(include=['number']).columns
        stats_y -= 0.06

        for col in numeric_cols[:5]:  # Limita a 5 métricas
            total = df[col].sum()
            media = df[col].mean()

            ax.text(0.1, stats_y, f"{col}:", ha='left', va='top',
                   fontsize=11, fontweight='bold', transform=ax.transAxes)
            stats_y -= 0.04
            ax.text(0.15, stats_y, f"Total: {total:,.2f}  |  Média: {media:,.2f}",
                   ha='left', va='top', fontsize=10, transform=ax.transAxes)
            stats_y -= 0.05

        # Rodapé
        ax.text(0.5, 0.05, "CIABot Oráculo - Sistema de Inteligência Agrícola",
               ha='center', va='bottom', fontsize=8, style='italic',
               transform=ax.transAxes)

        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

    def _create_charts_page(self, pdf: PdfPages, df: pd.DataFrame,
                           params: Dict[str, Any]) -> None:
        """Cria página com gráficos"""
        fig = Figure(figsize=(8.5, 11))

        # Detecta colunas relevantes
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()

        if not date_cols and 'data' in df.columns:
            df['data'] = pd.to_datetime(df['data'], errors='coerce')
            date_cols = ['data']

        # Gráfico 1: Evolução temporal (se houver data)
        if date_cols and numeric_cols:
            ax1 = fig.add_subplot(2, 1, 1)
            date_col = date_cols[0]
            metric_col = numeric_cols[0]

            df_sorted = df.sort_values(date_col)
            ax1.plot(df_sorted[date_col], df_sorted[metric_col],
                    marker='o', linewidth=2)
            ax1.set_title(f'Evolução de {metric_col}', fontsize=12, fontweight='bold')
            ax1.set_xlabel('Data')
            ax1.set_ylabel(metric_col)
            ax1.grid(True, alpha=0.3)
            ax1.tick_params(axis='x', rotation=45)

        # Gráfico 2: Distribuição ou agregação
        if len(numeric_cols) >= 2:
            ax2 = fig.add_subplot(2, 1, 2)

            # Se tiver coluna de agrupamento (unidade, turno, etc)
            group_cols = [col for col in df.columns
                         if col.lower() in ['unidade', 'turno', 'frente', 'equipamento']]

            if group_cols:
                group_col = group_cols[0]
                metric_col = numeric_cols[0]

                grouped = df.groupby(group_col)[metric_col].sum().sort_values(ascending=False)
                grouped[:10].plot(kind='bar', ax=ax2, color='steelblue')
                ax2.set_title(f'{metric_col} por {group_col}',
                            fontsize=12, fontweight='bold')
                ax2.set_xlabel(group_col)
                ax2.set_ylabel(metric_col)
                ax2.tick_params(axis='x', rotation=45)
            else:
                # Gráfico de distribuição
                metric_col = numeric_cols[0]
                ax2.hist(df[metric_col].dropna(), bins=20, color='steelblue', edgecolor='black')
                ax2.set_title(f'Distribuição de {metric_col}',
                            fontsize=12, fontweight='bold')
                ax2.set_xlabel(metric_col)
                ax2.set_ylabel('Frequência')

            ax2.grid(True, alpha=0.3, axis='y')

        fig.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

    def _create_data_table_page(self, pdf: PdfPages, df: pd.DataFrame,
                               params: Dict[str, Any]) -> None:
        """Cria página com tabela de dados"""
        # Limita a 100 linhas para não ficar muito grande
        df_display = df.head(100)

        # Seleciona colunas mais relevantes
        cols_to_show = df_display.columns.tolist()[:8]  # Máximo 8 colunas
        df_display = df_display[cols_to_show]

        # Formata valores numéricos
        for col in df_display.select_dtypes(include=['number']).columns:
            df_display[col] = df_display[col].apply(lambda x: f'{x:,.2f}' if pd.notna(x) else '')

        fig = Figure(figsize=(8.5, 11))
        ax = fig.add_subplot(111)
        ax.axis('tight')
        ax.axis('off')

        # Título
        ax.text(0.5, 0.98, 'Dados Detalhados', ha='center', va='top',
               fontsize=14, fontweight='bold', transform=ax.transAxes)

        # Tabela
        table_data = [df_display.columns.tolist()] + df_display.values.tolist()

        table = ax.table(cellText=table_data, cellLoc='left',
                        loc='center', bbox=[0, 0.05, 1, 0.90])

        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 1.5)

        # Estiliza cabeçalho
        for i in range(len(cols_to_show)):
            table[(0, i)].set_facecolor('#4472C4')
            table[(0, i)].set_text_props(weight='bold', color='white')

        # Rodapé
        if len(df) > 100:
            ax.text(0.5, 0.02, f'Mostrando 100 de {len(df)} registros',
                   ha='center', va='bottom', fontsize=8, style='italic',
                   transform=ax.transAxes)

        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

    def _create_hourly_page(self, pdf: PdfPages, df: pd.DataFrame,
                           params: Dict[str, Any]) -> None:
        """Cria página com análise hora a hora"""
        fig = Figure(figsize=(8.5, 11))

        # Tenta extrair hora
        date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()

        if not date_cols and 'data' in df.columns:
            df['data'] = pd.to_datetime(df['data'], errors='coerce')
            date_cols = ['data']

        if date_cols:
            date_col = date_cols[0]
            df['hora'] = pd.to_datetime(df[date_col]).dt.hour

            # Agrupa por hora
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            numeric_cols = [col for col in numeric_cols if col != 'hora']

            if numeric_cols:
                metric_col = numeric_cols[0]
                hourly = df.groupby('hora')[metric_col].agg(['sum', 'mean', 'count'])

                ax = fig.add_subplot(111)
                x = hourly.index

                ax.bar(x, hourly['sum'], alpha=0.7, label='Total', color='steelblue')
                ax.set_xlabel('Hora do dia', fontsize=12)
                ax.set_ylabel(f'{metric_col} (Total)', fontsize=12)
                ax.set_title(f'Análise Hora a Hora - {metric_col}',
                           fontsize=14, fontweight='bold')
                ax.legend()
                ax.grid(True, alpha=0.3, axis='y')
                ax.set_xticks(range(24))

                # Adiciona tabela
                table_data = []
                table_data.append(['Hora', 'Total', 'Média', 'Registros'])

                for hour in range(24):
                    if hour in hourly.index:
                        row = hourly.loc[hour]
                        table_data.append([
                            f'{hour:02d}:00',
                            f'{row["sum"]:,.2f}',
                            f'{row["mean"]:,.2f}',
                            f'{int(row["count"])}'
                        ])
                    else:
                        table_data.append([f'{hour:02d}:00', '-', '-', '0'])

                # Cria tabela em subplot separado
                ax_table = fig.add_subplot(2, 1, 2)
                ax_table.axis('tight')
                ax_table.axis('off')

                table = ax_table.table(cellText=table_data, cellLoc='center',
                                      loc='center', bbox=[0, 0, 1, 1])
                table.auto_set_font_size(False)
                table.set_fontsize(8)

                # Estiliza cabeçalho
                for i in range(4):
                    table[(0, i)].set_facecolor('#4472C4')
                    table[(0, i)].set_text_props(weight='bold', color='white')

        fig.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

    def cleanup_old_reports(self, days: int = 7) -> None:
        """Remove relatórios antigos"""
        cutoff = datetime.now().timestamp() - (days * 86400)

        for file in self.output_dir.glob("*.pdf"):
            if file.stat().st_mtime < cutoff:
                file.unlink()
                logger.info(f"Relatório removido: {file.name}")

"""
Módulo de Previsões e Análise de Tendências
Usa dados históricos para prever comportamentos futuros
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import polars as pl

logger = logging.getLogger(__name__)


class PredictionsEngine:
    """Motor de previsões e análise de tendências"""

    def __init__(self):
        logger.info("PredictionsEngine inicializado")

    def analyze_trend(self, df: pl.DataFrame, metric_column: str,
                     date_column: str = "data") -> Dict[str, Any]:
        """
        Analisa tendência de uma métrica ao longo do tempo

        Args:
            df: DataFrame com dados
            metric_column: Coluna da métrica a analisar
            date_column: Coluna de data

        Returns:
            Análise de tendência
        """
        try:
            # Converte para Pandas para análise
            if isinstance(df, pl.DataFrame):
                pdf = df.to_pandas()
            else:
                pdf = df

            if metric_column not in pdf.columns:
                return {"error": f"Coluna {metric_column} não encontrada"}

            # Garante que data está em datetime
            pdf[date_column] = pd.to_datetime(pdf[date_column])
            pdf = pdf.sort_values(date_column)

            # Remove valores nulos
            pdf = pdf.dropna(subset=[metric_column])

            if len(pdf) < 3:
                return {"error": "Dados insuficientes para análise de tendência"}

            # Calcula estatísticas
            values = pdf[metric_column].values

            # Regressão linear simples
            x = np.arange(len(values))
            coeffs = np.polyfit(x, values, 1)
            trend_line = np.poly1d(coeffs)

            # Determina direção da tendência
            slope = coeffs[0]
            if slope > 0.01:
                direction = "crescente"
            elif slope < -0.01:
                direction = "decrescente"
            else:
                direction = "estável"

            # Calcula variação percentual
            first_value = values[0]
            last_value = values[-1]
            percent_change = ((last_value - first_value) / first_value * 100) \
                if first_value != 0 else 0

            # Identifica picos e vales
            peaks = self._find_peaks(values)
            valleys = self._find_valleys(values)

            # Calcula volatilidade (desvio padrão)
            volatility = np.std(values)

            # Média móvel (últimos 7 pontos)
            window = min(7, len(values))
            moving_avg = pdf[metric_column].rolling(window=window).mean().iloc[-1]

            return {
                "metric": metric_column,
                "direction": direction,
                "slope": float(slope),
                "percent_change": float(percent_change),
                "current_value": float(last_value),
                "average": float(np.mean(values)),
                "moving_average": float(moving_avg),
                "volatility": float(volatility),
                "min": float(np.min(values)),
                "max": float(np.max(values)),
                "peaks_count": len(peaks),
                "valleys_count": len(valleys),
                "data_points": len(values),
                "period_days": (pdf[date_column].max() - pdf[date_column].min()).days
            }

        except Exception as e:
            logger.error(f"Erro ao analisar tendência: {e}")
            return {"error": str(e)}

    def predict_next_values(self, df: pl.DataFrame, metric_column: str,
                           periods: int = 7, date_column: str = "data") -> Dict[str, Any]:
        """
        Prevê próximos valores baseado em tendência

        Args:
            df: DataFrame com dados históricos
            metric_column: Coluna da métrica
            periods: Número de períodos para prever
            date_column: Coluna de data

        Returns:
            Previsões
        """
        try:
            # Converte para Pandas
            if isinstance(df, pl.DataFrame):
                pdf = df.to_pandas()
            else:
                pdf = df

            if metric_column not in pdf.columns:
                return {"error": f"Coluna {metric_column} não encontrada"}

            pdf[date_column] = pd.to_datetime(pdf[date_column])
            pdf = pdf.sort_values(date_column)
            pdf = pdf.dropna(subset=[metric_column])

            if len(pdf) < 5:
                return {"error": "Dados insuficientes para previsão"}

            values = pdf[metric_column].values
            dates = pdf[date_column].values

            # Regressão polinomial de grau 2
            x = np.arange(len(values))
            coeffs = np.polyfit(x, values, min(2, len(values) - 1))
            poly = np.poly1d(coeffs)

            # Gera previsões
            future_x = np.arange(len(values), len(values) + periods)
            predictions = poly(future_x)

            # Calcula intervalo de confiança (simplificado)
            residuals = values - poly(x)
            std_error = np.std(residuals)
            confidence_interval = 1.96 * std_error  # 95% de confiança

            # Gera datas futuras
            last_date = pd.to_datetime(dates[-1])
            date_diff = pd.to_datetime(dates[-1]) - pd.to_datetime(dates[-2]) \
                if len(dates) > 1 else timedelta(days=1)

            future_dates = [
                last_date + (date_diff * (i + 1))
                for i in range(periods)
            ]

            # Prepara resultado
            forecast = []
            for i, (date, pred) in enumerate(zip(future_dates, predictions)):
                forecast.append({
                    "date": date.isoformat(),
                    "predicted_value": float(max(0, pred)),  # Não permite negativos
                    "lower_bound": float(max(0, pred - confidence_interval)),
                    "upper_bound": float(pred + confidence_interval),
                    "confidence": 0.95 if i < 3 else 0.80  # Menos confiante para períodos distantes
                })

            return {
                "metric": metric_column,
                "forecast": forecast,
                "model": "polynomial_regression",
                "historical_points": len(values),
                "periods_ahead": periods
            }

        except Exception as e:
            logger.error(f"Erro ao prever valores: {e}")
            return {"error": str(e)}

    def compare_periods(self, df: pl.DataFrame, metric_column: str,
                       period1_start: datetime, period1_end: datetime,
                       period2_start: datetime, period2_end: datetime,
                       date_column: str = "data") -> Dict[str, Any]:
        """
        Compara métricas entre dois períodos

        Args:
            df: DataFrame com dados
            metric_column: Coluna da métrica
            period1_start, period1_end: Período 1
            period2_start, period2_end: Período 2
            date_column: Coluna de data

        Returns:
            Comparação detalhada
        """
        try:
            if isinstance(df, pl.DataFrame):
                pdf = df.to_pandas()
            else:
                pdf = df

            pdf[date_column] = pd.to_datetime(pdf[date_column])

            # Filtra períodos
            period1 = pdf[
                (pdf[date_column] >= period1_start) &
                (pdf[date_column] <= period1_end)
            ][metric_column]

            period2 = pdf[
                (pdf[date_column] >= period2_start) &
                (pdf[date_column] <= period2_end)
            ][metric_column]

            if len(period1) == 0 or len(period2) == 0:
                return {"error": "Sem dados para um ou ambos os períodos"}

            # Calcula estatísticas
            stats1 = {
                "total": float(period1.sum()),
                "average": float(period1.mean()),
                "median": float(period1.median()),
                "std": float(period1.std()),
                "min": float(period1.min()),
                "max": float(period1.max()),
                "count": int(len(period1))
            }

            stats2 = {
                "total": float(period2.sum()),
                "average": float(period2.mean()),
                "median": float(period2.median()),
                "std": float(period2.std()),
                "min": float(period2.min()),
                "max": float(period2.max()),
                "count": int(len(period2))
            }

            # Calcula diferenças
            total_diff = stats2["total"] - stats1["total"]
            total_pct = (total_diff / stats1["total"] * 100) if stats1["total"] != 0 else 0

            avg_diff = stats2["average"] - stats1["average"]
            avg_pct = (avg_diff / stats1["average"] * 100) if stats1["average"] != 0 else 0

            # Determina qual período foi melhor
            if total_diff > 0:
                better_period = "period2"
                improvement = "aumento"
            elif total_diff < 0:
                better_period = "period1"
                improvement = "redução"
            else:
                better_period = "equal"
                improvement = "sem mudança"

            return {
                "metric": metric_column,
                "period1": {
                    "start": period1_start.isoformat(),
                    "end": period1_end.isoformat(),
                    "stats": stats1
                },
                "period2": {
                    "start": period2_start.isoformat(),
                    "end": period2_end.isoformat(),
                    "stats": stats2
                },
                "comparison": {
                    "total_difference": float(total_diff),
                    "total_percent_change": float(total_pct),
                    "average_difference": float(avg_diff),
                    "average_percent_change": float(avg_pct),
                    "better_period": better_period,
                    "improvement": improvement
                }
            }

        except Exception as e:
            logger.error(f"Erro ao comparar períodos: {e}")
            return {"error": str(e)}

    def detect_anomalies(self, df: pl.DataFrame, metric_column: str,
                        threshold: float = 2.0) -> List[Dict[str, Any]]:
        """
        Detecta anomalias nos dados

        Args:
            df: DataFrame com dados
            metric_column: Coluna da métrica
            threshold: Número de desvios padrão para considerar anomalia

        Returns:
            Lista de anomalias detectadas
        """
        try:
            if isinstance(df, pl.DataFrame):
                pdf = df.to_pandas()
            else:
                pdf = df

            if metric_column not in pdf.columns:
                return []

            values = pdf[metric_column].dropna()

            if len(values) < 10:
                return []

            mean = values.mean()
            std = values.std()

            anomalies = []

            for idx, value in values.items():
                z_score = abs((value - mean) / std) if std != 0 else 0

                if z_score > threshold:
                    anomaly_type = "alto" if value > mean else "baixo"

                    anomalies.append({
                        "index": int(idx),
                        "value": float(value),
                        "z_score": float(z_score),
                        "type": anomaly_type,
                        "deviation_from_mean": float(value - mean),
                        "percent_deviation": float((value - mean) / mean * 100) if mean != 0 else 0
                    })

            return sorted(anomalies, key=lambda x: x['z_score'], reverse=True)

        except Exception as e:
            logger.error(f"Erro ao detectar anomalias: {e}")
            return []

    def _find_peaks(self, values: np.ndarray, min_distance: int = 1) -> List[int]:
        """Encontra picos nos dados"""
        peaks = []
        for i in range(min_distance, len(values) - min_distance):
            if values[i] > values[i-1] and values[i] > values[i+1]:
                peaks.append(i)
        return peaks

    def _find_valleys(self, values: np.ndarray, min_distance: int = 1) -> List[int]:
        """Encontra vales nos dados"""
        valleys = []
        for i in range(min_distance, len(values) - min_distance):
            if values[i] < values[i-1] and values[i] < values[i+1]:
                valleys.append(i)
        return valleys

    def seasonal_analysis(self, df: pl.DataFrame, metric_column: str,
                         date_column: str = "data") -> Dict[str, Any]:
        """
        Analisa sazonalidade nos dados

        Args:
            df: DataFrame com dados
            metric_column: Coluna da métrica
            date_column: Coluna de data

        Returns:
            Análise de sazonalidade
        """
        try:
            if isinstance(df, pl.DataFrame):
                pdf = df.to_pandas()
            else:
                pdf = df

            pdf[date_column] = pd.to_datetime(pdf[date_column])

            # Agrupa por dia da semana
            pdf['day_of_week'] = pdf[date_column].dt.dayofweek
            by_weekday = pdf.groupby('day_of_week')[metric_column].mean()

            # Agrupa por hora (se houver)
            pdf['hour'] = pdf[date_column].dt.hour
            by_hour = pdf.groupby('hour')[metric_column].mean()

            # Agrupa por mês
            pdf['month'] = pdf[date_column].dt.month
            by_month = pdf.groupby('month')[metric_column].mean()

            weekday_names = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']

            return {
                "metric": metric_column,
                "by_weekday": [
                    {"day": weekday_names[i], "average": float(by_weekday.get(i, 0))}
                    for i in range(7)
                ],
                "by_hour": [
                    {"hour": int(h), "average": float(avg)}
                    for h, avg in by_hour.items()
                ],
                "by_month": [
                    {"month": int(m), "average": float(avg)}
                    for m, avg in by_month.items()
                ],
                "best_weekday": weekday_names[int(by_weekday.idxmax())] if len(by_weekday) > 0 else None,
                "best_hour": int(by_hour.idxmax()) if len(by_hour) > 0 else None,
                "best_month": int(by_month.idxmax()) if len(by_month) > 0 else None
            }

        except Exception as e:
            logger.error(f"Erro na análise sazonal: {e}")
            return {"error": str(e)}

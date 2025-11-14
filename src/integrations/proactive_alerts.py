"""
Sistema de Alertas Proativos
Status: EM DESENVOLVIMENTO - Aguardando integração com Dashboard e WhatsApp

Funcionalidades:
- Monitoramento contínuo de métricas
- Detecção de anomalias
- Alertas de threshold
- Alertas preditivos
- Envio via Dashboard e WhatsApp
"""
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import threading
import time

from src.integrations.dashboard_connector import DashboardConnector
from src.integrations.whatsapp_connector import WhatsAppConnector
from src.data.parquet_processor import ParquetProcessor
from src.analytics.predictions import PredictionsEngine

logger = logging.getLogger(__name__)


class ProactiveAlerts:
    """
    Sistema de alertas proativos

    STATUS: EM DESENVOLVIMENTO

    TODO: Configurar regras de monitoramento
    - Definir thresholds por métrica
    - Configurar destinatários
    - Implementar scheduler para checks periódicos
    """

    def __init__(self, parquet_processor: ParquetProcessor,
                dashboard_connector: Optional[DashboardConnector] = None,
                whatsapp_connector: Optional[WhatsAppConnector] = None):
        """
        Inicializa sistema de alertas proativos

        Args:
            parquet_processor: Processador de dados
            dashboard_connector: Conector do dashboard
            whatsapp_connector: Conector do WhatsApp
        """
        self.parquet_processor = parquet_processor
        self.dashboard = dashboard_connector or DashboardConnector()
        self.whatsapp = whatsapp_connector or WhatsAppConnector()
        self.predictions = PredictionsEngine()

        # Regras de alerta (configuráveis)
        self.alert_rules = []
        self.enabled = False
        self.monitoring_thread = None
        self.stop_monitoring = threading.Event()

        # Configurações padrão
        self.check_interval = 300  # 5 minutos
        self.alert_history = []

        logger.info("ProactiveAlerts inicializado [EM DESENVOLVIMENTO]")

    def add_threshold_rule(self, metric: str, threshold_value: float,
                          condition: str = "above", unidade: Optional[str] = None,
                          operacao: Optional[str] = None,
                          alert_title: Optional[str] = None,
                          severity: str = "warning") -> None:
        """
        Adiciona regra de threshold

        Args:
            metric: Nome da métrica a monitorar
            threshold_value: Valor do threshold
            condition: Condição ("above", "below", "equals")
            unidade: Filtro por unidade
            operacao: Filtro por operação
            alert_title: Título personalizado do alerta
            severity: Severidade (info, warning, error, critical)
        """
        rule = {
            "type": "threshold",
            "metric": metric,
            "threshold": threshold_value,
            "condition": condition,
            "unidade": unidade,
            "operacao": operacao,
            "alert_title": alert_title or f"Threshold Alert: {metric}",
            "severity": severity,
            "enabled": True
        }

        self.alert_rules.append(rule)

        logger.info(
            f"Regra de threshold adicionada: {metric} {condition} {threshold_value}"
        )

    def add_anomaly_detection_rule(self, metric: str, sensitivity: float = 2.0,
                                   unidade: Optional[str] = None,
                                   operacao: Optional[str] = None,
                                   alert_title: Optional[str] = None) -> None:
        """
        Adiciona regra de detecção de anomalias

        Args:
            metric: Nome da métrica a monitorar
            sensitivity: Sensibilidade (número de desvios padrão)
            unidade: Filtro por unidade
            operacao: Filtro por operação
            alert_title: Título personalizado
        """
        rule = {
            "type": "anomaly",
            "metric": metric,
            "sensitivity": sensitivity,
            "unidade": unidade,
            "operacao": operacao,
            "alert_title": alert_title or f"Anomaly Detected: {metric}",
            "severity": "warning",
            "enabled": True
        }

        self.alert_rules.append(rule)

        logger.info(
            f"Regra de anomalia adicionada: {metric} (sensitivity={sensitivity})"
        )

    def add_prediction_rule(self, metric: str, days_ahead: int = 7,
                           threshold_value: Optional[float] = None,
                           condition: str = "above",
                           unidade: Optional[str] = None,
                           operacao: Optional[str] = None,
                           alert_title: Optional[str] = None) -> None:
        """
        Adiciona regra de alerta preditivo

        Args:
            metric: Nome da métrica
            days_ahead: Dias à frente para prever
            threshold_value: Threshold na previsão
            condition: Condição do threshold
            unidade: Filtro por unidade
            operacao: Filtro por operação
            alert_title: Título personalizado
        """
        rule = {
            "type": "prediction",
            "metric": metric,
            "days_ahead": days_ahead,
            "threshold": threshold_value,
            "condition": condition,
            "unidade": unidade,
            "operacao": operacao,
            "alert_title": alert_title or f"Prediction Alert: {metric}",
            "severity": "info",
            "enabled": True
        }

        self.alert_rules.append(rule)

        logger.info(
            f"Regra preditiva adicionada: {metric} ({days_ahead} dias)"
        )

    def check_rules(self) -> List[Dict[str, Any]]:
        """
        Verifica todas as regras e retorna alertas

        Returns:
            Lista de alertas gerados

        TODO: Otimizar queries de dados
        """
        alerts = []

        for rule in self.alert_rules:
            if not rule.get("enabled", True):
                continue

            try:
                if rule["type"] == "threshold":
                    alert = self._check_threshold_rule(rule)
                elif rule["type"] == "anomaly":
                    alert = self._check_anomaly_rule(rule)
                elif rule["type"] == "prediction":
                    alert = self._check_prediction_rule(rule)
                else:
                    logger.warning(f"Tipo de regra desconhecido: {rule['type']}")
                    continue

                if alert:
                    alerts.append(alert)

            except Exception as e:
                logger.error(f"Erro ao verificar regra: {e}")
                continue

        return alerts

    def _check_threshold_rule(self, rule: Dict) -> Optional[Dict]:
        """Verifica regra de threshold"""
        # Busca dados
        files = self.parquet_processor.find_relevant_files(
            query=rule["metric"],
            operation=rule.get("operacao"),
            unit=rule.get("unidade")
        )

        if not files:
            return None

        filters = {}
        if rule.get("unidade"):
            filters["unidade"] = rule["unidade"]
        if rule.get("operacao"):
            filters["operacao"] = rule["operacao"]

        # Pega dados recentes (últimas 24h)
        filters["data_inicio"] = datetime.now() - timedelta(days=1)
        filters["data_fim"] = datetime.now()

        df = self.parquet_processor.query_data(files, filters)

        if df is None or len(df) == 0:
            return None

        # Calcula valor atual
        metric_col = rule["metric"]
        if metric_col not in df.columns:
            return None

        current_value = df[metric_col].mean()
        threshold = rule["threshold"]
        condition = rule["condition"]

        # Verifica condição
        triggered = False
        if condition == "above" and current_value > threshold:
            triggered = True
        elif condition == "below" and current_value < threshold:
            triggered = True
        elif condition == "equals" and abs(current_value - threshold) < 0.01:
            triggered = True

        if triggered:
            message = (
                f"Métrica {metric_col} está {current_value:.2f}, "
                f"{condition} threshold de {threshold:.2f}"
            )

            return {
                "type": "threshold",
                "title": rule["alert_title"],
                "message": message,
                "severity": rule["severity"],
                "metric": metric_col,
                "current_value": float(current_value),
                "threshold": threshold,
                "condition": condition
            }

        return None

    def _check_anomaly_rule(self, rule: Dict) -> Optional[Dict]:
        """Verifica regra de anomalia"""
        # Busca dados históricos
        files = self.parquet_processor.find_relevant_files(
            query=rule["metric"],
            operation=rule.get("operacao"),
            unit=rule.get("unidade")
        )

        if not files:
            return None

        filters = {}
        if rule.get("unidade"):
            filters["unidade"] = rule["unidade"]
        if rule.get("operacao"):
            filters["operacao"] = rule["operacao"]

        df = self.parquet_processor.query_data(files, filters)

        if df is None or len(df) == 0:
            return None

        # Detecta anomalias
        anomalies = self.predictions.detect_anomalies(
            df=df,
            metric_column=rule["metric"],
            threshold=rule["sensitivity"]
        )

        if anomalies:
            # Pega anomalia mais recente/significativa
            top_anomaly = anomalies[0]

            message = (
                f"Anomalia detectada em {rule['metric']}: "
                f"Valor {top_anomaly['value']:.2f} "
                f"({top_anomaly['type']}, z-score: {top_anomaly['z_score']:.2f})"
            )

            return {
                "type": "anomaly",
                "title": rule["alert_title"],
                "message": message,
                "severity": rule["severity"],
                "metric": rule["metric"],
                "anomaly_details": top_anomaly
            }

        return None

    def _check_prediction_rule(self, rule: Dict) -> Optional[Dict]:
        """Verifica regra preditiva"""
        # Busca dados históricos
        files = self.parquet_processor.find_relevant_files(
            query=rule["metric"],
            operation=rule.get("operacao"),
            unit=rule.get("unidade")
        )

        if not files:
            return None

        filters = {}
        if rule.get("unidade"):
            filters["unidade"] = rule["unidade"]
        if rule.get("operacao"):
            filters["operacao"] = rule["operacao"]

        df = self.parquet_processor.query_data(files, filters)

        if df is None or len(df) == 0:
            return None

        # Gera previsão
        prediction = self.predictions.predict_next_values(
            df=df,
            metric_column=rule["metric"],
            periods=rule["days_ahead"]
        )

        if "error" in prediction:
            return None

        # Verifica se previsão ultrapassa threshold
        if rule.get("threshold"):
            forecast = prediction.get("forecast", [])
            threshold = rule["threshold"]
            condition = rule["condition"]

            for day_pred in forecast:
                value = day_pred["predicted_value"]

                triggered = False
                if condition == "above" and value > threshold:
                    triggered = True
                elif condition == "below" and value < threshold:
                    triggered = True

                if triggered:
                    message = (
                        f"Previsão para {rule['metric']} indica que em "
                        f"{day_pred['date'][:10]} o valor será {value:.2f}, "
                        f"{condition} threshold de {threshold:.2f}"
                    )

                    return {
                        "type": "prediction",
                        "title": rule["alert_title"],
                        "message": message,
                        "severity": rule["severity"],
                        "metric": rule["metric"],
                        "prediction": day_pred
                    }

        return None

    def send_alert(self, alert: Dict[str, Any],
                  phone_numbers: Optional[List[str]] = None) -> None:
        """
        Envia alerta via Dashboard e WhatsApp

        Args:
            alert: Dados do alerta
            phone_numbers: Números para WhatsApp (opcional)
        """
        # Envia para dashboard
        self.dashboard.send_alert(
            alert_type=alert["type"],
            title=alert["title"],
            message=alert["message"],
            severity=alert.get("severity", "info"),
            metadata=alert
        )

        # Envia para WhatsApp se números fornecidos
        if phone_numbers:
            self.whatsapp.send_alert(
                phone_numbers=phone_numbers,
                alert_title=alert["title"],
                alert_message=alert["message"],
                severity=alert.get("severity", "info")
            )

        # Salva no histórico
        alert["timestamp"] = datetime.now().isoformat()
        self.alert_history.append(alert)

        logger.info(f"Alerta enviado: {alert['title']}")

    def start_monitoring(self, interval: int = 300) -> None:
        """
        Inicia monitoramento contínuo

        Args:
            interval: Intervalo de verificação em segundos (padrão: 5 min)

        TODO: Implementar com scheduler robusto (APScheduler)
        """
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            logger.warning("Monitoramento já está ativo")
            return

        self.check_interval = interval
        self.stop_monitoring.clear()
        self.enabled = True

        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()

        logger.info(f"Monitoramento iniciado (intervalo: {interval}s)")

    def stop_monitoring(self) -> None:
        """Para monitoramento"""
        if not self.monitoring_thread or not self.monitoring_thread.is_alive():
            logger.warning("Monitoramento não está ativo")
            return

        self.stop_monitoring.set()
        self.enabled = False

        logger.info("Monitoramento parado")

    def _monitoring_loop(self) -> None:
        """Loop de monitoramento (roda em thread separada)"""
        logger.info("Loop de monitoramento iniciado")

        while not self.stop_monitoring.is_set():
            try:
                # Verifica regras
                alerts = self.check_rules()

                # Envia alertas (aqui você pode definir destinatários)
                for alert in alerts:
                    # TODO: Configurar destinatários por tipo de alerta
                    self.send_alert(alert)

            except Exception as e:
                logger.error(f"Erro no loop de monitoramento: {e}")

            # Aguarda próximo ciclo
            self.stop_monitoring.wait(self.check_interval)

        logger.info("Loop de monitoramento finalizado")

    def get_alert_history(self, limit: int = 50) -> List[Dict]:
        """Retorna histórico de alertas"""
        return self.alert_history[-limit:]

    def clear_history(self) -> None:
        """Limpa histórico de alertas"""
        self.alert_history.clear()
        logger.info("Histórico de alertas limpo")

    def get_status(self) -> Dict[str, Any]:
        """Retorna status do sistema de alertas"""
        return {
            "enabled": self.enabled,
            "monitoring": self.monitoring_thread.is_alive() if self.monitoring_thread else False,
            "check_interval": self.check_interval,
            "active_rules": len([r for r in self.alert_rules if r.get("enabled")]),
            "total_rules": len(self.alert_rules),
            "alerts_sent": len(self.alert_history),
            "dashboard_status": self.dashboard.get_status(),
            "whatsapp_status": self.whatsapp.get_status(),
            "note": "Integration in development - Configure dashboard and WhatsApp connections"
        }

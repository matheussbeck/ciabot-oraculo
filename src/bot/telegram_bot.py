"""
Bot do Telegram - CIABot Oráculo
"""
import logging
from typing import Optional, Dict, List
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from config.settings import TELEGRAM_TOKEN, ALLOWED_USER_IDS
from src.ai.intelligence_engine import IntelligenceEngine
from src.data.parquet_processor import ParquetProcessor
from src.reports.pdf_generator import PDFGenerator
from src.reports.report_finder import ReportFinder

logger = logging.getLogger(__name__)


class TelegramBot:
    """Bot do Telegram para interface C-Level"""

    def __init__(self):
        self.token = TELEGRAM_TOKEN
        self.allowed_users = set(ALLOWED_USER_IDS) if ALLOWED_USER_IDS else set()

        # Inicializa componentes
        self.parquet_processor = ParquetProcessor()
        self.intelligence_engine = IntelligenceEngine(self.parquet_processor)
        self.pdf_generator = PDFGenerator()
        self.report_finder = ReportFinder()  # Novo: busca relatórios Power BI

        # Application do bot
        self.application = None

        logger.info("TelegramBot inicializado")

    def _is_authorized(self, user_id: int) -> bool:
        """Verifica se usuário está autorizado"""
        if not self.allowed_users:
            return True  # Se não há restrição, permite todos
        return user_id in self.allowed_users

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler do comando /start"""
        user_id = update.effective_user.id

        if not self._is_authorized(user_id):
            await update.message.reply_text(
                "⛔ Acesso não autorizado.\n"
                "Este bot é restrito a executivos autorizados."
            )
            logger.warning(f"Tentativa de acesso não autorizada: {user_id}")
            return

        welcome_message = """
🤖 **CIABot Oráculo**

Bem-vindo ao sistema de inteligência para operações agrícolas.

**O que posso fazer:**
- Responder perguntas sobre operações (plantio, corte, transporte)
- Gerar relatórios em PDF
- Fornecer análises com alto nível de confiança (mínimo 90%)

**Exemplos de perguntas:**
- "Quantos hectares a unidade Barra plantou ontem?"
- "Me envie o relatório de plantio dos últimos 7 dias da Barra"
- "Qual foi a produção de corte da Piacatu este mês?"

**Comandos disponíveis:**
/start - Exibe esta mensagem
/ajuda - Mostra exemplos de uso
/status - Status do sistema
/refresh - Atualiza base de dados

**Importante:** Só respondo quando tenho 90% ou mais de certeza.
Se não souber, vou admitir claramente.
        """

        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        logger.info(f"Usuário {user_id} iniciou o bot")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler do comando /ajuda"""
        user_id = update.effective_user.id

        if not self._is_authorized(user_id):
            return

        help_message = """
📚 **Exemplos de Uso**

**Consultas de Métricas:**
- "Quantos hectares a Barra plantou ontem?"
- "Qual o total de corte da Piacatu nos últimos 7 dias?"
- "Quantas toneladas foram transportadas hoje?"

**Relatórios:**
- "Me envie o relatório de plantio da Barra"
- "Gerar relatório hora a hora do corte de ontem"
- "Relatório completo da safra da Univalem"

**Análises:**
- "Compare o plantio da Barra e Piacatu este mês"
- "Evolução do corte nos últimos 30 dias"

**Dicas:**
- Sempre especifique a unidade (Barra, Piacatu, etc)
- Indique o período (ontem, últimos 7 dias, mês, safra)
- Mencione a operação (plantio, corte, transporte, carregamento)
        """

        await update.message.reply_text(help_message, parse_mode='Markdown')

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler do comando /status"""
        user_id = update.effective_user.id

        if not self._is_authorized(user_id):
            return

        # Coleta informações de status
        total_files = len(self.parquet_processor.file_index)
        metrics = self.parquet_processor.get_available_metrics()

        status_message = f"""
📊 **Status do Sistema**

✅ Sistema operacional

**Dados:**
- Arquivos Parquet indexados: {total_files}
- Métricas disponíveis: {len(metrics)}

**Métricas monitoradas:**
{', '.join(metrics[:10]) if metrics else 'Nenhuma métrica encontrada'}

**IA:**
- Modelo: Claude Sonnet 3.5
- Threshold de confiança: 90%
- Status: Ativo

Última atualização: Agora
        """

        await update.message.reply_text(status_message, parse_mode='Markdown')
        logger.info(f"Status solicitado por {user_id}")

    async def refresh_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler do comando /refresh"""
        user_id = update.effective_user.id

        if not self._is_authorized(user_id):
            return

        await update.message.reply_text("🔄 Atualizando base de dados...")

        # Atualiza índice de arquivos Parquet
        self.parquet_processor.refresh_index()
        total_files = len(self.parquet_processor.file_index)

        # Atualiza índice de relatórios Power BI
        self.report_finder.refresh_index()
        total_reports = len(self.report_finder.report_index)

        await update.message.reply_text(
            f"✅ Base de dados atualizada!\n\n"
            f"📊 Arquivos Parquet: {total_files}\n"
            f"📄 Relatórios Power BI: {total_reports}"
        )

        logger.info(f"Refresh executado por {user_id}")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler de mensagens de texto"""
        user_id = update.effective_user.id
        user_query = update.message.text

        if not self._is_authorized(user_id):
            await update.message.reply_text(
                "⛔ Acesso não autorizado."
            )
            return

        logger.info(f"Query de {user_id}: {user_query}")

        # Envia indicador de digitação
        await update.message.chat.send_action(action="typing")

        try:
            # Processa a consulta
            result = self.intelligence_engine.process_query(
                user_query,
                user_context={"user_id": user_id}
            )

            # Envia resposta
            if result["success"]:
                await update.message.reply_text(
                    result["response"],
                    parse_mode='Markdown'
                )

                # Se requer relatório, gera e envia PDF
                if result.get("requires_report", False):
                    await self._generate_and_send_report(update, result)

            else:
                await update.message.reply_text(
                    result["response"],
                    parse_mode='Markdown'
                )

        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ Desculpe, ocorreu um erro ao processar sua consulta.\n"
                "Por favor, tente reformular a pergunta."
            )

    async def _generate_and_send_report(self, update: Update, result: Dict) -> None:
        """Busca relatório existente ou gera novo se necessário"""
        params = result.get("params", {})
        query = params.get("query", "")

        # Verifica se é um relatório comparativo (precisa gerar novo)
        is_comparative = any(term in query.lower() for term in [
            'comparar', 'comparativo', 'versus', 'vs', 'diferença', 'entre'
        ])

        if not is_comparative:
            # Tenta buscar relatório existente primeiro
            await update.message.reply_text("📄 Buscando relatório...")

            existing_reports = self.report_finder.find_reports(
                query=query,
                unidade=params.get("unidade"),
                operacao=params.get("operacao"),
                limite=3
            )

            if existing_reports:
                # Envia o(s) relatório(s) encontrado(s)
                await self._send_existing_reports(update, existing_reports)
                return

            # Se não encontrou, avisa que vai gerar um novo
            await update.message.reply_text(
                "ℹ️ Não encontrei relatório pronto. Vou gerar um customizado..."
            )

        else:
            await update.message.reply_text("📊 Gerando relatório comparativo...")

        # Gera relatório novo
        try:
            files = self.parquet_processor.find_relevant_files(
                query=params["query"],
                operation=params.get("operacao"),
                unit=params.get("unidade")
            )

            if not files:
                await update.message.reply_text(
                    "⚠️ Não foi possível gerar o relatório: dados não encontrados."
                )
                return

            # Monta filtros
            filters = {}
            if params.get("data_inicio"):
                filters["data_inicio"] = params["data_inicio"]
            if params.get("data_fim"):
                filters["data_fim"] = params["data_fim"]
            if params.get("unidade"):
                filters["unidade"] = params["unidade"]
            if params.get("operacao"):
                filters["operacao"] = params["operacao"]

            # Consulta dados
            df = self.parquet_processor.query_data(files, filters)

            if df is None or len(df) == 0:
                await update.message.reply_text(
                    "⚠️ Não há dados suficientes para gerar o relatório."
                )
                return

            # Determina tipo de relatório
            report_type = "detailed"
            if "hora a hora" in params["query"].lower():
                report_type = "hourly"

            # Gera PDF
            pdf_path = self.pdf_generator.generate_report(df, params, report_type)

            if pdf_path and pdf_path.exists():
                # Envia PDF
                await update.message.reply_document(
                    document=open(pdf_path, 'rb'),
                    filename=pdf_path.name,
                    caption=f"✅ Relatório gerado com sucesso!\n\n"
                           f"📊 {len(df)} registros incluídos"
                )

                logger.info(f"Relatório enviado: {pdf_path.name}")
            else:
                await update.message.reply_text(
                    "❌ Erro ao gerar relatório PDF."
                )

        except Exception as e:
            logger.error(f"Erro ao gerar/enviar relatório: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ Erro ao gerar relatório. Tente novamente."
            )

    async def _send_existing_reports(self, update: Update, reports: List[Dict]) -> None:
        """Envia relatórios existentes encontrados"""
        try:
            if len(reports) == 1:
                # Envia único relatório
                report = reports[0]
                await update.message.reply_text(
                    f"✅ Encontrei o relatório:\n\n"
                    f"📄 **{report['name']}**\n"
                    f"📅 Última atualização: {report['modified'].strftime('%d/%m/%Y %H:%M')}\n"
                    f"📊 Tamanho: {report['size'] / 1024:.1f} KB"
                )

                with open(report['path'], 'rb') as pdf_file:
                    await update.message.reply_document(
                        document=pdf_file,
                        filename=f"{report['name']}.pdf",
                        caption=f"📊 Relatório: {report['name']}"
                    )

                logger.info(f"Relatório existente enviado: {report['name']}")

            else:
                # Múltiplos relatórios encontrados - oferece opções
                message = "📚 Encontrei os seguintes relatórios:\n\n"

                for i, report in enumerate(reports[:3], 1):
                    message += f"{i}. **{report['name']}**\n"
                    message += f"   📅 {report['modified'].strftime('%d/%m/%Y %H:%M')}\n"
                    message += f"   📊 {report['size'] / 1024:.1f} KB\n\n"

                message += "Enviando o mais relevante..."

                await update.message.reply_text(message, parse_mode='Markdown')

                # Envia o mais relevante
                best_report = reports[0]
                with open(best_report['path'], 'rb') as pdf_file:
                    await update.message.reply_document(
                        document=pdf_file,
                        filename=f"{best_report['name']}.pdf",
                        caption=f"📊 Relatório: {best_report['name']}"
                    )

                logger.info(f"Relatório existente enviado: {best_report['name']}")

        except Exception as e:
            logger.error(f"Erro ao enviar relatório existente: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ Erro ao enviar o relatório. Vou tentar gerar um novo."
            )

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler de erros"""
        logger.error(f"Exception while handling an update: {context.error}", exc_info=True)

    def run(self) -> None:
        """Inicia o bot"""
        if not self.token:
            raise ValueError("TELEGRAM_TOKEN não configurado!")

        logger.info("Iniciando bot do Telegram...")

        # Cria application
        self.application = Application.builder().token(self.token).build()

        # Registra handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("ajuda", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("refresh", self.refresh_command))

        # Handler de mensagens
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

        # Handler de erros
        self.application.add_error_handler(self.error_handler)

        # Inicia polling
        logger.info("Bot iniciado e aguardando mensagens...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

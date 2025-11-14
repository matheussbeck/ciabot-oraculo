"""
Sistema de Backup Automático
Faz backup de dados críticos periodicamente
"""
import logging
import shutil
import tarfile
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import json

from config.settings import DATA_DIR, BASE_DIR

logger = logging.getLogger(__name__)


class BackupManager:
    """Gerenciador de backups automáticos"""

    def __init__(self, backup_dir: Optional[Path] = None):
        """
        Inicializa backup manager

        Args:
            backup_dir: Diretório para armazenar backups
        """
        self.backup_dir = backup_dir or (BASE_DIR / "backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"BackupManager inicializado: {self.backup_dir}")

    def create_backup(self, include_parquet: bool = False,
                     include_reports: bool = False,
                     include_learning: bool = True) -> Optional[Path]:
        """
        Cria backup completo

        Args:
            include_parquet: Incluir arquivos Parquet (pode ser grande!)
            include_reports: Incluir relatórios PDF
            include_learning: Incluir dados de aprendizado

        Returns:
            Caminho do arquivo de backup criado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"ciabot_backup_{timestamp}.tar.gz"
        backup_path = self.backup_dir / backup_name

        logger.info(f"Criando backup: {backup_name}")

        try:
            with tarfile.open(backup_path, "w:gz") as tar:

                # Config
                if (BASE_DIR / ".env").exists():
                    tar.add(BASE_DIR / ".env", arcname=".env")
                    logger.debug("Backup: .env")

                # Learning data
                if include_learning:
                    learning_dir = DATA_DIR / "learning"
                    if learning_dir.exists():
                        tar.add(learning_dir, arcname="learning")
                        logger.debug("Backup: learning data")

                # Vector DB
                vector_dir = DATA_DIR / "vector_db"
                if vector_dir.exists():
                    tar.add(vector_dir, arcname="vector_db")
                    logger.debug("Backup: vector DB")

                # WhatsApp messages DB
                whatsapp_db = DATA_DIR / "whatsapp_messages.db"
                if whatsapp_db.exists():
                    tar.add(whatsapp_db, arcname="whatsapp_messages.db")
                    logger.debug("Backup: WhatsApp DB")

                # Dashboard alerts
                alerts_dir = DATA_DIR / "dashboard_alerts"
                if alerts_dir.exists():
                    tar.add(alerts_dir, arcname="dashboard_alerts")
                    logger.debug("Backup: Dashboard alerts")

                # Parquet files (opcional - pode ser grande)
                if include_parquet:
                    parquet_dir = DATA_DIR / "parquet"
                    if parquet_dir.exists():
                        tar.add(parquet_dir, arcname="parquet")
                        logger.debug("Backup: Parquet files")

                # Reports (opcional)
                if include_reports:
                    reports_dir = DATA_DIR / "reports"
                    if reports_dir.exists():
                        tar.add(reports_dir, arcname="reports")
                        logger.debug("Backup: Reports")

                    powerbi_dir = DATA_DIR / "powerbi_reports"
                    if powerbi_dir.exists():
                        tar.add(powerbi_dir, arcname="powerbi_reports")
                        logger.debug("Backup: PowerBI reports")

                # Metadata
                metadata = {
                    "created_at": datetime.now().isoformat(),
                    "version": "1.0.0",
                    "include_parquet": include_parquet,
                    "include_reports": include_reports,
                    "include_learning": include_learning
                }

                # Salva metadata em arquivo temporário
                temp_meta = self.backup_dir / "metadata.json"
                with open(temp_meta, 'w') as f:
                    json.dump(metadata, f, indent=2)

                tar.add(temp_meta, arcname="metadata.json")
                temp_meta.unlink()  # Remove arquivo temporário

            size_mb = backup_path.stat().st_size / (1024 * 1024)
            logger.info(f"Backup criado com sucesso: {backup_name} ({size_mb:.2f} MB)")

            return backup_path

        except Exception as e:
            logger.error(f"Erro ao criar backup: {e}")
            if backup_path.exists():
                backup_path.unlink()
            return None

    def restore_backup(self, backup_path: Path, force: bool = False) -> bool:
        """
        Restaura backup

        Args:
            backup_path: Caminho do arquivo de backup
            force: Se True, sobrescreve arquivos existentes

        Returns:
            True se restaurado com sucesso
        """
        if not backup_path.exists():
            logger.error(f"Backup não encontrado: {backup_path}")
            return False

        if not force:
            logger.warning("Use force=True para confirmar restauração")
            return False

        logger.info(f"Restaurando backup: {backup_path.name}")

        try:
            with tarfile.open(backup_path, "r:gz") as tar:
                # Extrai para diretório temporário primeiro
                temp_dir = self.backup_dir / "temp_restore"
                temp_dir.mkdir(parents=True, exist_ok=True)

                tar.extractall(temp_dir)

                # Move arquivos para locais corretos
                if (temp_dir / "learning").exists():
                    shutil.rmtree(DATA_DIR / "learning", ignore_errors=True)
                    shutil.move(str(temp_dir / "learning"), str(DATA_DIR / "learning"))

                if (temp_dir / "vector_db").exists():
                    shutil.rmtree(DATA_DIR / "vector_db", ignore_errors=True)
                    shutil.move(str(temp_dir / "vector_db"), str(DATA_DIR / "vector_db"))

                if (temp_dir / "whatsapp_messages.db").exists():
                    (DATA_DIR / "whatsapp_messages.db").unlink(missing_ok=True)
                    shutil.move(
                        str(temp_dir / "whatsapp_messages.db"),
                        str(DATA_DIR / "whatsapp_messages.db")
                    )

                # Limpa temporário
                shutil.rmtree(temp_dir)

                logger.info(f"Backup restaurado com sucesso: {backup_path.name}")
                return True

        except Exception as e:
            logger.error(f"Erro ao restaurar backup: {e}")
            return False

    def list_backups(self) -> List[Dict[str, any]]:
        """Lista todos os backups disponíveis"""
        backups = []

        for backup_file in self.backup_dir.glob("ciabot_backup_*.tar.gz"):
            stat = backup_file.stat()

            backups.append({
                "name": backup_file.name,
                "path": str(backup_file),
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })

        return sorted(backups, key=lambda x: x['created'], reverse=True)

    def delete_old_backups(self, keep_last: int = 5) -> int:
        """
        Remove backups antigos, mantendo apenas os N mais recentes

        Args:
            keep_last: Número de backups a manter

        Returns:
            Número de backups removidos
        """
        backups = self.list_backups()

        if len(backups) <= keep_last:
            return 0

        backups_to_delete = backups[keep_last:]
        deleted = 0

        for backup in backups_to_delete:
            try:
                Path(backup['path']).unlink()
                deleted += 1
                logger.info(f"Backup antigo removido: {backup['name']}")
            except Exception as e:
                logger.error(f"Erro ao remover backup: {e}")

        return deleted

    def get_backup_size(self) -> float:
        """Retorna tamanho total dos backups em MB"""
        total_size = sum(
            f.stat().st_size
            for f in self.backup_dir.glob("ciabot_backup_*.tar.gz")
        )
        return round(total_size / (1024 * 1024), 2)

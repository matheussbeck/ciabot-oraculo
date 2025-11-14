#!/usr/bin/env python3
"""
Script para gerar dados de exemplo para o CIABot Oráculo

Execute: python scripts/generate_sample_data.py
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Adiciona diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import PARQUET_DIR


def generate_plantio_data(unidade: str, days: int = 30) -> pd.DataFrame:
    """Gera dados de exemplo de plantio"""

    data = []
    base_date = datetime.now() - timedelta(days=days)

    equipamentos = [f'PL-{i:03d}' for i in range(1, 6)]
    turnos = ['diurno', 'noturno']
    frentes = ['Frente A', 'Frente B', 'Frente C']

    for day in range(days):
        current_date = base_date + timedelta(days=day)

        # 3-8 registros por dia
        num_records = np.random.randint(3, 9)

        for _ in range(num_records):
            hora = np.random.randint(6, 23)

            data.append({
                'data': current_date.replace(hour=hora, minute=np.random.randint(0, 60)),
                'unidade': unidade,
                'operacao': 'plantio',
                'hectares': round(np.random.uniform(3.5, 12.5), 2),
                'mudas_plantadas': np.random.randint(5000, 15000),
                'equipamento': np.random.choice(equipamentos),
                'turno': 'diurno' if 6 <= hora < 18 else 'noturno',
                'frente': np.random.choice(frentes),
                'operador': f'OP-{np.random.randint(100, 999)}',
                'talhao': f'T-{np.random.randint(1, 50):03d}',
                'variedade_cana': np.random.choice(['RB92579', 'RB867515', 'SP81-3250']),
                'qualidade': np.random.choice(['Excelente', 'Boa', 'Regular'])
            })

    return pd.DataFrame(data)


def generate_corte_data(unidade: str, days: int = 30) -> pd.DataFrame:
    """Gera dados de exemplo de corte"""

    data = []
    base_date = datetime.now() - timedelta(days=days)

    equipamentos = [f'CT-{i:03d}' for i in range(1, 8)]
    turnos = ['diurno', 'noturno']
    frentes = ['Frente A', 'Frente B', 'Frente C', 'Frente D']

    for day in range(days):
        current_date = base_date + timedelta(days=day)

        # 5-15 registros por dia (corte é mais intenso)
        num_records = np.random.randint(5, 16)

        for _ in range(num_records):
            hora = np.random.randint(6, 23)
            hectares_cortados = round(np.random.uniform(2.0, 8.5), 2)

            data.append({
                'data': current_date.replace(hour=hora, minute=np.random.randint(0, 60)),
                'unidade': unidade,
                'operacao': 'corte',
                'hectares': hectares_cortados,
                'toneladas': round(hectares_cortados * np.random.uniform(70, 95), 2),
                'equipamento': np.random.choice(equipamentos),
                'turno': 'diurno' if 6 <= hora < 18 else 'noturno',
                'frente': np.random.choice(frentes),
                'operador': f'OP-{np.random.randint(100, 999)}',
                'talhao': f'T-{np.random.randint(1, 50):03d}',
                'atrs': round(np.random.uniform(130, 160), 2),  # ATR (kg/tonelada)
                'impurezas': round(np.random.uniform(1.5, 8.5), 2),
                'qualidade': np.random.choice(['Excelente', 'Boa', 'Regular'])
            })

    return pd.DataFrame(data)


def generate_transporte_data(unidade: str, days: int = 30) -> pd.DataFrame:
    """Gera dados de exemplo de transporte"""

    data = []
    base_date = datetime.now() - timedelta(days=days)

    caminhoes = [f'CAM-{i:03d}' for i in range(1, 15)]
    motoristas = [f'MOT-{i:03d}' for i in range(1, 25)]

    for day in range(days):
        current_date = base_date + timedelta(days=day)

        # 10-25 viagens por dia
        num_records = np.random.randint(10, 26)

        for _ in range(num_records):
            hora = np.random.randint(6, 23)
            toneladas = round(np.random.uniform(25, 45), 2)

            data.append({
                'data': current_date.replace(hour=hora, minute=np.random.randint(0, 60)),
                'unidade': unidade,
                'operacao': 'transporte',
                'toneladas': toneladas,
                'viagens': 1,
                'distancia_km': round(np.random.uniform(5.5, 35.8), 2),
                'tempo_viagem_min': np.random.randint(15, 90),
                'equipamento': np.random.choice(caminhoes),
                'motorista': np.random.choice(motoristas),
                'origem': f'Frente {np.random.choice(["A", "B", "C", "D"])}',
                'destino': 'Usina',
                'tipo_carga': 'cana',
                'status': np.random.choice(['Entregue', 'Entregue', 'Entregue', 'Atraso'])
            })

    return pd.DataFrame(data)


def generate_carregamento_data(unidade: str, days: int = 30) -> pd.DataFrame:
    """Gera dados de exemplo de carregamento"""

    data = []
    base_date = datetime.now() - timedelta(days=days)

    carregadeiras = [f'CG-{i:03d}' for i in range(1, 6)]
    frentes = ['Frente A', 'Frente B', 'Frente C', 'Frente D']

    for day in range(days):
        current_date = base_date + timedelta(days=day)

        # 8-20 operações por dia
        num_records = np.random.randint(8, 21)

        for _ in range(num_records):
            hora = np.random.randint(6, 23)
            toneladas = round(np.random.uniform(28, 42), 2)

            data.append({
                'data': current_date.replace(hour=hora, minute=np.random.randint(0, 60)),
                'unidade': unidade,
                'operacao': 'carregamento',
                'toneladas': toneladas,
                'tempo_carregamento_min': np.random.randint(8, 25),
                'equipamento': np.random.choice(carregadeiras),
                'frente': np.random.choice(frentes),
                'operador': f'OP-{np.random.randint(100, 999)}',
                'caminhao': f'CAM-{np.random.randint(1, 15):03d}',
                'eficiencia': round(np.random.uniform(75, 98), 2),
                'status': 'Concluído'
            })

    return pd.DataFrame(data)


def main():
    """Função principal"""
    print("=" * 60)
    print("CIABot Oráculo - Gerador de Dados de Exemplo")
    print("=" * 60)

    # Cria diretório se não existir
    PARQUET_DIR.mkdir(parents=True, exist_ok=True)

    unidades = ['Barra', 'Piacatu', 'Univalem', 'SaoJose']
    days = 60  # 60 dias de dados

    total_files = 0

    for unidade in unidades:
        print(f"\nGerando dados para {unidade}...")

        # Plantio
        print(f"  - Plantio...", end=" ")
        df_plantio = generate_plantio_data(unidade, days)
        file_plantio = PARQUET_DIR / f'plantio_{unidade.lower()}_2024.parquet'
        df_plantio.to_parquet(file_plantio, index=False)
        print(f"✓ ({len(df_plantio)} registros)")
        total_files += 1

        # Corte
        print(f"  - Corte...", end=" ")
        df_corte = generate_corte_data(unidade, days)
        file_corte = PARQUET_DIR / f'corte_{unidade.lower()}_2024.parquet'
        df_corte.to_parquet(file_corte, index=False)
        print(f"✓ ({len(df_corte)} registros)")
        total_files += 1

        # Transporte
        print(f"  - Transporte...", end=" ")
        df_transporte = generate_transporte_data(unidade, days)
        file_transporte = PARQUET_DIR / f'transporte_{unidade.lower()}_2024.parquet'
        df_transporte.to_parquet(file_transporte, index=False)
        print(f"✓ ({len(df_transporte)} registros)")
        total_files += 1

        # Carregamento
        print(f"  - Carregamento...", end=" ")
        df_carregamento = generate_carregamento_data(unidade, days)
        file_carregamento = PARQUET_DIR / f'carregamento_{unidade.lower()}_2024.parquet'
        df_carregamento.to_parquet(file_carregamento, index=False)
        print(f"✓ ({len(df_carregamento)} registros)")
        total_files += 1

    print("\n" + "=" * 60)
    print(f"✅ Concluído! {total_files} arquivos gerados em:")
    print(f"   {PARQUET_DIR}")
    print("=" * 60)
    print("\nPróximos passos:")
    print("1. Configure o arquivo .env com suas credenciais")
    print("2. Execute: python main.py")
    print("3. Acesse seu bot no Telegram")
    print("\nExemplo de pergunta:")
    print('  "Quantos hectares a Barra plantou nos últimos 7 dias?"')
    print("=" * 60)


if __name__ == "__main__":
    main()

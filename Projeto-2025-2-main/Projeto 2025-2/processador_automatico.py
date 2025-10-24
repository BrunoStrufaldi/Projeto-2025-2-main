# processador_automatico.py
#
# ESTE É O SCRIPT "CHEFE"
# Ele junta o Banco de Dados (database_manager.py) 
# com a Inteligência Artificial (detect_desmatamento.py)

import numpy as np
from pathlib import Path
import sys

# --- 1. IMPORTANDO SUAS FERRAMENTAS ---

# Importa as ferramentas do seu Banco de Dados
try:
    from database_manager import get_pending_images, update_image_analysis_result
except ImportError:
    print("[ERRO FATAL] Não foi possível encontrar 'database_manager.py'.")
    print("Verifique se este script está na mesma pasta que ele.")
    sys.exit(1)

# Importa as ferramentas da sua IA
try:
    # Vamos usar a função 'process_image' de dentro do seu script de IA
    from detect_desmatamento import process_image, ensure_dir
except ImportError:
    print("[ERRO FATAL] Não foi possível encontrar 'detect_desmatamento.py'.")
    print("Verifique se este script está na mesma pasta que ele.")
    sys.exit(1)


# --- 2. "TRAVANDO" OS PARÂMETROS DE OURO ---
# (Baseado no seu teste bem-sucedido)

print("Carregando parâmetros de ouro...")

# Limites de Cor (O que define "solo")
LOWER_HSV_FIXO = np.array([0, 20, 20], dtype=np.uint8)
UPPER_HSV_FIXO = np.array([40, 255, 255], dtype=np.uint8)

# Filtro de Vegetação (O que ignora "verde")
USE_EXG_FIXO = True
EXG_THRESH_FIXO = 0.6  # (Este é o valor padrão do script, que funcionou bem)
COMBINE_MODE_FIXO = "and" # (Modo padrão)

# Filtro de Ruído (Área Mínima)
# Seu teste com '0' foi perfeito para essa imagem.
# Se em outras imagens aparecerem "pontinhos", este é o primeiro
# número que você deve aumentar (ex: para 500 ou 1000).
MIN_AREA_FIXO = 500

# Filtros Morfológicos (Padrão do script)
KERNEL_OPEN_FIXO = 3
KERNEL_CLOSE_FIXO = 5

# Pasta para salvar os overlays (imagens vermelhas)
OUTPUT_DIR_FIXO = ensure_dir(Path("resultados_automaticos"))

# Confiança padrão (só para salvar no banco)
CONFIANCA_FIXA = 0.99 # (99% de confiança, já que o resultado foi ótimo)

# --- 3. O PIPELINE DE AUTOMAÇÃO ---

def rodar_pipeline_completo():
    """
    Função principal que roda todo o processo.
    """
    print("="*30)
    print("INICIANDO PIPELINE DE ANÁLISE AUTOMÁTICA")
    print("="*30)
    print("Buscando imagens pendentes no banco de dados...")

    try:
        lista_de_trabalhos = get_pending_images()
    except Exception as e:
        print(f"[ERRO NO BANCO] Não foi possível buscar trabalhos: {e}")
        return

    if not lista_de_trabalhos:
        print("\nNenhum trabalho novo encontrado. Encerrando.")
        return

    print(f"Sucesso! Encontrados {len(lista_de_trabalhos)} trabalhos para processar.")

    # Loop para processar cada imagem da lista
    for trabalho in lista_de_trabalhos:
        image_id = trabalho['id']
        image_path = Path(trabalho['file_path'])

        print(f"\n--- Processando Imagem ID: {image_id} ---")
        print(f"Caminho do arquivo: {image_path}")

        # Checa se o arquivo de imagem realmente existe
        if not image_path.exists():
            print(f"[ERRO] ARQUIVO NÃO ENCONTRADO em: {image_path}")
            # (Opcional: criar uma função para marcar 'erro' no banco)
            continue # Pula para o próximo trabalho

        try:
            # A MÁGICA ACONTECE AQUI!
            # Chamando a função da IA com os parâmetros fixos
            resultados_ia = process_image(
                img_path=image_path,
                out_dir=OUTPUT_DIR_FIXO,
                lower_hsv=LOWER_HSV_FIXO,
                upper_hsv=UPPER_HSV_FIXO,
                kernel_open=KERNEL_OPEN_FIXO,
                kernel_close=KERNEL_CLOSE_FIXO,
                min_component_area=MIN_AREA_FIXO,
                use_exg=USE_EXG_FIXO,
                exg_thresh=EXG_THRESH_FIXO,
                combine_mode=COMBINE_MODE_FIXO,
                save_intermediates=False # Não precisamos mais disso
            )
            
            # Coletando os resultados que a IA calculou
            percentual = resultados_ia.get('percentual', 0.0)
            area_em_pixels = resultados_ia.get('pixels_desmatado', 0)
            
            print(f"Análise concluída. Resultado: {percentual:.4f}% de cobertura.")
            
            # Salvando os resultados de volta no Banco de Dados
            update_image_analysis_result(
                image_id=image_id,
                percentage=percentual,
                area=area_em_pixels,  # (Salvando a área em pixels)
                confidence=CONFIANCA_FIXA
            )
            print(f"Resultados da Imagem ID {image_id} salvos no banco de dados.")

        except Exception as e:
            print(f"[ERRO NA IA] Falha ao processar a Imagem ID {image_id}: {e}")
            # (Opcional: marcar 'erro' no banco)

    print("\n" + "="*30)
    print("PIPELINE CONCLUÍDO. Todos os trabalhos foram processados.")
    print("="*30)

# --- 4. EXECUTAR O SCRIPT ---
if __name__ == "__main__":
    rodar_pipeline_completo()
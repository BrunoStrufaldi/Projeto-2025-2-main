from database_manager import remove_image
import sys

# 1. Pedir os IDs separados por vírgula
id_input = input("Digite os IDs que você quer remover (separados por vírgula): ")

ids_para_deletar = []
try:
    # 2. Limpar a string e converter para uma lista de números
    id_strings = id_input.split(',')
    
    for id_str in id_strings:
        id_num = int(id_str.strip()) # .strip() remove espaços (ex: " 2 ")
        ids_para_deletar.append(id_num)

except ValueError:
    # 3. Falhar se qualquer parte não for um número
    print(f"\n[ERRO] Formato inválido. Use apenas números separados por vírgula (ex: 1, 2, 3).")
    print(f"Você digitou: '{id_input}'.")
    print("Operação cancelada.")
    sys.exit()

# Checa se a lista não está vazia
if not ids_para_deletar:
    print("Nenhum ID fornecido. Operação cancelada.")
    sys.exit()

# 4. Pedir confirmação para o lote todo
print(f"\nAtenção! Você está prestes a remover {len(ids_para_deletar)} imagem(ns):")
print(f"IDs: {ids_para_deletar}")
resposta = input("Você tem certeza? (s/n): ")

if resposta.lower() == 's':
    print("\nIniciando remoção em lote...")
    
    # 5. Criar um laço e remover um por um
    for image_id in ids_para_deletar:
        print(f"--- Processando remoção do ID: {image_id} ---")
        remove_image(image_id) #
    
    print("\nOperação em lote concluída.")
else:
    print("\nOperação cancelada.")
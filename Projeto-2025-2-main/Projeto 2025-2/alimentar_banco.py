# alimentar_banco.py
from database_manager import add_image

# --- CAMINHOS CORRIGIDOS ---

add_image(
    filename="foto_do_drone_01.jpg",
    file_path="images/foto_do_drone_01.jpg", # CORRETO
    capture_date="2025-07-15",
    source="UFLA - Universidade Federal de Lavras"
)

add_image(
    filename="RTEmagicC_desmate-ibama_04.jpg", 
    file_path="images/RTEmagicC_desmate-ibama_04.jpg", # CORRETO
    capture_date="2023-07-20",
    source="Ibama"

)

add_image(
    filename='imagem.jpg',
    file_path='images/imagem.jpg', # CORRETO
    capture_date='2025-07-10',
    source='Internet'

)

add_image(
    filename='download.jpeg',
    file_path='images/download.jpeg',
    capture_date='2025-07-11',
    source='Internet'
)

print("\nProcesso de adição de imagens concluído.")
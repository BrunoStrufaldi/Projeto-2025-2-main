# database_manager.py
import sqlite3
import os
from datetime import datetime

# --- MUDANÇA IMPORTANTE ---
# Pega o caminho absoluto da pasta ONDE ESTE SCRIPT ESTÁ
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Define que o banco de dados deve estar NA MESMA PASTA
DB_FILE = os.path.join(BASE_DIR, "deforestation_monitor.db")
# --- FIM DA MUDANÇA ---

def add_image(filename, file_path, capture_date, source):
    """Adiciona uma nova imagem ao banco de dados com status 'pending'."""
    try:
        # Conecta ao banco de dados no caminho absoluto
        conn = sqlite3.connect(DB_FILE) 
        cursor = conn.cursor()
        sql = """
        INSERT INTO images (filename, file_path, capture_date, source)
        VALUES (?, ?, ?, ?);
        """
        cursor.execute(sql, (filename, file_path, capture_date, source))
        conn.commit()
        print(f"Imagem '{filename}' adicionada à fila para análise.")
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        print(f"Erro: A imagem em '{file_path}' já existe no banco de dados.")
        return None
    finally:
        if conn:
            conn.close()

def get_pending_images():
    """Retorna uma lista de imagens que ainda não foram analisadas."""
    conn = sqlite3.connect(DB_FILE) # Conecta no caminho absoluto
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, file_path FROM images WHERE analysis_status = 'pending';")
    images = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in images]

def update_image_analysis_result(image_id, percentage, area, confidence):
    """Atualiza o registro de uma imagem com os resultados da análise da IA."""
    conn = sqlite3.connect(DB_FILE) # Conecta no caminho absoluto
    cursor = conn.cursor()
    sql = """
    UPDATE images
    SET 
        analysis_status = 'success',
        deforestation_percentage = ?,
        deforestation_area_sqm = ?,
        confidence_score = ?,
        last_updated = ?
    WHERE id = ?;
    """
    now = datetime.now()
    cursor.execute(sql, (percentage, area, confidence, now, image_id))
    conn.commit()
    
    if cursor.rowcount == 0:
        print(f"Aviso: Nenhuma imagem encontrada com ID {image_id} para atualizar.")
    else:
        print(f"Análise da imagem ID {image_id} salva com sucesso.")
        
    conn.close()

def remove_image(image_id):
    """Remove uma imagem do banco de dados e apaga o arquivo físico."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE) # Conecta no caminho absoluto
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT file_path FROM images WHERE id = ?;", (image_id,))
        record = cursor.fetchone()

        if record is None:
            print(f"Erro: Nenhuma imagem encontrada com o ID {image_id}.")
            return

        file_path_to_delete = record['file_path']
        cursor.execute("DELETE FROM images WHERE id = ?;", (image_id,))
        conn.commit()
        print(f"Registro da imagem ID {image_id} removido do banco.")

        if os.path.exists(file_path_to_delete):
            os.remove(file_path_to_delete)
            print(f"Arquivo '{file_path_to_delete}' apagado do disco.")
        else:
            print(f"Aviso: Arquivo '{file_path_to_delete}' não encontrado no disco.")

    except Exception as e:
        print(f"Ocorreu um erro ao tentar remover a imagem: {e}")
    finally:
        if conn:
            conn.close()
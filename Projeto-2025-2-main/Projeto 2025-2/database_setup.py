# database_setup.py
import sqlite3
import os

# --- MUDANÇA IMPORTANTE ---
# Pega o caminho absoluto da pasta ONDE ESTE SCRIPT ESTÁ
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Define que o banco de dados deve estar NA MESMA PASTA
DB_FILE = os.path.join(BASE_DIR, "deforestation_monitor.db")
IMAGE_DIR = os.path.join(BASE_DIR, "images")
# --- FIM DA MUDANÇA ---

def setup_database():
    """
    Cria o banco de dados e a tabela 'images' se eles não existirem.
    """
    if not os.path.exists(IMAGE_DIR):
        print(f"Criando diretório para imagens em: '{IMAGE_DIR}/'")
        os.makedirs(IMAGE_DIR)

    # Conecta ao banco de dados no caminho absoluto
    conn = sqlite3.connect(DB_FILE) 
    cursor = conn.cursor()

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        file_path TEXT NOT NULL UNIQUE,
        capture_date DATE,
        source TEXT,
        
        analysis_status TEXT DEFAULT 'pending',
        deforestation_percentage REAL DEFAULT 0.0,
        deforestation_area_sqm REAL DEFAULT 0.0,
        confidence_score REAL DEFAULT 0.0,
        
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_updated TIMESTAMP
    );
    """
    cursor.execute(create_table_sql)
    print(f"Banco de dados verificado em: {DB_FILE}")
    print("Tabela 'images' está pronta.")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_database()
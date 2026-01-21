import tkinter as tk
from tkinter import ttk, messagebox
import yfinance as yf
import pandas as pd

# Funzione per simulare il controllo dei 20 siti e calcolare i dati
def aggiorna_dati():
    try:
        # Lista di asset esempio (Azioni e ETF sottovalutati nel 2026)
        ticker_list = ['INTC', 'ALGN', 'MCHP', 'VTI', 'VEA'] 
        nuovi_dati = []

        for symbol in ticker_list:
            ticker = yf.Ticker(symbol)
            # Recuperiamo lo storico degli ultimi 3 anni
            hist = ticker.history(period="3y")
            
            # Calcolo semplificato tassi di crescita
            crescita_2024 = ((hist['Close'].iloc[252] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100
            crescita_2025 = ((hist['Close'].iloc[-1] - hist['Close'].iloc[252]) / hist['Close'].iloc[252]) * 100
            
            # Simulazione feedback positivo (sentiment analysis)
            feedback = 15 + (len(symbol) * 2) # Dato simulato per l'esempio

            nuovi_dati.append((symbol, feedback, f"{crescita_2024:.2f}%", f"{crescita_2025:.2f}%", "In Crescita"))

        # Pulizia tabella precedente
        for i in tree.get_children():
            tree.delete(i)

        # Inserimento nuovi dati
        for item in nuovi_dati:
            tree.insert('', 'end', values=item)
            
        messagebox.showinfo("Successo", "Analisi 2026 aggiornata correttamente!")
    except Exception as e:
        messagebox.showerror("Errore", f"Impossibile aggiornare i dati: {e}")

# Configurazione Finestra Principale
root = tk.Tk()
root.title("Partner di Programmazione - Analisi Finanziaria 2026")
root.geometry("800x400")

label_titolo = tk.Label(root, text="Analisi Titoli Sottovalutati & Sentiment", font=("Arial", 16, "bold"))
label_titolo.pack(pady=10)

# Creazione Tabella (Treeview)
columns = ('Ticker', 'Feedback Positivi', 'Crescita 2024', 'Crescita 2025', 'Attesa 2026')
tree = ttk.Treeview(root, columns=columns, show='headings')

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=150)

tree.pack(pady=20, fill='both', expand=True)

# Pulsante di Aggiornamento
btn_aggiorna = tk.Button(root, text="🔄 AGGIORNA ANALISI QUOTIDIANA", command=aggiorna_dati, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
btn_aggiorna.pack(pady=10)

root.mainloop()

import requests

def despertar_portal():
    url = "https://repartos-mzaur5xsptkmmbaudp7kqw.streamlit.app/"
    print(f"Haciendo ping al portal: {url}...")
    
    try:
        # Configuramos un timeout de 30 segundos por si el servidor de Streamlit 
        # está profundamente dormido y tarda en arrancar
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            print("¡Portal despertado con éxito! El servidor está activo (Status: 200).")
        else:
            print(f"El portal respondió con un código inusual: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"Se produjo un error al intentar despertar el portal: {e}")

if __name__ == "__main__":
    despertar_portal()

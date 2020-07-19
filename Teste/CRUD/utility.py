from math import radians, cos, sin, asin, sqrt 
def distance(lat1, lat2, lon1, lon2):
    """Utiliza a Fórmula de Haversine para calcular a distância entre dois pontos, dadas as coordenadas"""
    lon1 = radians(lon1)
    lon2 = radians(lon2)
    lat1 = radians(lat1)
    lat2 = radians(lat2)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    return 2 * asin(sqrt(a))*6371

def sort_key(e):
    """Função de comparação para ordenar as distâncias."""
    return e[2]

def decode_utf8(input_iterator):
    """Função decodificadora para abertura dos arquivos csv"""
    for l in input_iterator:
        yield l.decode('utf-8')
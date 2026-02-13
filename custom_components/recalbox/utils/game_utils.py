

def clean_game_name(raw_game_name:str | None) -> str | None:
    """
    Nettoie le nom d'un jeu, pour un affichage plus naturel :
    s'il commence par 3 chiffres + espaces, on les ignore
    """
    if raw_game_name is None:
        return None
    elif len(raw_game_name) > 4 and raw_game_name[:3].isdigit() and raw_game_name[3] == " ":
        return raw_game_name[4:]
    else:
        return raw_game_name
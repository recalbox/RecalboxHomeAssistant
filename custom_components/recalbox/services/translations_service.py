# translations.py
import json
import os
import random
import logging

_LOGGER = logging.getLogger(__name__)

class RecalboxTranslator:
    def __init__(self, hass, domain):
        self.hass = hass
        self._domain = domain
        self._cache = {}
        self._base_path = hass.config.path("custom_components", domain, "custom_translations")

    def _load_language(self, lang):
        _LOGGER.info(f"Loading translations from lang : {lang}")
        if lang not in self._cache:
            file_path = os.path.join(self._base_path, f"{lang}.json")
            if not os.path.exists(file_path):
                file_path = os.path.join(self._base_path, "fr.json") # Fallback

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self._cache[lang] = json.load(f)
            except Exception as e:
                _LOGGER.error(f"Erreur chargement translation {lang}: {e}")
                self._cache[lang] = {}
        return self._cache[lang]

    def translate(self, path, variables=None, lang=None):
        target_lang = lang or self.hass.config.language or "en"
        data = self._load_language(target_lang)

        # Navigation dans le JSON par points (ex: "intent_response.status.off")
        keys = path.split(".")
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                _LOGGER.warning(f"Missing translation key : {path}")
                return path # Retourne la clé brute si non trouvé

        # Gestion du "default" si on pointe sur un dictionnaire
        if isinstance(value, dict):
            value = value.get("default", path)

        # Gestion des variantes (listes)
        if isinstance(value, list):
            value = random.choice(value)

        # Injection des variables
        if variables and isinstance(value, str):
            try:
                return value.format(**variables)
            except KeyError as e:
                _LOGGER.warning(f"Variable manquante {e} pour la trad {path}")

        return value
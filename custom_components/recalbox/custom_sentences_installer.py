import os
import shutil
import logging
import hashlib
from homeassistant.core import HomeAssistant
from .const import DOMAIN

# by Aurélien Tomassini - ooree23
# Tools : installer les custom_sentences



_LOGGER = logging.getLogger(__name__)

# Calcule le MD5 en ignorant les différences de retours à la ligne
def _get_file_hash(filename):
    """Calcule le hash MD5 d'un fichier."""
    hash_md5 = hashlib.md5()
    try:
        with open(filename, "r", encoding="utf-8", newline=None) as f:
            for line in f:
                # On encode chaque ligne en utf-8 pour le hash
                hash_md5.update(line.encode("utf-8"))
        hashValue = hash_md5.hexdigest()
        _LOGGER.debug("The file %s hash is %s", filename, hashValue)
        return hashValue
    except FileNotFoundError:
        _LOGGER.debug("The file %s doesnt exist", filename)
        return None


def install_sentences(hass: HomeAssistant) -> bool :
    _LOGGER.debug("Checking for Recalbox custom_sentences (re)installation...")
    """Copie récursivement les sentences du composant vers le dossier système de HA."""
    # Chemin source : /config/custom_components/recalbox/sentences
    source_root = hass.config.path("custom_components", DOMAIN, "custom_sentences")
    # Chemin destination : /config/custom_sentences
    dest_root = hass.config.path("custom_sentences")
    changes_made = False

    if not os.path.exists(source_root):
        _LOGGER.warning("Dossier source des sentences introuvable : %s", source_root)
        return False

    try:
        # On parcourt les dossiers de langues (fr, en, es...)
        for lang_dir in os.listdir(source_root):
            source_lang_path = os.path.join(source_root, lang_dir)

            if os.path.isdir(source_lang_path):
                dest_lang_path = os.path.join(dest_root, lang_dir)
                os.makedirs(dest_lang_path, exist_ok=True)
                _LOGGER.debug("Comparing folders %s and %s ...", source_lang_path, dest_lang_path)

                # On copie chaque fichier YAML
                for file_name in os.listdir(source_lang_path):
                    if file_name.endswith(".yaml"):
                        source_file = os.path.join(source_lang_path, file_name)
                        dest_file = os.path.join(dest_lang_path, file_name)
                        _LOGGER.debug("Check if should copy %s to %s ...", source_file, dest_file)

                        # LOGIQUE PAR HASH
                        source_hash = _get_file_hash(source_file)
                        dest_hash = _get_file_hash(dest_file)

                        # Si le fichier destination n'existe pas ou si le contenu diffère
                        if source_hash != dest_hash:
                            _LOGGER.debug("Hashes are different")
                            try:
                                shutil.copy2(source_file, dest_file)
                                _LOGGER.info("Mise à jour phrase Assist : %s", dest_file)
                                changes_made = True
                            except Exception as e:
                                _LOGGER.error("Failed to copy file to %s: %s", dest_file, e)
                        else:
                            _LOGGER.debug("Hashes are equals, no need to copy again this file.")
        if not changes_made:
            _LOGGER.info("Pas de mise à jour nécessaire des phrases Assist")
        return changes_made
    except Exception as e:
        _LOGGER.error("Erreur lors de l'installation des phrases Assist : %s", e)
        return False


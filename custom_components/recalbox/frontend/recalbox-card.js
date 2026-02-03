const RECALBOX_SCRIPT_MIN_VERSION = "v1.4.0";
// Traductions
const TRANSLATIONS = {
  "fr": {
    "subtitle": "Console rétrogaming tout en un",
    "system": "Console",
    "game": "Jeu en cours",
    "genre": "Genre",
    "romPath": "Rom",
    "rebootRequired": "De nouvelles phrases Assist ont été détectées et installées. Redémarrez Home Assistant une nouvelle fois pour les activer et avoir accès aux nouvelles commandes vocales/textuelles.",
    "recalboxScriptUpgradeRequired": "Vous devez installer la dernière version du script sur votre Recalbox. La version actuellement installée est trop ancienne.",
    "buttons": {
      "shutdown": "Éteindre",
      "reboot": "Redémarrer",
      "screenshot": "Capture",
      "pause": "Pause/Reprendre",
      "save": "Enregistrer",
      "load": "Restaurer",
      "stop": "Quitter le jeu"
    },
    "footer": {
        "onHardware": "sur",
        "webManagerLabel": "Web manager Recalbox",
        "integrationLabel": "GitHub de l'intégration",
        "githubPagesLabel": "GitHub Pages"
    },
    "form_sections": {
        "system_buttons": "Affichage des boutons système",
        "in_game_buttons": "Affichage des boutons en jeu",
    },
    "form_label": {
        "entity": "Entité Recalbox",
        "title": "Titre de la carte",
        "subtitle": "Sous-titre",
        "showGameGenre": "Afficher le genre",
        "showRomPath": "Afficher le chemin vers la ROM",
        "showRestartRequiredSuggestion": "Suggestion de redémarrage suite aux mises à jour des phrases Assist",
        "showTurnOffButton": "Éteindre",
        "showRebootButton": "Redémarrer",
        "showScreenshotButton": "Capture",
        "showPauseGameButton": "Pause/Reprendre",
        "showLoadGameButton": "Restaurer",
        "showSaveGameButton": "Enregistrer",
        "showQuitGameButton": "Quitter le jeu",
    },
    "form_description": {
        "entity": "Doit être une entité créée à partir de l'intégration Recalbox",
        "showGameGenre": "Afficher ou non le genre du jeu (textuellement) dans la section du jeu en cours.",
        "showRomPath": "Afficher ou non le chemin de stockage de la ROM lancée, dans la section du jeu en cours.",
        "showRestartRequiredSuggestion": "Lorsque l'intégration Recalbox est installée, ou mise à jour, elle installe les fichiers nécessaires à la reconnaissances des phrases Assist. Si ces phrases ont été mises à jour, l'intégration essaye de recharger Assist, mais en cas d'échec, Home Assistant pourrait nécessiter un redémarrage pour les prendre en compte.",
        "showTurnOffButton": "Demande d'extinction par appel à l'API Recalbox",
        "showRebootButton": "Demande de redémarrage par appel à l'API Recalbox",
        "showScreenshotButton": "Demande de screenshot du jeu en cours, par UDP (sinon, par l'API si l'envoi UDP a échoué)",
        "showPauseGameButton": "Pause/reprise de l'émulateur en cours (par UDP)",
        "showLoadGameButton": "Restaurer le dernier point de sauvegarde par UDP (équivalent à HK + X)",
        "showSaveGameButton": "Créer un point de sauvegarde par UDP (équivalent à HK + Y)",
        "showQuitGameButton": "Quitter le jeu en cours par UDP (retour au menu)",
    },
  },
  "en": {
    "subtitle": "All-in-one retro-gaming console",
    "system": "System",
    "game": "Current game",
    "genre": "Genre",
    "romPath": "Rom",
    "rebootRequired": "New Assist sentences have been installed. You will have to restart Home Assistant again to have access to the new intents on text/voice commands.",
    "recalboxScriptUpgradeRequired": "Please update the script in your Recalbox. The version installed on your Recalbox is too old.",
    "buttons": {
      "shutdown": "Power off",
      "reboot": "Reboot",
      "screenshot": "Screenshot",
      "stop": "Quit game",
      "pause": "Pause/Resume",
      "save": "Save State",
      "load": "Load State",
    },
    "footer": {
        "onHardware": "on",
        "webManagerLabel": "Recalbox web manager",
        "integrationLabel": "GitHub integration",
        "githubPagesLabel": "GitHub Pages"
    },
    "form_sections": {
        "system_buttons": "System buttons display",
        "in_game_buttons": "In-game buttons display"
    },
    "form_label": {
        "entity": "Recalbox Entity",
        "title": "Card Title",
        "subtitle": "Subtitle",
        "showGameGenre": "Show genre",
        "showRomPath": "Show ROM path",
        "showRestartRequiredSuggestion": "Restart suggestion on Assist phrase updates",
        "showTurnOffButton": "Power off",
        "showRebootButton": "Reboot",
        "showScreenshotButton": "Screenshot",
        "showPauseGameButton": "Pause/Resume",
        "showLoadGameButton": "Load State",
        "showSaveGameButton": "Save State",
        "showQuitGameButton": "Quit game"
    },
    "form_description": {
        "entity": "Must be an entity created by the Recalbox integration",
        "showGameGenre": "Whether to display the game genre (text) in the current game section.",
        "showRomPath": "Whether to display the storage path of the running ROM in the current game section.",
        "showRestartRequiredSuggestion": "When the Recalbox integration is installed or updated, it installs the files required for Assist phrase recognition. If these phrases have been updated, and the automatic reload fails, Home Assistant may require a restart to load them.",
        "showTurnOffButton": "Request shutdown via Recalbox API",
        "showRebootButton": "Request reboot via Recalbox API",
        "showScreenshotButton": "Request a screenshot of the current game via UDP (falls back to API if UDP fails)",
        "showPauseGameButton": "Pause/resume the current emulator (via UDP)",
        "showLoadGameButton": "Restore the last save point via UDP (equivalent to HK + X)",
        "showSaveGameButton": "Create a save point via UDP (equivalent to HK + Y)",
        "showQuitGameButton": "Quit the current game via UDP (return to menu)"
    },
  }
};



// ------------ VISUEL DE MA CARTE RECALBOX ------------------


class RecalboxCard extends HTMLElement {

  set hass(hass) {
    if (!hass || !hass.connected) {
      this.innerHTML = `<ha-card><div style="padding:16px; color:orange;">Home Assistant is not ready...</div></ha-card>`;
      return;
    }
    if (!this.config) {
      this.innerHTML = `<ha-card><div style="padding:16px; color:orange;">Configuration not ready yet...</div></ha-card>`;
      return;
    }

    const entityId = this.config.entity;
    const state = hass.states[entityId];

    if (!state) {
      this.innerHTML = `<ha-card><div style="padding:16px; color:red;">Entité non trouvée : ${entityId}</div></ha-card>`;
      return;
    }

    if (!state.attributes) {
      this.innerHTML = `<ha-card><div style="padding:16px; color:red;">Attributs non accessibles : ${entityId}</div></ha-card>`;
      return;
    }

    const lang = (this.config.lang || hass.language || 'en').split('-')[0].toLowerCase();
    const i18n = TRANSLATIONS[lang] || TRANSLATIONS['en'];

    const showGameGenre = this.config.showGameGenre ?? true;
    const showRomPath = this.config.showRomPath ?? false;
    const showRestartRequiredSuggestion = this.config.showRestartRequiredSuggestion ?? true;
    const showTurnOffButton = this.config.showTurnOffButton ?? true;
    const showRebootButton = this.config.showRebootButton ?? true;
    const showScreenshotButton = this.config.showScreenshotButton ?? true;
    const showPauseGameButton = this.config.showPauseGameButton ?? true;
    const showLoadGameButton = this.config.showLoadGameButton ?? true;
    const showSaveGameButton = this.config.showSaveGameButton ?? true;
    const showQuitGameButton = this.config.showQuitGameButton ?? true;

    let needsRecalboxScriptUpgrade = false;
    const currentScriptVersion = state.attributes.scriptVersion;
    if (state && state.attributes.recalboxVersion) {
        if (!currentScriptVersion) {
            // we already had a recalbox version but not the script version
            console.log("Recalbox Card: Aucun scriptVersion trouvé dans les attributs.");
            needsRecalboxScriptUpgrade = true;
        } else {
            const versionParts = currentScriptVersion.split(":");
            const cleanVersion = versionParts.length > 1 ? versionParts[1].trim() : versionParts[0].trim();

            const comparison = cleanVersion.localeCompare(RECALBOX_SCRIPT_MIN_VERSION, undefined, { numeric: true, sensitivity: 'base' });

            // logs
            console.log("--- Recalbox Script Check ---");
            console.log("Brut provenant de l'entité :", currentScriptVersion);
            console.log("Version extraite (clean) :", cleanVersion);
            console.log("Version minimale requise :", RECALBOX_SCRIPT_MIN_VERSION);
            console.log("Résultat localeCompare :", comparison, "(Si < 0, mise à jour requise)");

            needsRecalboxScriptUpgrade = (comparison < 0);
        }
    } else {

    }


    if (!this.content) {
      this.innerHTML = `
        <div id="title"></div>
        <ha-card>
          <style>
            .card-header { padding: 24px 16px 16px; margin-block-start: 0px; margin-block-end: 0px; font-weight: var(--ha-font-weight-normal); font-family: var(--ha-card-header-font-family, inherit); font-size: var(--ha-card-header-font-size, var(--ha-font-size-2xl)); line-height: var(--ha-line-height-condensed); }

            .recalbox-card-content { padding: var(--ha-space-4); }
            .recalbox-card-content hr { margin: 12px 0; border: 0; border-top: 1px solid var(--divider-color); margin: 8px 0; }
            .info-row { display: flex; align-items: center; padding: 4px 0; min-height: 40px; }
            .info-row ha-icon { color: var(--state-icon-color); margin-right: 24px; margin-left: 4px; }
            .info-text { flex-grow: 1; }
            .info-value { color: var(--secondary-text-color); font-size: 0.9em; }
            .one-line { display: flex; flex-direction: row-reverse; gap: 20px; justify-content: space-between; vertical-align: middle; margin: 6px 0; }
            .one-line .info-value { color: var(--primary-text-color); font-size: inherit; }

            .game-preview { text-align: center; padding: 10px 0; margin: 10px -16px; }
            .game-preview img { max-width: 90%; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.5); }

            .card-actions { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; padding: 12px; border-top: 1px solid var(--divider-color); border-radius: 0 0 12px 12px; }
            .action-button { display: flex; min-height: 26px; flex-direction: row; gap: 6px; border-radius: 20px; padding: 0 12px; align-items: center; cursor: pointer; font-size: 10px; text-transform: uppercase; color: var(--primary-text-color); background-color: var(--chip-background-color); }
            /* Couleur spécifique pour le Thème Clair (Light) */ @media (prefers-color-scheme: light) { .action-button { background-color: var(--ha-assist-chip-active-container-color); }}
            .action-button ha-icon { color: var(--_leading-icon-color); --mdc-icon-size: 18px; }
            .no-gap { gap: 0; }
            .game-icon-button { padding: 0 4px; min-height: 26px; align-content: center; }
            .game-icon-button:hover { background-color: var(--chip-background-color); }

            .card-markdown-footer { padding: 24px 16px 16px; font-size: 0.8em; color: var(--secondary-text-color); line-height: 1.4; }
            .card-markdown-footer hr { border: 0; border-top: 1px solid var(--divider-color); margin: 16px 0; }
            .card-markdown-footer a { color: var(--primary-color); text-decoration: none; font-weight: bold; }

            .game-picture { }
          </style>
          <div id="container"></div>
          <div id="actions-area" class="card-actions"></div>
        </ha-card>
        <div id="picture" class="game-picture"></div>
        <div id="markdown-footer" class="card-markdown-footer"></div>
      `;
      this.card_title = this.querySelector('#title');
      this.content = this.querySelector('#container');
      this.picture = this.querySelector('#picture');
      this.actions = this.querySelector('#actions-area');
      this.footer = this.querySelector('#markdown-footer');
    }

    const recalboxName = state.attributes.friendly_name || state.attributes.entity_name || "Recalbox";
    const isOn = state.state === "on";
    const game = state.attributes.game || "-";
    const consoleName = state.attributes.console || "-";
    const genre = state.attributes.genre || "-";
    const romPath = state.attributes.rom || "-";
    const imageUrl = state.attributes.imageUrl || "";
    const isAGameRunning = game && game!="-" && game!="None" && consoleName!="Kodi";
    const needsRestart = state.attributes.needs_restart || false;

    // 0. titre
    this.card_title.innerHTML = `
      <h1 class="card-header">
        ${this.config.title || "Recalbox"}
      </h1>
    `

    // 1. Infos principales
    this.content.innerHTML = `
      <div class="recalbox-card-content">
        <div class="info-row">
          <ha-icon icon="mdi:gamepad-variant-outline"></ha-icon>
          <div class="info-text"><div>${recalboxName}</div><div class="info-value">${this.config.subtitle || i18n.subtitle}</div></div>
          <ha-icon
            icon="mdi:power"
            style="color: ${isOn ? 'var(--state-icon-color)' : 'var(--state-unavailable-color)'}; margin: 0;">
          </ha-icon>
        </div>
        ${isOn ? `
          <hr/>
          <div class="info-row"><ha-icon icon="mdi:sony-playstation"></ha-icon><div class="info-text one-line"><div>${consoleName}</div><div class="info-value">${i18n.system}</div></div></div>
          <div class="info-row"><ha-icon icon="mdi:gamepad-variant-outline"></ha-icon><div class="info-text one-line"><div>${game}</div><div class="info-value">${i18n.game}</div></div></div>
          <div class="info-row" ` + (showGameGenre ? '' : 'style="display:none"')+ `><ha-icon icon="mdi:folder-outline"></ha-icon><div class="info-text one-line"><div>${genre}</div><div class="info-value">${i18n.genre}</div></div></div>
          <div class="info-row" ` + (showRomPath ? '' : 'style="display:none"')+ `><ha-icon icon="mdi:file-outline"></ha-icon><div class="info-text one-line"><div>${romPath}</div><div class="info-value">${i18n.romPath}</div></div></div>
        ` : ''}
      </div>
    `;

    if (needsRestart && showRestartRequiredSuggestion) {
      // insertions d'un petit bandeau d'alerte en haut de la carte
      // Uniquement si on a effectué une mise à jour des sentences,
      // et que l'utilisateur a accepté d'afficher ces alertes
      const alertHtml = `
        <div style="background-color: var(--secondary-background-color); color: white; padding: 12px; border-radius: 6px; border: solid 1px grey; margin: 10px; font-size: 0.8em; display: flex; align-items: center;">
          <ha-icon icon="mdi:alert" style="margin-right: 16px;"></ha-icon>
          ${i18n.rebootRequired}
        </div>
      `;
      this.content.innerHTML += alertHtml;
    }

    if (needsRecalboxScriptUpgrade) {
      const alertHtml = `
        <div style="background-color: var(--secondary-background-color); color: white; padding: 12px; border-radius: 6px; border: solid 1px grey; margin: 10px; font-size: 0.8em; display: flex; align-items: center;">
          <ha-icon icon="mdi:alert" style="margin-right: 16px;"></ha-icon>
          ${i18n.recalboxScriptUpgradeRequired}
          <br/>Min : ${RECALBOX_SCRIPT_MIN_VERSION}
          <br/>Script : ${currentScriptVersion}
        </div>
      `;
      this.content.innerHTML += alertHtml;
    }


    const contentDiv = this.querySelector('.recalbox-card-content');
    if (contentDiv) {
      contentDiv.style.cursor = 'pointer'; // Pour montrer que c'est cliquable
      contentDiv.onclick = () => {
        const event = new Event('hass-more-info', {
          bubbles: true,
          composed: true,
        });
        event.detail = { entityId: this.config.entity };
        this.dispatchEvent(event);
      };
    }

    // Image
    this.picture.innerHTML = `
        ${isOn && isAGameRunning && imageUrl && imageUrl.length > 5 ? `<div class="game-preview">
            <img src="${imageUrl}" onerror="this.style.display='none'; this.style.height='0px';">
        </div>` : ''}
    `

    // 2. Boutons d'actions
    if (isOn) {
      this.actions.style.display = "flex";
      this.actions.innerHTML = `
        <div class="action-button" id="btn-power-off" ` + ((showTurnOffButton) ? '' : 'style="display:none"')+ `><ha-icon icon="mdi:power"></ha-icon>${i18n.buttons.shutdown}</div>
        <div class="action-button" id="btn-reboot" ` + ((showRebootButton) ? '' : 'style="display:none"')+ `><ha-icon icon="mdi:restart"></ha-icon>${i18n.buttons.reboot}</div>

        <div class="action-button no-gap" ` + (isAGameRunning ? '' : 'style="display:none"')+ `>
            ${i18n.game} &nbsp;
            <div class="game-icon-button" title="${i18n.buttons.screenshot}" id="btn-snap" ` + ((showScreenshotButton) ? '' : 'style="display:none"')+ `><ha-icon icon="mdi:camera"></ha-icon></div>
            <div class="game-icon-button" title="${i18n.buttons.pause}" id="btn-pause" ` + ((showPauseGameButton) ? '' : 'style="display:none"')+ `><ha-icon icon="mdi:play-pause"></ha-icon></div>
            <div class="game-icon-button" title="${i18n.buttons.save}" id="btn-save" ` + ((showSaveGameButton) ? '' : 'style="display:none"')+ `><ha-icon icon="mdi:content-save"></ha-icon></div>
            <div class="game-icon-button" title="${i18n.buttons.load}" id="btn-load" ` + ((showLoadGameButton) ? '' : 'style="display:none"')+ `><ha-icon icon="mdi:restore"></ha-icon></div>
            <div class="game-icon-button" title="${i18n.buttons.stop}" id="btn-stop" ` + ((showQuitGameButton) ? '' : 'style="display:none"')+ `><ha-icon icon="mdi:stop"></ha-icon></div>
        </div>
      `;
      this.actions.querySelector('#btn-power-off').onclick = () => hass.callService('recalbox', 'shutdown', { entity_id: entityId });
      this.actions.querySelector('#btn-reboot').onclick = () => hass.callService('recalbox', 'reboot', { entity_id: entityId });
      this.actions.querySelector('#btn-snap').onclick = () => hass.callService('recalbox', 'screenshot', { entity_id: entityId });
      this.actions.querySelector('#btn-pause').onclick = () => hass.callService('recalbox', 'pause_resume_game', { entity_id: entityId });
      this.actions.querySelector('#btn-save').onclick = () => hass.callService('recalbox', 'save_state', { entity_id: entityId });
      this.actions.querySelector('#btn-load').onclick = () => hass.callService('recalbox', 'load_state', { entity_id: entityId });
      this.actions.querySelector('#btn-stop').onclick = () => hass.callService('recalbox', 'quit_game', { entity_id: entityId });
    } else {
      this.actions.style.display = "none";
    }

    // 3. Markdown Footer (Hardware & Links)
    // On essaie de récupérer les infos du device via le registry de HA
    const deviceId = state.context && state.context.device_id;
    const recalboxVersion = state.attributes.recalboxVersion || "x.x";
    const hardware = state.attributes.hardware;
    const host = state.attributes.host;

    this.footer.innerHTML = `
      <div>
        Recalbox (${host}) version ${recalboxVersion}${ (hardware) ? `, ${i18n.footer.onHardware} ${hardware}` : ''}
        <br>
        <a href="http://${host}" target="_blank">${i18n.footer.webManagerLabel}</a> &nbsp; | &nbsp;
        <a href="https://www.recalbox.com" target="_blank">Recalbox.com</a> &nbsp; | &nbsp;
        <!-- <a href="https://github.com/ooree23/RecalboxHomeAssistant" target="_blank">${i18n.footer.integrationLabel}</a> &nbsp; | &nbsp; -->
        <a href="https://ooree23.github.io/RecalboxHomeAssistant/" target="_blank">${i18n.footer.integrationLabel}</a>
      </div>
    `;
  }


  setConfig(config) {
    if (!config.entity) throw new Error("Missing entity in card yaml !");
    this.config = config;
  }
  
  static getConfigElement() {
    return document.createElement("recalbox-card-editor");
  }

  static getStubConfig() {
    return {
      entity: "",
      title: "Recalbox",
      subtitle: "",
      showGameGenre: true,
      showRomPath: false,
      showRestartRequiredSuggestion: true,
      showTurnOffButton: true,
      showRebootButton: true,
      showScreenshotButton: true,
      showPauseGameButton: true,
      showLoadGameButton: true,
      showSaveGameButton: true,
      showQuitGameButton: true,
    };
  }

  getCardSize() { return 6; }
}








// ------------ EDITEUR DE MA CARTE RECALBOX ------------------
// Pour afficher un éditeur inteactif plutot que du yaml pur
// https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/

class RecalboxCardEditor extends HTMLElement {
	
  set hass(hass) {
    this._hass = hass;
    if (this._form) {
      this._form.hass = hass;
    }
  }

  setConfig(config) {
    this._config = config;
    if (this._form) {
      this._form.data = config;
    }
  }

  connectedCallback() {
    this._render();
  }

  _render() {
    if (this._form) return;
    this._form = document.createElement("ha-form");
    this._form.hass = this._hass;
    this._form.data = this._config;
    this._form.schema = this._getSchema();
    this._form.computeLabel = (s) => this._computeLabel(s);
    this._form.computeHelper = (s) => this._computeHelper(s);
    this._form.addEventListener("value-changed", (ev) => {
      const event = new CustomEvent("config-changed", {
        detail: { config: ev.detail.value },
        bubbles: true,
        composed: true,
      });
      this.dispatchEvent(event);
    });
    this.appendChild(this._form);
  }

  _computeLabel(schema) {
    const lang = (this._hass.language || 'en').split('-')[0].toLowerCase();
    const i18n = TRANSLATIONS[lang] ?? TRANSLATIONS['en'];
    const form_labels = i18n.form_label;
    return form_labels[schema.name] || schema.name;
  }

  _computeHelper(schema) {
    const lang = (this._hass.language || 'en').split('-')[0].toLowerCase();
    const i18n = TRANSLATIONS[lang] ?? TRANSLATIONS['en'];
    const labels = i18n.form_description;
    return labels[schema.name];
  }
  
  
  // Le schéma définit les champs de l'interface visuelle
  _getSchema() {
    const lang = (this._hass.language || 'en').split('-')[0].toLowerCase();
    const i18n = TRANSLATIONS[lang] ?? TRANSLATIONS['en'];
    return [
      { name: "title", selector: { text: {} } },
      { name: "entity", required: true, selector: { 
		entity: {
			domain: "switch",
			integration: "recalbox"
		}
	  }}, // https://www.home-assistant.io/docs/blueprint/selectors/#entity-selector
      { name: "subtitle", selector: { text: {} } },
      {
        type: "expandable",
        name: "",
		title: "Informations",
		flatten: true,
        schema: [
          { name: "showGameGenre", selector: { boolean: {} } },
          { name: "showRomPath", selector: { boolean: {} } },
          { name: "showRestartRequiredSuggestion", selector: { boolean: {} } },
        ],
      },
      {
        name: "",
		title: i18n.form_sections.system_buttons,
        type: "expandable",
		flatten: true,
        schema: [
            { name: "showTurnOffButton", selector: { boolean: {} } },
            { name: "showRebootButton", selector: { boolean: {} } },
        ]
      },
      {
        name: "",
		title: i18n.form_sections.in_game_buttons,
        type: "expandable",
		flatten: true,
        schema: [
            { name: "showScreenshotButton", selector: { boolean: {} } },
            { name: "showPauseGameButton", selector: { boolean: {} } },
            { name: "showSaveGameButton", selector: { boolean: {} } },
            { name: "showLoadGameButton", selector: { boolean: {} } },
            { name: "showQuitGameButton", selector: { boolean: {} } },
        ]
      }
    ];
  }
  
}



const isFrench = navigator.language.toLowerCase().startsWith('fr');
const cardDescription = isFrench
  ? "Carte complète avec gestion des jeux, actions et informations système."
  : "Complete card with game management, actions, and system information.";

window.customCards = window.customCards || [];
window.customCards.push({
  type: "recalbox-card",
  name: "Recalbox Card",
  description: cardDescription
});


if (!customElements.get("recalbox-card-editor")) {
  customElements.define("recalbox-card-editor", RecalboxCardEditor);
}
if (!customElements.get("recalbox-card")) {
  customElements.define("recalbox-card", RecalboxCard);
}
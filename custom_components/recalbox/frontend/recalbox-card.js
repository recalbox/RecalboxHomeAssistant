// Traductions
const TRANSLATIONS = {
  "fr": {
    "subtitle": "Console rétrogaming tout en un",
    "system": "Console",
    "game": "Jeu en cours",
    "genre": "Genre",
    "rebootRequired": "De nouvelles phrases Assist ont été détectées et installées. Redémarrez une fois de plus pour les activer et avoir accès aux nouvelles commandes vocales/textuelles.",
    "buttons": {
      "shutdown": "Éteindre",
      "reboot": "Redémarrer",
      "screenshot": "Capture",
      "stop": "Stop"
    },
    "footer": {
        "onHardware": "sur"
    }
  },
  "en": {
    "subtitle": "All-in-one retro-gaming console",
    "system": "System",
    "game": "Current game",
    "genre": "Genre",
    "rebootRequired": "New Assist sentences have been installed. You will have to restart Home Assistant again to have access to the new intents on text/voice commands.",
    "buttons": {
      "shutdown": "Shutdown",
      "reboot": "Reboot",
      "screenshot": "Screenshot",
      "stop": "Stop"
    },
    "footer": {
        "onHardware": "on"
    }
  }
};

class RecalboxCard extends HTMLElement {

  set hass(hass) {
    const entityId = this.config.entity;
    const state = hass.states[entityId];

    const lang = (hass.language || 'en').split('-')[0];
    const i18n = TRANSLATIONS[lang] || TRANSLATIONS['en'];

    if (!state) {
      this.innerHTML = `<ha-card><div style="padding:16px; color:red;">Entité non trouvée : ${entityId}</div></ha-card>`;
      return;
    }

    const shutdownBtn = this.config.shutdown_button || `button.recalbox_shutdown`;
    const rebootBtn = this.config.reboot_button || `button.recalbox_reboot`;
    const screenshotBtn = this.config.screenshot_button || `button.recalbox_screenshot`;
    const stopBtn = this.config.quit_button || `button.recalbox_stop`;

    if (!this.content) {
      this.innerHTML = `
        <div id="title"></div>
        <ha-card>
          <style>
            .card-header { padding: 24px 16px 16px; margin-block-start: 0px; margin-block-end: 0px; font-weight: var(--ha-font-weight-normal); font-family: var(--ha-card-header-font-family, inherit); font-size: var(--ha-card-header-font-size, var(--ha-font-size-2xl)); line-height: var(--ha-line-height-condensed); }

            .recalbox-card-content { padding: 16px; }
            .recalbox-card-content hr { margin: 12px 0; border: 0; border-top: 1px solid var(--divider-color); margin: 8px 0; }
            .info-row { display: flex; align-items: center; padding: 8px 0; }
            .info-row ha-icon { color: var(--state-icon-color); margin-right: 16px; }
            .info-text { flex-grow: 1; }
            .info-value { color: var(--secondary-text-color); font-size: 0.9em; }
            .one-line { display: flex; flex-direction: row-reverse; gap: 20px; justify-content: space-between; vertical-align: middle; margin: 6px 0; }
            .one-line .info-value { color: var(--primary-text-color); font-size: inherit; }
            .status-badge { background: var(--disabled-text-color); color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.8em; float: right; }
            .status-on { background: var(--success-color); }

            .game-preview { text-align: center; padding: 10px 0; margin: 10px -16px; }
            .game-preview img { max-width: 90%; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.5); }

            .card-actions { display: flex; gap: 8px; justify-content: center; padding: 12px; background-color: var(--secondary-background-color); border-top: 1px solid var(--divider-color); border-radius: 0 0 12px 12px; }
            .action-button { display: flex; flex-direction: row; gap: 6px; border-radius: 20px; padding: 2px 12px; align-items: center; cursor: pointer; font-size: 10px; text-transform: uppercase; color: var(--primary-text-color); background-color: var(--chip-background-color); }
            .action-button ha-icon { color: var(--_leading-icon-color); margin-bottom: 4px; --mdc-icon-size: 18px; }

            .card-markdown-footer { padding: 24px 16px 16px; font-size: 0.8em; color: var(--secondary-text-color); line-height: 1.4; }
            .card-markdown-footer hr { border: 0; border-top: 1px solid var(--divider-color); margin: 8px 0; }
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

    const isOn = state.state === "on";
    const game = state.attributes.game || "-";
    const consoleName = state.attributes.console || "-";
    const isAGameRunning = game && game!="-" && game!="None" && consoleName!="Kodi";
    const genre = state.attributes.genre || "-";
    const imageUrl = state.attributes.imageUrl || "";
    const needsRestart = state.attributes.needs_restart || false;

    // 0. titre
    this.card_title.innerHTML = `
      <h1 class="card-header">
        Recalbox
      </h1>
    `

    // 1. Infos principales
    this.content.innerHTML = `
      <div class="recalbox-card-content">
        <div class="info-row">
          <ha-icon icon="mdi:gamepad-variant-outline"></ha-icon>
          <div class="info-text"><div>${this.config.title || "Recalbox"}</div><div class="info-value">${i18n.subtitle}</div></div>
          <span class="status-badge ${isOn ? 'status-on' : ''}">${state.state.toUpperCase()}</span>
        </div>
        ${isOn ? `
          <hr/>
          <div class="info-row"><ha-icon icon="mdi:sony-playstation"></ha-icon><div class="info-text one-line"><div>${consoleName}</div><div class="info-value">${i18n.system}</div></div></div>
          <div class="info-row"><ha-icon icon="mdi:gamepad-variant-outline"></ha-icon><div class="info-text one-line"><div>${game}</div><div class="info-value">${i18n.game}</div></div></div>
          <div class="info-row"><ha-icon icon="mdi:folder-outline"></ha-icon><div class="info-text one-line"><div>${genre}</div><div class="info-value">${i18n.genre}</div></div></div>
        ` : ''}
      </div>
    `;

    if (needsRestart) {
      // On insère un petit bandeau d'alerte en haut de la carte
      const alertHtml = `
        <div style="background-color: var(--warning-color); color: white; padding: 8px; border-radius: 4px; margin: 10px; font-size: 0.8em; display: flex; align-items: center;">
          <ha-icon icon="mdi:alert" style="margin-right: 8px;"></ha-icon>
          ${i18n.rebootRequired}
        </div>
      `;
      // Injecter ce HTML dans ta carte
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
        <div class="action-button" id="btn-power-off"><ha-icon icon="mdi:power"></ha-icon>${i18n.buttons.shutdown}</div>
        <div class="action-button" id="btn-reboot"><ha-icon icon="mdi:restart"></ha-icon>${i18n.buttons.reboot}</div>
        <div class="action-button" id="btn-snap" ` + (isAGameRunning ? '' : 'style="display:none"')+ `><ha-icon icon="mdi:camera"></ha-icon>${i18n.buttons.screenshot}</div>
        <div class="action-button" id="btn-stop" ` + (isAGameRunning ? '' : 'style="display:none"')+ `><ha-icon icon="mdi:location-exit"></ha-icon>${i18n.buttons.stop}</div>
      `;
      this.actions.querySelector('#btn-power-off').onclick = () => hass.callService('button', 'press', { entity_id: shutdownBtn });
      this.actions.querySelector('#btn-reboot').onclick = () => hass.callService('button', 'press', { entity_id: rebootBtn });
      this.actions.querySelector('#btn-snap').onclick = () => hass.callService('button', 'press', { entity_id: screenshotBtn });
      this.actions.querySelector('#btn-stop').onclick = () => hass.callService('button', 'press', { entity_id: stopBtn });
    } else {
      this.actions.style.display = "none";
    }

    // 3. Markdown Footer (Hardware & Links)
    // On essaie de récupérer les infos du device via le registry de HA
    const deviceId = state.context && state.context.device_id;
    const recalboxVersion = state.attributes.recalboxVersion || "x.x";
    const hardware = state.attributes.hardware;
    const host = this.config.host || "recalbox.local";

    this.footer.innerHTML = `
      <div>
        Recalbox (${host}) version ${recalboxVersion}${ (hardware) ? `, ${i18n.footer.onHardware} ${hardware}` : ''}
        <br>
        <a href="http://${host}:81" target="_blank">Web manager Recalbox</a> |
        <a href="https://www.recalbox.com" target="_blank">Recalbox.com</a> |
        <a href="https://github.com/tototo23/RecalboxHomeAssistant" target="_blank">GitHub intégration</a>
      </div>
    `;
  }

  setConfig(config) {
    if (!config.entity) throw new Error("Entité manquante");
    this.config = config;
  }

  getCardSize() { return 6; }
}

customElements.define('recalbox-card', RecalboxCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "recalbox-card",
  name: "Recalbox Card",
  description: "Carte complète avec gestion des jeux, actions et informations système."
});
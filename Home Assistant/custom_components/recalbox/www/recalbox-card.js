class RecalboxCard extends HTMLElement {
  set hass(hass) {
    if (!this.content) {
      this.innerHTML = `<ha-card header="Recalbox"></ha-card>`;
      this.content = this.querySelector('ha-card');
    }

    const entityId = this.config.entity;
    const state = hass.states[entityId];

    if (!state) {
      this.content.innerHTML = `<div style="padding:16px;">Entité non trouvée : ${entityId}</div>`;
      return;
    }

    const game = state.attributes.game || "-";
    const console = state.attributes.console || "-";
    const genre = state.attributes.genre || "-";
    const imageUrl = state.attributes.imageUrl || "";
    const isOn = state.state === "on";

    let html = `
      <style>
        .card-content { padding: 16px; }
        .game-img { width: 100%; border-radius: 8px; margin: 10px 0; display: ${imageUrl && isOn ? 'block' : 'none'}; }
        .status-on { color: var(--success-color); }
        .info-row { display: flex; align-items: center; margin: 8px 0; }
        .info-row ha-icon { margin-right: 12px; color: var(--primary-text-color); }
        .actions { display: flex; justify-content: space-around; padding: 8px; border-top: 1px solid var(--divider-color); }
      </style>
      <div class="card-content">
        <div class="info-row">
          <ha-icon icon="mdi:controller"></ha-icon>
          <span>Statut: <b class="${isOn ? 'status-on' : ''}">${state.state.toUpperCase()}</b></span>
        </div>
    `;

    if (isOn) {
      html += `
        <div class="info-row"><ha-icon icon="mdi:sony-playstation"></ha-icon><span>Console: ${console}</span></div>
        <div class="info-row"><ha-icon icon="mdi:gamepad-variant-outline"></ha-icon><span>Jeu: ${game}</span></div>
        <div class="info-row"><ha-icon icon="mdi:folder-outline"></ha-icon><span>Genre: ${genre}</span></div>
      `;
    }

    html += `</div>`;

    // Ajout des boutons si souhaité
    html += `
      <div class="actions">
        <ha-icon-button icon="mdi:camera" title="Screenshot" id="btn-snap"></ha-icon-button>
        <ha-icon-button icon="mdi:restart" title="Reboot" id="btn-reboot"></ha-icon-button>
        <ha-icon-button icon="mdi:power" title="Shutdown" id="btn-stop"></ha-icon-button>
      </div>
    `;

    if (isOn && img.length && img.length > 5) {
      html += `
        <img class="game-img" src="${imageUrl}">
      `;
    }

    this.content.innerHTML = html;

    // Gestion des clics (Exemple pour Screenshot)
    this.content.querySelector('#btn-snap').onclick = () => {
      hass.callService('button', 'press', { entity_id: this.config.screenshot_button });
    };
  }

  setConfig(config) {
    if (!config.entity) throw new Error("Vous devez définir l'entité binary_sensor");
    this.config = config;
  }

  getCardSize() { return 3; }
}

customElements.define('recalbox-card', RecalboxCard);

// Enregistrement pour l'interface de sélection des cartes
window.customCards = window.customCards || [];
window.customCards.push({
  type: "recalbox-card",
  name: "Recalbox Card",
  preview: true,
  description: "Affiche l'état du jeu et les contrôles Recalbox"
});
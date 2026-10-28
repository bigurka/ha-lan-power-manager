// LAN Power Manager sidebar panel - plain Web Component, no build step, no external dependencies.
// Talks to the backend only through the lan_power_manager/* websocket commands.

const T = {
  it: {
    title: "LAN Power Manager",
    scan: "Scansiona ora",
    scanning: "Scansione in corso…",
    add: "Aggiungi dispositivo",
    last_scan: "Ultima scansione",
    never: "mai",
    subnets: "Reti",
    search: "Cerca nome, IP, MAC…",
    f_all: "Tutti",
    f_mapped: "Mappati",
    f_unmapped: "Non mappati",
    f_new: "Nuovi",
    f_ignored: "Ignorati",
    c_state: "Stato",
    c_name: "Dispositivo",
    c_ip: "IP",
    c_mac: "MAC",
    c_vendor: "Produttore",
    c_seen: "Ultimo visto",
    c_actions: "Azioni",
    online: "Acceso",
    offline: "Spento",
    turning_on: "In accensione…",
    turning_off: "In spegnimento…",
    mapped: "Mappato",
    new: "Nuovo",
    ignored: "Ignorato",
    windows: "Windows",
    map: "Mappa",
    edit: "Modifica",
    ignore: "Ignora",
    unignore: "Ripristina",
    delete: "Elimina",
    power_on: "Accendi",
    power_off: "Spegni",
    confirm_off: "{action} {name}?",
    off_shutdown: "Spegni",
    off_hibernate: "Iberna",
    off_suspend: "Sospendi",
    d_off_action: "Azione allo spegnimento",
    d_off_action_hint: "È quello che fa lo switch quando lo spegni, e compare nel suo nome (\"Accendi / Iberna\"); l'entity_id switch.<nome> non cambia. Ogni azione ha comunque il suo pulsante.",
    d_off_hibernate_windows: "Windows: l'ibernazione va attivata sul PC con powercfg /h on (prompt come amministratore). Niente avviso a video.",
    d_off_suspend_windows: "Windows: se sul PC è attiva l'ibernazione, al posto della sospensione può ibernare. Niente avviso a video.",
    d_off_hibernate_linux: "Linux: serve una swap configurata per l'ibernazione.",
    confirm_delete: "Eliminare {name} dall'inventario?",
    empty: "Nessun dispositivo. Avvia una scansione o aggiungine uno a mano.",
    d_title_map: "Mappa dispositivo",
    d_title_edit: "Modifica dispositivo",
    d_title_new: "Nuovo dispositivo",
    d_general: "Generale",
    d_name: "Nome",
    d_mac: "MAC",
    d_ip: "Indirizzo IP",
    d_entities: "Entità in Home Assistant",
    e_none: "Nessuna (non mappato)",
    e_presence: "Solo presenza",
    e_control: "Solo controllo",
    e_both: "Presenza e controllo",
    d_entities_hint: "Presenza: device_tracker.<nome> (in casa / fuori casa). Controllo: switch.<nome> (accende col Wake-on-LAN, spegne con l'azione allo spegnimento) e i pulsanti button.<nome>_wol / _shutdown / _hibernate / _suspend, solo quelli possibili per questo dispositivo.",
    b_presence: "Presenza",
    b_control: "Controllo",
    b_both: "Presenza + controllo",
    d_power_on: "Accensione",
    d_wol: "Wake-on-LAN abilitato",
    d_broadcast: "Broadcast WOL (facoltativo, per reti dietro un router)",
    d_power_off: "Spegnimento",
    d_method: "Metodo",
    m_windows: "Windows (WMI/RPC)",
    m_ssh: "SSH (Windows, Linux, macOS)",
    m_none: "Nessuno (solo accensione)",
    d_username: "Utente",
    d_password: "Password",
    d_domain: "Dominio Windows",
    d_clear_password: "Cancella la password salvata",
    d_default: "predefinito: {value}",
    d_password_keep: "vuota = invariata",
    d_password_global: "vuota = quella delle opzioni",
    d_ssh_port: "Porta SSH",
    d_ssh_command: "Comando personalizzato (azione allo spegnimento)",
    d_delay: "Preavviso (secondi)",
    d_message: "Messaggio di avviso",
    d_policy: "Se c'è un utente collegato",
    p_default: "Come nelle opzioni",
    p_force: "Avvisa, aspetta e spegni",
    p_skip: "Non spegnere",
    d_last_action: "Ultima azione",
    cancel: "Annulla",
    save: "Salva",
    saved: "Salvato.",
    no_mac: "senza MAC: Wake-on-LAN non possibile",
    random_mac: "(indirizzo casuale/virtuale)",
    ssh_key_title: "Chiave SSH di Home Assistant",
    ssh_key_hint: "Generata da Home Assistant. La parte privata non esce mai da Home Assistant: sui PC si installa solo questa parte pubblica.",
    copy: "Copia",
    copied: "Copiato.",
    d_ssh_os: "Sistema del PC",
    os_windows: "Windows",
    os_linux: "Linux",
    os_macos: "macOS",
    d_ssh_restricted: "Solo questa azione (con questa chiave il PC accetta solo l'azione allo spegnimento)",
    d_ssh_restricted_hint: "Azione, comando, preavviso e messaggio vengono scritti nella chiave sul PC: se li cambi, reinstalla la chiave. Le altre azioni (es. lan_power_manager.hibernate su uno switch \"Spegni\") non saranno possibili.",
    d_identity: "Identità del PC",
    d_identity_none: "non ancora memorizzata: lo sarà alla prima connessione",
    d_forget: "Dimentica identità (PC reinstallato o sostituito)",
    d_setup: "Comando di installazione",
    d_test: "Verifica connessione",
    d_test_save_first: "Salva il dispositivo prima di verificare la connessione.",
    d_setup_windows: "Sul PC apri PowerShell come amministratore e incolla questi comandi. Installano il server SSH, aprono la porta 22 e autorizzano la chiave di Home Assistant per gli account amministratori.",
    d_setup_linux: "Esegui questi comandi sul PC con l'utente usato da Home Assistant (serve sudo per il permesso di spegnimento).",
    d_password_key: "facoltativa: si usa la chiave",
    d_cmd_windows: "predefinito: secondo l'azione allo spegnimento",
  },
  en: {
    title: "LAN Power Manager",
    scan: "Scan now",
    scanning: "Scanning…",
    add: "Add device",
    last_scan: "Last scan",
    never: "never",
    subnets: "Subnets",
    search: "Search name, IP, MAC…",
    f_all: "All",
    f_mapped: "Mapped",
    f_unmapped: "Not mapped",
    f_new: "New",
    f_ignored: "Ignored",
    c_state: "State",
    c_name: "Device",
    c_ip: "IP",
    c_mac: "MAC",
    c_vendor: "Vendor",
    c_seen: "Last seen",
    c_actions: "Actions",
    online: "On",
    offline: "Off",
    turning_on: "Turning on…",
    turning_off: "Turning off…",
    mapped: "Mapped",
    new: "New",
    ignored: "Ignored",
    windows: "Windows",
    map: "Map",
    edit: "Edit",
    ignore: "Ignore",
    unignore: "Restore",
    delete: "Delete",
    power_on: "Turn on",
    power_off: "Turn off",
    confirm_off: "{action} {name}?",
    off_shutdown: "Shut down",
    off_hibernate: "Hibernate",
    off_suspend: "Suspend",
    d_off_action: "Off action",
    d_off_action_hint: "What the switch does when turned off; it shows in its name (\"On / Hibernate\") while the entity_id switch.<name> does not change. Each action also has its own button.",
    d_off_hibernate_windows: "Windows: enable hibernation on the computer with powercfg /h on (administrator prompt). No on-screen warning.",
    d_off_suspend_windows: "Windows: if hibernation is enabled on the computer it may hibernate instead of sleeping. No on-screen warning.",
    d_off_hibernate_linux: "Linux: needs swap set up for hibernation.",
    confirm_delete: "Delete {name} from the inventory?",
    empty: "No devices. Start a scan or add one by hand.",
    d_title_map: "Map device",
    d_title_edit: "Edit device",
    d_title_new: "New device",
    d_general: "General",
    d_name: "Name",
    d_mac: "MAC",
    d_ip: "IP address",
    d_entities: "Entities in Home Assistant",
    e_none: "None (not mapped)",
    e_presence: "Presence only",
    e_control: "Control only",
    e_both: "Presence and control",
    d_entities_hint: "Presence: device_tracker.<name> (home / not home). Control: switch.<name> (on with Wake-on-LAN, off with the off action) and the buttons button.<name>_wol / _shutdown / _hibernate / _suspend, only the ones possible for this device.",
    b_presence: "Presence",
    b_control: "Control",
    b_both: "Presence + control",
    d_power_on: "Power on",
    d_wol: "Wake-on-LAN enabled",
    d_broadcast: "WOL broadcast (optional, for subnets behind a router)",
    d_power_off: "Power off",
    d_method: "Method",
    m_windows: "Windows (WMI/RPC)",
    m_ssh: "SSH (Windows, Linux, macOS)",
    m_none: "None (power on only)",
    d_username: "Username",
    d_password: "Password",
    d_domain: "Windows domain",
    d_clear_password: "Clear the stored password",
    d_default: "default: {value}",
    d_password_keep: "empty = unchanged",
    d_password_global: "empty = the one in the options",
    d_ssh_port: "SSH port",
    d_ssh_command: "Custom command (off action)",
    d_delay: "Warning (seconds)",
    d_message: "Warning message",
    d_policy: "If a user is logged on",
    p_default: "As in the options",
    p_force: "Warn, wait and shut down",
    p_skip: "Do not shut down",
    d_last_action: "Last action",
    cancel: "Cancel",
    save: "Save",
    saved: "Saved.",
    no_mac: "no MAC: Wake-on-LAN not possible",
    random_mac: "(random/virtual address)",
    ssh_key_title: "Home Assistant SSH key",
    ssh_key_hint: "Generated by Home Assistant. The private half never leaves Home Assistant: only this public half is installed on the computers.",
    copy: "Copy",
    copied: "Copied.",
    d_ssh_os: "Computer system",
    os_windows: "Windows",
    os_linux: "Linux",
    os_macos: "macOS",
    d_ssh_restricted: "This action only (with this key the computer accepts nothing but the off action)",
    d_ssh_restricted_hint: "Action, command, warning and message are written in the key on the computer: if you change them, install the key again. The other actions (e.g. lan_power_manager.hibernate on a \"Shut down\" switch) will not be possible.",
    d_identity: "Computer identity",
    d_identity_none: "not stored yet: it will be at the first connection",
    d_forget: "Forget identity (computer reinstalled or replaced)",
    d_setup: "Setup commands",
    d_test: "Test connection",
    d_test_save_first: "Save the device before testing the connection.",
    d_setup_windows: "On the computer open PowerShell as administrator and paste these commands. They install the SSH server, open port 22 and authorize the Home Assistant key for administrator accounts.",
    d_setup_linux: "Run these commands on the computer as the user Home Assistant logs in with (sudo is needed for the shutdown permission).",
    d_password_key: "optional: the key is used",
    d_cmd_windows: "default: depends on the off action",
  },
};

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[c]);
}

function ipKey(ip) {
  if (!ip) return Number.MAX_SAFE_INTEGER;
  return ip.split(".").reduce((acc, part) => acc * 256 + Number(part), 0);
}

const STYLES = `
  :host { display: block; min-height: 100vh; background: var(--primary-background-color); color: var(--primary-text-color);
    font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif); }
  header { display: flex; align-items: center; gap: 12px; height: 56px; padding: 0 16px;
    background: var(--app-header-background-color, var(--primary-color)); color: var(--app-header-text-color, #fff); }
  header h1 { font-size: 20px; font-weight: 400; margin: 0; flex: 1; }
  .menu { background: none; border: none; color: inherit; cursor: pointer; padding: 8px; display: none; }
  .menu.narrow { display: inline-flex; }
  main { padding: 16px; max-width: 1400px; margin: 0 auto; box-sizing: border-box; }
  .toolbar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 12px; }
  .info { color: var(--secondary-text-color); font-size: 13px; margin-bottom: 12px; }
  button.btn { border: none; border-radius: 6px; padding: 8px 14px; cursor: pointer; font: inherit; font-size: 14px;
    background: var(--primary-color); color: var(--text-primary-color, #fff); }
  button.btn.flat { background: transparent; color: var(--primary-color); border: 1px solid var(--divider-color); }
  button.btn.small { padding: 4px 10px; font-size: 13px; }
  button.btn.danger { background: var(--error-color, #db4437); }
  button.btn.ok { background: var(--success-color, #43a047); }
  button.btn:disabled { opacity: .5; cursor: default; }
  .chips { display: flex; gap: 4px; flex-wrap: wrap; }
  .chip { border: 1px solid var(--divider-color); border-radius: 16px; padding: 4px 12px; cursor: pointer; font-size: 13px;
    background: var(--card-background-color); color: var(--primary-text-color); }
  .chip.active { background: var(--primary-color); color: var(--text-primary-color, #fff); border-color: var(--primary-color); }
  input.search { flex: 1; min-width: 180px; padding: 8px 10px; border-radius: 6px; border: 1px solid var(--divider-color);
    background: var(--card-background-color); color: var(--primary-text-color); font: inherit; }
  .card { background: var(--card-background-color); border-radius: var(--ha-card-border-radius, 12px);
    box-shadow: var(--ha-card-box-shadow, none); border: 1px solid var(--divider-color); overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; font-size: 14px; }
  th { text-align: left; font-weight: 500; color: var(--secondary-text-color); padding: 10px 12px;
    border-bottom: 1px solid var(--divider-color); white-space: nowrap; }
  td { padding: 8px 12px; border-bottom: 1px solid var(--divider-color); vertical-align: middle; }
  tr:last-child td { border-bottom: none; }
  tr.ignored td { opacity: .55; }
  .mono { font-family: var(--code-font-family, monospace); font-size: 13px; white-space: nowrap; }
  .dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; background: var(--disabled-color, #999); }
  .dot.on { background: var(--success-color, #43a047); }
  .dot.pending { background: var(--warning-color, #ffa600); animation: blink 1s infinite; }
  @keyframes blink { 50% { opacity: .3; } }
  .state { white-space: nowrap; }
  .name { font-weight: 500; }
  .sub { color: var(--secondary-text-color); font-size: 12px; }
  .badge { display: inline-block; font-size: 11px; border-radius: 4px; padding: 1px 6px; margin-left: 4px;
    background: var(--secondary-background-color); color: var(--secondary-text-color); vertical-align: middle; }
  .badge.mapped { background: var(--primary-color); color: var(--text-primary-color, #fff); }
  .badge.new { background: var(--warning-color, #ffa600); color: #000; }
  .actions { display: flex; gap: 4px; flex-wrap: wrap; }
  .empty { padding: 32px; text-align: center; color: var(--secondary-text-color); }
  .toast { position: fixed; left: 50%; bottom: 24px; transform: translateX(-50%); padding: 10px 16px; border-radius: 6px;
    background: #323232; color: #fff; max-width: 90vw; z-index: 10; font-size: 14px; }
  .toast.error { background: var(--error-color, #db4437); }
  dialog { border: none; border-radius: 12px; padding: 0; width: min(560px, 94vw); max-height: 90vh;
    background: var(--card-background-color); color: var(--primary-text-color); }
  dialog::backdrop { background: rgba(0,0,0,.45); }
  form { display: flex; flex-direction: column; max-height: 90vh; }
  .d-head { padding: 16px 20px 8px; font-size: 18px; }
  .d-body { padding: 0 20px; overflow-y: auto; }
  .d-foot { display: flex; justify-content: flex-end; gap: 8px; padding: 12px 20px 16px; }
  fieldset { border: 1px solid var(--divider-color); border-radius: 8px; margin: 8px 0; padding: 8px 12px 12px; }
  legend { color: var(--secondary-text-color); font-size: 13px; padding: 0 4px; }
  label.f { display: flex; flex-direction: column; gap: 4px; font-size: 13px; margin-top: 8px; color: var(--secondary-text-color); }
  label.f input, label.f select { padding: 8px; border-radius: 6px; border: 1px solid var(--divider-color); font: inherit;
    background: var(--primary-background-color); color: var(--primary-text-color); }
  label.c { display: flex; align-items: center; gap: 8px; font-size: 14px; margin-top: 10px; }
  .row { display: grid; grid-template-columns: 1fr 1fr; gap: 0 12px; }
  .hint { font-size: 12px; color: var(--secondary-text-color); margin-top: 8px; }
  .hint.bad { color: var(--error-color, #db4437); }
  details.key { margin-bottom: 12px; font-size: 13px; }
  details.key summary { cursor: pointer; color: var(--secondary-text-color); }
  .keybox { display: flex; gap: 8px; align-items: flex-start; margin-top: 8px; }
  .keybox code, textarea.script { flex: 1; font-family: var(--code-font-family, monospace); font-size: 12px; word-break: break-all;
    background: var(--secondary-background-color); color: var(--primary-text-color); padding: 8px; border-radius: 6px; }
  textarea.script { width: 100%; box-sizing: border-box; min-height: 160px; border: 1px solid var(--divider-color); resize: vertical; white-space: pre; word-break: normal; }
  .btnrow { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
  @media (max-width: 700px) {
    .hide-narrow { display: none; }
    .row { grid-template-columns: 1fr; }
    main { padding: 8px; }
  }
`;

class LanPowerManagerPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._state = null;
    this._filter = "all";
    this._search = "";
    this._unsub = null;
    this._toastTimer = null;
  }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    if (first) {
      this._renderShell();
      this._subscribe();
    }
  }

  set narrow(narrow) {
    this._narrow = narrow;
    const menu = this.shadowRoot.querySelector(".menu");
    if (menu) menu.classList.toggle("narrow", !!narrow);
  }

  disconnectedCallback() {
    if (this._unsub) {
      this._unsub.then((unsub) => unsub()).catch(() => {});
      this._unsub = null;
    }
  }

  connectedCallback() {
    if (this._hass && !this._unsub) this._subscribe();
  }

  _t(key, vars = {}) {
    const lang = (this._hass?.locale?.language || this._hass?.language || "en").startsWith("it") ? "it" : "en";
    let text = T[lang][key] ?? T.en[key] ?? key;
    for (const [k, v] of Object.entries(vars)) text = text.replace(`{${k}}`, v);
    return text;
  }

  _ws(msg) {
    return this._hass.connection.sendMessagePromise({ ...msg, type: `lan_power_manager/${msg.type}` });
  }

  _subscribe() {
    this._unsub = this._hass.connection.subscribeMessage(
      (state) => {
        this._state = state;
        this._renderContent();
      },
      { type: "lan_power_manager/subscribe" }
    );
    this._unsub.catch((err) => this._toast(err.message || String(err), true));
  }

  _toast(text, error = false) {
    const el = this.shadowRoot.querySelector(".toast");
    // A modal dialog sits in the top layer: show the toast inside it, or it would be hidden behind.
    const dialog = this.shadowRoot.querySelector("#dialog");
    (dialog.open ? dialog : this.shadowRoot).appendChild(el);
    el.textContent = text;
    el.className = `toast${error ? " error" : ""}`;
    el.hidden = false;
    clearTimeout(this._toastTimer);
    this._toastTimer = setTimeout(() => (el.hidden = true), error ? 8000 : 3500);
  }

  async _copy(text) {
    try {
      await navigator.clipboard.writeText(text);
    } catch (err) {
      // No clipboard API on plain http: fall back to a selected textarea.
      const dialog = this.shadowRoot.querySelector("#dialog");
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      (dialog.open ? dialog : this.shadowRoot).appendChild(ta);
      ta.select();
      document.execCommand("copy");
      ta.remove();
    }
    this._toast(this._t("copied"));
  }

  async _run(promise, okText) {
    try {
      const result = await promise;
      if (result?.detail) this._toast(result.detail);
      else if (okText) this._toast(okText);
    } catch (err) {
      this._toast(err.message || String(err), true);
    }
  }

  _renderShell() {
    this.shadowRoot.innerHTML = `
      <style>${STYLES}</style>
      <header>
        <button class="menu${this._narrow ? " narrow" : ""}" title="Menu">
          <svg width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M3,6H21V8H3V6M3,11H21V13H3V11M3,16H21V18H3V16Z"/></svg>
        </button>
        <h1>${esc(this._t("title"))}</h1>
      </header>
      <main>
        <div class="toolbar">
          <button class="btn" id="scan">${esc(this._t("scan"))}</button>
          <button class="btn flat" id="add">${esc(this._t("add"))}</button>
          <input class="search" id="search" placeholder="${esc(this._t("search"))}">
        </div>
        <div class="toolbar"><div class="chips" id="chips"></div></div>
        <div class="info" id="info"></div>
        <details class="key" id="key"></details>
        <div class="card" id="list"></div>
      </main>
      <dialog id="dialog"></dialog>
      <div class="toast" hidden></div>
    `;
    const root = this.shadowRoot;
    root.querySelector(".menu").addEventListener("click", () =>
      this.dispatchEvent(new Event("hass-toggle-menu", { bubbles: true, composed: true }))
    );
    root.querySelector("#scan").addEventListener("click", () => this._run(this._ws({ type: "scan" })));
    root.querySelector("#add").addEventListener("click", () => this._openDialog(null));
    root.querySelector("#search").addEventListener("input", (ev) => {
      this._search = ev.target.value.trim().toLowerCase();
      this._renderContent();
    });
    root.querySelector("#list").addEventListener("click", (ev) => this._onListClick(ev));
    this._renderContent();
  }

  _filtered() {
    const devices = this._state?.devices ?? [];
    const q = this._search;
    return devices
      .filter((d) => {
        switch (this._filter) {
          case "mapped": return d.mapped;
          case "unmapped": return !d.mapped && !d.ignored;
          case "new": return d.new && !d.mapped && !d.ignored;
          case "ignored": return d.ignored;
          default: return !d.ignored;
        }
      })
      .filter((d) => !q || [d.label, d.hostname, d.ip, d.mac, d.vendor].some((v) => (v || "").toLowerCase().includes(q)))
      .sort((a, b) => (b.mapped - a.mapped) || (ipKey(a.ip) - ipKey(b.ip)));
  }

  _formatDate(iso) {
    if (!iso) return "—";
    const d = new Date(iso);
    const lang = this._hass?.locale?.language || this._hass?.language || "it";
    const today = new Date().toDateString() === d.toDateString();
    return today
      ? d.toLocaleTimeString(lang, { hour: "2-digit", minute: "2-digit" })
      : d.toLocaleString(lang, { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
  }

  _renderContent() {
    const root = this.shadowRoot;
    if (!root.querySelector("#list")) return;
    const state = this._state;
    const devices = state?.devices ?? [];

    const scanBtn = root.querySelector("#scan");
    scanBtn.disabled = !!state?.scanning;
    scanBtn.textContent = state?.scanning ? this._t("scanning") : this._t("scan");

    const counts = {
      all: devices.filter((d) => !d.ignored).length,
      mapped: devices.filter((d) => d.mapped).length,
      unmapped: devices.filter((d) => !d.mapped && !d.ignored).length,
      new: devices.filter((d) => d.new && !d.mapped && !d.ignored).length,
      ignored: devices.filter((d) => d.ignored).length,
    };
    root.querySelector("#chips").innerHTML = Object.keys(counts)
      .map((f) => `<button class="chip${this._filter === f ? " active" : ""}" data-filter="${f}">${esc(this._t(`f_${f}`))} (${counts[f]})</button>`)
      .join("");
    root.querySelectorAll(".chip").forEach((chip) =>
      chip.addEventListener("click", () => {
        this._filter = chip.dataset.filter;
        this._renderContent();
      })
    );

    if (state) {
      root.querySelector("#info").textContent =
        `${this._t("subnets")}: ${state.subnets.join(", ") || "—"} · ${this._t("last_scan")}: ` +
        (state.last_scan ? this._formatDate(state.last_scan) : this._t("never"));
    }

    const keyBox = root.querySelector("#key");
    if (state?.ssh_public_key && keyBox.dataset.key !== state.ssh_public_key) {
      keyBox.dataset.key = state.ssh_public_key;
      keyBox.innerHTML = `
        <summary>${esc(this._t("ssh_key_title"))} · ${esc(state.ssh_key_fingerprint)}</summary>
        <div class="hint">${esc(this._t("ssh_key_hint"))}</div>
        <div class="keybox"><code>${esc(state.ssh_public_key)}</code>
          <button class="btn small flat" id="copykey">${esc(this._t("copy"))}</button></div>`;
      keyBox.querySelector("#copykey").addEventListener("click", () => this._copy(state.ssh_public_key));
    }

    const rows = this._filtered();
    const list = root.querySelector("#list");
    if (!rows.length) {
      list.innerHTML = `<div class="empty">${esc(this._t("empty"))}</div>`;
      return;
    }
    list.innerHTML = `
      <table>
        <thead><tr>
          <th>${esc(this._t("c_state"))}</th>
          <th>${esc(this._t("c_name"))}</th>
          <th>${esc(this._t("c_ip"))}</th>
          <th class="hide-narrow">${esc(this._t("c_mac"))}</th>
          <th class="hide-narrow">${esc(this._t("c_vendor"))}</th>
          <th class="hide-narrow">${esc(this._t("c_seen"))}</th>
          <th>${esc(this._t("c_actions"))}</th>
        </tr></thead>
        <tbody>${rows.map((d) => this._row(d)).join("")}</tbody>
      </table>`;
  }

  _row(d) {
    let dot = d.online ? "on" : "";
    let stateText = this._t(d.online ? "online" : "offline");
    if (d.pending !== null && d.pending !== undefined) {
      dot = "pending";
      stateText = this._t(d.pending ? "turning_on" : "turning_off");
    }
    const badges = [
      d.mapped ? `<span class="badge mapped">${esc(this._t(`b_${d.entity_mode || "control"}`))}</span>` : "",
      d.new && !d.mapped && !d.ignored ? `<span class="badge new">${esc(this._t("new"))}</span>` : "",
      d.windows ? `<span class="badge">${esc(this._t("windows"))}</span>` : "",
      d.ignored ? `<span class="badge">${esc(this._t("ignored"))}</span>` : "",
    ].join("");
    const subName = d.name && d.hostname && d.name !== d.hostname ? `<div class="sub">${esc(d.hostname)}</div>` : "";
    const lastAction = d.mapped && d.last_action
      ? `<div class="sub" title="${esc(d.last_action)}" style="color:${d.last_action_ok ? "inherit" : "var(--error-color)"}">${esc(this._formatDate(d.last_action_at))} · ${esc(d.last_action.length > 70 ? d.last_action.slice(0, 70) + "…" : d.last_action)}</div>`
      : "";
    const id = esc(d.id);
    const busy = d.pending !== null && d.pending !== undefined;
    const actions = [];
    const control = d.mapped && d.entity_mode !== "presence";
    if (d.mapped) {
      if (control) actions.push(`<button class="btn small ok" data-act="on" data-id="${id}" ${busy || d.online || !d.wol_enabled || !d.mac ? "disabled" : ""}>${esc(this._t("power_on"))}</button>`);
      if (control) actions.push(`<button class="btn small danger" data-act="off" data-id="${id}" ${busy || !d.online || d.shutdown_method === "none" ? "disabled" : ""}>${esc(this._t(`off_${d.off_action || "shutdown"}`))}</button>`);
      actions.push(`<button class="btn small flat" data-act="edit" data-id="${id}">${esc(this._t("edit"))}</button>`);
    } else {
      actions.push(`<button class="btn small" data-act="edit" data-id="${id}">${esc(this._t("map"))}</button>`);
      actions.push(`<button class="btn small flat" data-act="ignore" data-id="${id}">${esc(this._t(d.ignored ? "unignore" : "ignore"))}</button>`);
      actions.push(`<button class="btn small flat" data-act="delete" data-id="${id}">${esc(this._t("delete"))}</button>`);
    }
    return `
      <tr class="${d.ignored ? "ignored" : ""}">
        <td class="state"><span class="dot ${dot}"></span>${esc(stateText)}</td>
        <td><span class="name">${esc(d.label)}</span>${badges}${subName}${lastAction}</td>
        <td class="mono">${esc(d.ip || "—")}</td>
        <td class="mono hide-narrow">${esc(d.mac || "—")}</td>
        <td class="hide-narrow">${esc(d.vendor || (d.random_mac ? this._t("random_mac") : ""))}</td>
        <td class="hide-narrow">${esc(this._formatDate(d.last_seen))}</td>
        <td><div class="actions">${actions.join("")}</div></td>
      </tr>`;
  }

  _device(id) {
    return (this._state?.devices ?? []).find((d) => d.id === id);
  }

  _onListClick(ev) {
    const btn = ev.target.closest("button[data-act]");
    if (!btn) return;
    const d = this._device(btn.dataset.id);
    if (!d) return;
    switch (btn.dataset.act) {
      case "edit":
        this._openDialog(d);
        break;
      case "ignore":
        this._run(this._ws({ type: "devices/save", device_id: d.id, ignored: !d.ignored }));
        break;
      case "delete":
        if (confirm(this._t("confirm_delete", { name: d.label }))) {
          this._run(this._ws({ type: "devices/delete", device_id: d.id }));
        }
        break;
      case "on":
        this._run(this._ws({ type: "devices/power", device_id: d.id, on: true }));
        break;
      case "off":
        if (confirm(this._t("confirm_off", { name: d.label, action: this._t(`off_${d.off_action || "shutdown"}`) }))) {
          this._run(this._ws({ type: "devices/power", device_id: d.id, on: false }));
        }
        break;
    }
  }

  _openDialog(d) {
    const defaults = this._state?.defaults ?? {};
    const isNew = !d;
    const dev = d || { mapped: true, entity_mode: "both", wol_enabled: true, shutdown_method: "windows" };
    const method = dev.shutdown_method === "none" && !dev.mapped && dev.windows ? "windows" : dev.shutdown_method || "none";
    const title = isNew ? this._t("d_title_new") : dev.mapped ? this._t("d_title_edit") : this._t("d_title_map");
    const def = (v) => (v !== undefined && v !== null && v !== "" ? this._t("d_default", { value: v }) : "");
    const val = (v) => esc(v ?? "");
    const dialog = this.shadowRoot.querySelector("#dialog");
    dialog.innerHTML = `
      <form method="dialog">
        <div class="d-head">${esc(title)}</div>
        <div class="d-body">
          <fieldset>
            <legend>${esc(this._t("d_general"))}</legend>
            <label class="f">${esc(this._t("d_name"))}<input name="name" value="${val(dev.name)}" placeholder="${val(dev.hostname || dev.ip || "")}"></label>
            <div class="row">
              <label class="f">${esc(this._t("d_ip"))}<input name="ip" value="${val(dev.ip)}" placeholder="192.168.1.10"></label>
              <label class="f">${esc(this._t("d_mac"))}<input name="mac" value="${val(dev.mac)}" placeholder="AA:BB:CC:DD:EE:FF"></label>
            </div>
            <label class="f">${esc(this._t("d_entities"))}
              <select name="entities">
                ${["none", "presence", "control", "both"].map((m) => `<option value="${m}" ${(dev.mapped ? dev.entity_mode || "control" : "both") === m ? "selected" : ""}>${esc(this._t(`e_${m}`))}</option>`).join("")}
              </select>
            </label>
            <div class="hint">${esc(this._t("d_entities_hint"))}</div>
          </fieldset>
          <fieldset>
            <legend>${esc(this._t("d_power_on"))}</legend>
            <label class="c"><input type="checkbox" name="wol_enabled" ${dev.wol_enabled !== false ? "checked" : ""}>${esc(this._t("d_wol"))}</label>
            <label class="f">${esc(this._t("d_broadcast"))}<input name="broadcast" value="${val(dev.broadcast)}" placeholder="192.168.2.255"></label>
            <div class="hint bad" id="nomac" ${dev.mac ? "hidden" : ""}>${esc(this._t("no_mac"))}</div>
          </fieldset>
          <fieldset>
            <legend>${esc(this._t("d_power_off"))}</legend>
            <label class="f">${esc(this._t("d_method"))}
              <select name="shutdown_method">
                ${["windows", "ssh", "none"].map((m) => `<option value="${m}" ${method === m ? "selected" : ""}>${esc(this._t(`m_${m}`))}</option>`).join("")}
              </select>
            </label>
            <div data-for="windows ssh">
              <label class="f">${esc(this._t("d_off_action"))}
                <select name="off_action">
                  ${["shutdown", "hibernate", "suspend"].map((a) => `<option value="${a}" ${(dev.off_action || "shutdown") === a ? "selected" : ""}>${esc(this._t(`off_${a}`))}</option>`).join("")}
                </select>
              </label>
              <div class="hint">${esc(this._t("d_off_action_hint"))}</div>
              <div class="hint" id="off_hint" hidden></div>
            </div>
            <div data-for="windows ssh">
              <div class="row">
                <label class="f">${esc(this._t("d_username"))}<input name="username" value="${val(dev.username)}" placeholder="${val(def(defaults.username))}" autocomplete="off"></label>
                <label class="f">${esc(this._t("d_password"))}<input type="password" name="password" autocomplete="new-password" placeholder="${esc(dev.has_password ? this._t("d_password_keep") : this._t("d_password_global"))}"></label>
              </div>
              ${dev.has_password ? `<label class="c"><input type="checkbox" name="clear_password">${esc(this._t("d_clear_password"))}</label>` : ""}
            </div>
            <div data-for="windows">
              <div class="row">
                <label class="f">${esc(this._t("d_domain"))}<input name="win_domain" value="${val(dev.win_domain)}"></label>
                <label class="f">${esc(this._t("d_policy"))}
                  <select name="user_policy">
                    <option value="" ${!dev.user_policy ? "selected" : ""}>${esc(this._t("p_default"))}</option>
                    <option value="force" ${dev.user_policy === "force" ? "selected" : ""}>${esc(this._t("p_force"))}</option>
                    <option value="skip" ${dev.user_policy === "skip" ? "selected" : ""}>${esc(this._t("p_skip"))}</option>
                  </select>
                </label>
              </div>
            </div>
            <div data-for="ssh">
              <div class="row">
                <label class="f">${esc(this._t("d_ssh_os"))}
                  <select name="ssh_os">
                    ${["windows", "linux", "macos"].map((o) => `<option value="${o}" ${(dev.ssh_os || "windows") === o ? "selected" : ""}>${esc(this._t(`os_${o}`))}</option>`).join("")}
                  </select>
                </label>
                <label class="f">${esc(this._t("d_ssh_port"))}<input type="number" min="1" max="65535" name="ssh_port" value="${val(dev.ssh_port)}" placeholder="${val(defaults.ssh_port)}"></label>
              </div>
              <label class="f">${esc(this._t("d_ssh_command"))}<input name="ssh_command" value="${val(dev.ssh_command)}"></label>
            </div>
            <div data-for="windows ssh" data-os="windows" id="warnbox">
              <div class="row">
                <label class="f">${esc(this._t("d_delay"))}<input type="number" min="0" max="600" name="shutdown_delay" value="${val(dev.shutdown_delay)}" placeholder="${val(def(defaults.shutdown_delay))}"></label>
                <label class="f">${esc(this._t("d_message"))}<input name="shutdown_message" value="${val(dev.shutdown_message)}" placeholder="${val(defaults.shutdown_message)}"></label>
              </div>
            </div>
            <div data-for="ssh">
              <label class="c"><input type="checkbox" name="ssh_restricted" ${dev.ssh_restricted ? "checked" : ""}>${esc(this._t("d_ssh_restricted"))}</label>
              <div class="hint" id="restricted_hint">${esc(this._t("d_ssh_restricted_hint"))}</div>
              <div class="hint">${esc(this._t("d_identity"))}: <span id="identity">${dev.ssh_host_fingerprint ? `<span class="mono">${esc(dev.ssh_host_fingerprint)}</span>` : esc(this._t("d_identity_none"))}</span></div>
              ${dev.ssh_host_fingerprint ? `<label class="c"><input type="checkbox" name="forget_host_key">${esc(this._t("d_forget"))}</label>` : ""}
              <div class="btnrow">
                <button class="btn small flat" type="button" id="setup">${esc(this._t("d_setup"))}</button>
                <button class="btn small flat" type="button" id="test">${esc(this._t("d_test"))}</button>
              </div>
              <div id="setupbox" hidden>
                <div class="hint" id="setuphint"></div>
                <textarea class="script" readonly id="script"></textarea>
                <div class="btnrow"><button class="btn small" type="button" id="copyscript">${esc(this._t("copy"))}</button></div>
              </div>
            </div>
          </fieldset>
          ${dev.last_action ? `<div class="hint">${esc(this._t("d_last_action"))} (${esc(this._formatDate(dev.last_action_at))}): ${esc(dev.last_action)}</div>` : ""}
        </div>
        <div class="d-foot">
          <button class="btn flat" value="cancel" type="button" id="cancel">${esc(this._t("cancel"))}</button>
          <button class="btn" value="save" type="submit">${esc(this._t("save"))}</button>
        </div>
      </form>`;

    const form = dialog.querySelector("form");
    const setupBox = dialog.querySelector("#setupbox");
    const syncMethod = () => {
      const m = form.shutdown_method.value;
      const os = form.ssh_os.value;
      form.querySelectorAll("[data-for]").forEach((el) => {
        const osOk = !el.dataset.os || m !== "ssh" || el.dataset.os === os;
        el.hidden = !el.dataset.for.split(" ").includes(m) || !osOk;
      });
      dialog.querySelector("#restricted_hint").hidden = !form.ssh_restricted.checked;
      form.password.placeholder = m === "ssh" ? this._t("d_password_key")
        : dev.has_password ? this._t("d_password_keep") : this._t("d_password_global");
      form.ssh_command.placeholder = os === "windows" ? this._t("d_cmd_windows") : this._t("d_default", { value: defaults.ssh_command });
      const target = m === "windows" ? "windows" : os;
      const action = form.off_action.value;
      const offHint = dialog.querySelector("#off_hint");
      const hintKey = { "windows/hibernate": "d_off_hibernate_windows", "windows/suspend": "d_off_suspend_windows", "linux/hibernate": "d_off_hibernate_linux" }[`${target}/${action}`];
      offHint.hidden = !hintKey;
      // Warning delay and message exist only for the Windows shutdown.
      if (action !== "shutdown") dialog.querySelector("#warnbox").hidden = true;
      offHint.textContent = hintKey ? this._t(hintKey) : "";
      setupBox.hidden = true; // the script depends on these values: build it again on request
    };
    form.shutdown_method.addEventListener("change", syncMethod);
    form.ssh_os.addEventListener("change", syncMethod);
    form.ssh_restricted.addEventListener("change", syncMethod);
    form.off_action.addEventListener("change", syncMethod);
    const sshParams = () => ({
      ssh_os: form.ssh_os.value,
      ssh_restricted: form.ssh_restricted.checked,
      off_action: form.off_action.value,
      name: form.name.value,
      ssh_command: form.ssh_command.value,
      shutdown_delay: form.shutdown_delay.value,
      shutdown_message: form.shutdown_message.value,
    });
    dialog.querySelector("#setup").addEventListener("click", async () => {
      try {
        const res = await this._ws({ type: "ssh/setup", ...sshParams() });
        dialog.querySelector("#setuphint").textContent = this._t(form.ssh_os.value === "windows" ? "d_setup_windows" : "d_setup_linux");
        dialog.querySelector("#script").value = res.script;
        setupBox.hidden = false;
      } catch (err) {
        this._toast(err.message || String(err), true);
      }
    });
    dialog.querySelector("#copyscript").addEventListener("click", () => this._copy(dialog.querySelector("#script").value));
    dialog.querySelector("#test").addEventListener("click", () => {
      if (isNew) {
        this._toast(this._t("d_test_save_first"), true);
        return;
      }
      this._run(
        this._ws({ type: "ssh/test", device_id: dev.id }).then((res) => {
          // The state update (with the identity just stored) arrives before the result.
          const fp = this._device(dev.id)?.ssh_host_fingerprint;
          if (fp) dialog.querySelector("#identity").innerHTML = `<span class="mono">${esc(fp)}</span>`;
          return res;
        })
      );
    });
    form.mac.addEventListener("input", () => (dialog.querySelector("#nomac").hidden = !!form.mac.value.trim()));
    syncMethod();
    dialog.querySelector("#cancel").addEventListener("click", () => dialog.close());
    form.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const f = form.elements;
      const msg = {
        type: "devices/save",
        ...(isNew ? {} : { device_id: dev.id }),
        name: f.name.value,
        ip: f.ip.value,
        mac: f.mac.value,
        mapped: f.entities.value !== "none",
        ...(f.entities.value !== "none" ? { entity_mode: f.entities.value } : {}),
        wol_enabled: f.wol_enabled.checked,
        broadcast: f.broadcast.value,
        shutdown_method: f.shutdown_method.value,
        username: f.username.value,
        win_domain: f.win_domain.value,
        shutdown_delay: f.shutdown_delay.value,
        shutdown_message: f.shutdown_message.value,
        user_policy: f.user_policy.value,
        ssh_port: f.ssh_port.value,
        ssh_command: f.ssh_command.value,
        ssh_os: f.ssh_os.value,
        off_action: f.off_action.value,
        ssh_restricted: f.ssh_restricted.checked,
      };
      if (f.forget_host_key?.checked) msg.forget_host_key = true;
      if (f.password.value) msg.password = f.password.value;
      if (f.clear_password?.checked) msg.clear_password = true;
      try {
        await this._ws(msg);
        dialog.close();
        this._toast(this._t("saved"));
      } catch (err) {
        this._toast(err.message || String(err), true);
      }
    });
    dialog.showModal();
  }
}

customElements.define("lan-power-manager-panel", LanPowerManagerPanel);

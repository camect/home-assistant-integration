"""
Support for Camect Home.

Example configuration.yaml entry:
camect:
    - host: camect.local
      port: 443
      username: admin
      password: XXXXX
      camera_ids: aaa,bbbb
      id: (optional)  // provide this if you have multiple Camect devices so you could
                      // tell which camera is from which Camect device.
"""
import voluptuous as vol

from homeassistant.components import camera
from homeassistant.const import (
    CONF_HOST, CONF_ID, CONF_PASSWORD, CONF_PORT, CONF_USERNAME)
from homeassistant.helpers import config_validation as cv, discovery

ATTR_MODE = 'mode'
CONF_CAMERA_IDS = 'camera_ids'
DEFAULT_HOST = 'camect.local'
DEFAULT_PORT = 8443
DEFAULT_USERNAME = 'admin'
DOMAIN = 'camect'
SERVICE_CHANGE_OP_MODE = 'change_op_mode'
SERVICE_DISABLE_CAMERA_ALERT = 'disable_camera_alert'
SERVICE_ENABLE_CAMERA_ALERT = 'enable_camera_alert'
CAMERA_IDS = 'camera'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema(vol.All([{
        vol.Optional(CONF_HOST, default=DEFAULT_HOST): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional(CONF_USERNAME, default=DEFAULT_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_ID): cv.string,
        vol.Optional(CONF_CAMERA_IDS, default=[]): vol.All(
            cv.ensure_list_csv, [cv.string]),
    }], vol.Length(min=1))),
}, extra=vol.ALLOW_EXTRA)

CHANGE_OP_MODE_SCHEMA = vol.Schema({
    vol.Required(ATTR_MODE): cv.string
})

CAMERA_ALERT_SCHEMA = vol.Schema({
    vol.Required(CAMERA_IDS, default=[]): vol.All(
        cv.ensure_list_csv, [cv.string])
})

def setup(hass, config):
    """Set up the Camect component."""
    import camect

    # Create camect.Home instances.
    homes = []
    data = []
    for conf in config[DOMAIN]:
        host = conf.get(CONF_HOST)
        port = conf.get(CONF_PORT)
        home = camect.Home('{}:{}'.format(host, port),
            conf.get(CONF_USERNAME), conf.get(CONF_PASSWORD))
        home.add_event_listener(lambda evt: hass.bus.fire('camect_event', evt))
        homes.append(home)
        data.append((conf.get(CONF_CAMERA_IDS), conf.get(CONF_ID)))
    hass.data[DOMAIN] = homes
    discovery.load_platform(hass, camera.DOMAIN, DOMAIN, data, config)


    # Register services.
    def handle_change_op_mode_service(call):
        mode = call.data.get(ATTR_MODE).upper()
        if mode in ('HOME', 'DEFAULT'):
            home.set_mode(mode)
        elif mode == 'AWAY':
            home.set_mode('DEFAULT')
    hass.services.register(
        DOMAIN, SERVICE_CHANGE_OP_MODE, handle_change_op_mode_service,
        schema=CHANGE_OP_MODE_SCHEMA)

    def handle_disable_camera_alert(call):
        camera = call.data.get(CAMERA_IDS)
        home.disable_alert(camera, "HomeAssistant")
    hass.services.register(
        DOMAIN, SERVICE_DISABLE_CAMERA_ALERT, handle_disable_camera_alert,
        schema=CAMERA_ALERT_SCHEMA)

    def handle_enable_camera_alert(call):
        camera = call.data.get(CAMERA_IDS)
        home.enable_alert(camera, "HomeAssistant")
    hass.services.register(
        DOMAIN, SERVICE_ENABLE_CAMERA_ALERT, handle_enable_camera_alert,
        schema=CAMERA_ALERT_SCHEMA)
    
    return True

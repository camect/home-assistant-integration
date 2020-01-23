"""
Support for Camect Home.

Example configuration.yaml entry:
camect:
    - host: camect.local
      port: 443
      username: admin
      password: XXXXX
      camera_ids: aaa,bbbb
"""
import voluptuous as vol

from homeassistant.components import camera
from homeassistant.const import (
    CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME)
from homeassistant.helpers import config_validation as cv, discovery

ATTR_MODE = 'mode'
CONF_CAMERA_IDS = 'camera_ids'
DEFAULT_HOST = 'camect.local'
DEFAULT_PORT = 8443
DEFAULT_USERNAME = 'admin'
DOMAIN = 'camect'
SERVICE_CHANGE_OP_MODE = 'change_op_mode'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema(vol.All([{
        vol.Optional(CONF_HOST, default=DEFAULT_HOST): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional(CONF_USERNAME, default=DEFAULT_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_CAMERA_IDS, default=[]): vol.All(
            cv.ensure_list_csv, [cv.string]),
    }], vol.Length(min=1))),
}, extra=vol.ALLOW_EXTRA)

CHANGE_OP_MODE_SCHEMA = vol.Schema({
    vol.Required(ATTR_MODE): cv.string
})


def setup(hass, config):
    """Set up the Camect component."""
    import camect

    # Create camect.Home instances.
    homes = []
    cam_id_lists = []
    for conf in config[DOMAIN]:
        host = conf.get(CONF_HOST)
        port = conf.get(CONF_PORT)
        home = camect.Home('{}:{}'.format(host, port),
            conf.get(CONF_USERNAME), conf.get(CONF_PASSWORD))
        homes.append(home)
        cam_id_lists.append(conf.get(CONF_CAMERA_IDS))
    hass.data[DOMAIN] = homes
    discovery.load_platform(hass, camera.DOMAIN, DOMAIN, cam_id_lists, config)

    home.add_event_listener(lambda evt: hass.bus.fire('camect_event', evt))

    # Register service.
    def handle_change_op_mode_service(call):
        mode = call.data.get(ATTR_MODE).upper()
        if mode in ('HOME', 'DEFAULT'):
            home.set_mode(mode)
        elif mode == 'AWAY':
            home.set_mode('DEFAULT')
    hass.services.register(
        DOMAIN, SERVICE_CHANGE_OP_MODE, handle_change_op_mode_service,
        schema=CHANGE_OP_MODE_SCHEMA)

    return True

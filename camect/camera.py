"""Support for streaming any camera supported by Camect using WebRTC."""
import asyncio
import logging
from typing import Dict

import aiohttp
from aiohttp import web
import async_timeout

from homeassistant.components import camera

_LOGGER = logging.getLogger(__name__)
DOMAIN = 'camect'


def setup_platform(hass, config, add_entities, cam_ids):
    """Add an entity for every camera from Camect Home."""
    component = hass.data[camera.DOMAIN]
    hass.http.register_view(CamectWebsocketView(component))

    home = hass.data[DOMAIN]
    camect_site = home.get_cloud_url('')
    cam_jsons = home.list_cameras()
    if cam_jsons:
        cams = []
        for cj in cam_jsons:
            if not cam_ids or cj['id'] in cam_ids:
                cams.append(Camera(home, cj, camect_site))
        add_entities(cams, True)
    return True


class Camera(camera.Camera):
    """An implementation of a camera supported by Camect Home."""

    def __init__(self, home, json: Dict[str, str], camect_site: str):
        """Initialize a camera supported by Camect Home."""
        super(Camera, self).__init__()
        self._home = home
        self._device_id = json['id']
        self._id = '{}_{}'.format(DOMAIN, self._device_id)
        self.entity_id = '{}.{}'.format(camera.DOMAIN, self._id)
        self._name = json['name']
        self._make = json['make'] or ''
        self._model = json['model'] or ''
        self._url = json['url']
        self._width = int(json['width'])
        self._height = int(json['height'])
        self._camect_site = camect_site

    @property
    def name(self):
        """Return the name of this camera."""
        return self._name

    @property
    def brand(self):
        """Return the camera brand."""
        return self._make

    @property
    def model(self):
        """Return the camera model."""
        return self._model

    @property
    def is_recording(self):
        """Return true if the device is recording."""
        return True

    @property
    def is_on(self):
        """Return true if on."""
        return True

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._id

    @property
    def entity_picture(self):
        """Return a link to the camera feed as entity picture."""
        return None

    def camera_image(self):
        """Return a still image response from the camera."""
        return self._home.snapshot_camera(self._device_id)

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            'device_id': self._device_id,
            'device_url': self._url,
            'video_width': self._width,
            'video_height': self._height,
            'camect_site': self._camect_site,
            'ws_url': '/api/camect_proxy/websocket/' + self.entity_id,
        }

    @property
    def should_poll(self):
        """No need for the poll."""
        return False


class CamectWebsocketView(camera.CameraView):
    """Camect view to proxy Websocket to home."""

    url = '/api/camect_proxy/websocket/{entity_id}'
    name = 'api:camect:websocket'

    async def handle(self, request, camera):
        """Serve Camect Websocket."""
        ha_ws = web.WebSocketResponse()
        await ha_ws.prepare(request)

        hass = request.app['hass']
        home = hass.data[DOMAIN]
        ws_url = home.get_unsecure_websocket_url()
        if not ws_url:
            raise web.HTTPInternalServerError()
        session = aiohttp.ClientSession()
        camect_ws = await session.ws_connect(ws_url, ssl=False)

        async def forward(src, dst):
            async for msg in src:
                if msg.type == aiohttp.WSMsgType.BINARY:
                    await dst.send_bytes(msg.data)
                else:
                    _LOGGER.warning(
                        "Received invalid message type: %s", msg.type)
        await asyncio.gather(
            forward(ha_ws, camect_ws), forward(camect_ws, ha_ws))

        ha_ws.close()
        camect_ws.close()
